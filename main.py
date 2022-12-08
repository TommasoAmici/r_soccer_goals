import asyncio
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime

import aiohttp
import uvloop
from aiogram import Bot
from aiogram.utils.exceptions import WrongFileIdentifier
from redis import StrictRedis
from yt_dlp import YoutubeDL

from teams import blacklist_regex, teams_regex

cache = StrictRedis(
    os.environ.get("REDIS_HOST", "localhost"),
    int(os.environ.get("REDIS_PORT", "6379")),
    charset="utf-8",
    decode_responses=True,
)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

LIMIT = 10
CACHE_PREFIX = "r_soccer_goals"
SUBMISSIONS_KEY = f"{CACHE_PREFIX}:submissions"
QUEUE_KEY = f"{CACHE_PREFIX}:queue"
PROCESSED_KEY = f"{CACHE_PREFIX}:processed"


def clean_zset(before=60 * 60 * 24 * 3):
    """
    Removes elements added more than three days ago to the ZSET of processed submissions
    """
    now = time.monotonic()
    cache.zremrangebyscore(PROCESSED_KEY, 0, now - before)


@dataclass
class Submission:
    id: str
    url: str
    title: str
    flair: str | None

    @classmethod
    def get(cls, id):
        submission = cache.hgetall(f"{SUBMISSIONS_KEY}:{id}")
        return Submission(id, submission["url"], submission["title"], None)

    @property
    def key(self):
        return f"{SUBMISSIONS_KEY}:{self.id}"

    def add_to_queue(self):
        """
        Stores submission data in Redis for later retrieval and adds submission to
        the queue for processing. The cached data expires after 24 hours.
        """
        cache.hset(
            self.key,
            mapping={
                "id": self.id,
                "url": self.url,
                "title": self.title,
            },
        )
        cache.expire(self.key, 86400)
        cache.lpush(QUEUE_KEY, self.id)

    def add_to_processed(self):
        cache.zadd(PROCESSED_KEY, {self.id: time.monotonic()})

    def already_processed(self) -> bool:
        return cache.zscore(PROCESSED_KEY, self.id) is not None

    def is_video(self) -> bool:
        if self.flair == "media":
            return True

        streams = (
            "stream",
            "clip",
            "mixtape",
            "flixtc",
            "v.redd",
            "a.pomfe.co",
            "kyouko.se",
            "twitter",
            "sporttube",
            "dubz.co",
        )
        if any(s in self.url for s in streams):
            return True
        return False

    def matches_wanted_teams(self) -> bool:
        """Returns True if the submission's title matches the teams list"""
        is_wanted_team = teams_regex.search(self.title) is not None
        is_blacklisted = blacklist_regex.search(self.title)
        return is_wanted_team and not is_blacklisted


class Schedule:
    """
    Schedule is a class with helpers to determine the frequency with which
    we should query reddit for new content
    """

    def __init__(self):
        self.now = datetime.utcnow()

    @property
    def is_saturday(self):
        return self.now.day == 5

    @property
    def is_sunday(self):
        return self.now.day == 6

    @property
    def is_afternoon(self):
        return self.now.hour > 11 and self.now.hour < 17

    @property
    def is_evening(self):
        return self.now.hour > 17 and self.now.hour < 23

    @property
    def is_night(self):
        return self.now.hour > 1 and self.now.hour < 12

    @property
    def refresh_frequency(self) -> int:
        # during the night there is no Serie A
        if self.is_night:
            return 60 * 5
        if self.is_evening:
            return 60
        if (self.is_saturday or self.is_sunday) and (
            self.is_afternoon or self.is_evening
        ):
            return 60
        return 60 * 2


async def get_url(video_url: str) -> str | None:
    result = {}
    with YoutubeDL(
        {"quiet": True, "no_check_certificate": True, "logger": logger}
    ) as ydl:
        # mostly to handle tweets
        try:
            result = ydl.extract_info(video_url, download=False)
        except:
            logger.error("Failed to extract video URL")
            return None
    if result is None:
        return None
    if "entries" in result:
        # Can be a playlist or a list of videos
        video = result["entries"][0]
    else:
        video = result
    if video.get("url") is None:
        return None

    async with aiohttp.ClientSession() as session:
        async with session.head(video["url"], allow_redirects=True) as response:
            if response.status != 200:
                return None
            return str(response.url)


async def send(bot: Bot, submission: Submission):
    """
    For each item in queue, extracts direct url and sends it to telegram channel
    """

    url = await get_url(submission.url)

    if url is not None:
        logger.debug(f"{submission.id}: sending video {url}")
        try:
            await bot.send_video(
                chat_id=os.environ["TELEGRAM_CHAT_ID"],
                video=url,
                caption=submission.title,
            )
            return
        except WrongFileIdentifier:
            logger.error(
                f"{submission.id}: failed to send video to channel, url: {url}"
            )
            pass
    # if it fails to send video, send a link
    # don't send tweets as links
    if "twitter" not in submission.url:
        try:
            await bot.send_video(
                chat_id=os.environ["TELEGRAM_CHAT_ID"],
                video=submission.url,
                caption=submission.title,
            )
        except WrongFileIdentifier:
            logger.info(f"{submission.id}: sending as message")
            await bot.send_message(
                chat_id=os.environ["TELEGRAM_CHAT_ID"],
                text=f"{submission.title}\n\n{submission.url}",
            )


async def worker(bot: Bot):
    while True:
        submission_id = cache.rpop(QUEUE_KEY)
        if submission_id is None:
            return
        submission = Submission.get(submission_id)
        logger.info(f"{submission.id}: processing from queue")
        await send(bot, submission)


async def fetch_submissions(subreddit: str):
    """
    Fetches the latest posts from the given subreddit and processes each submission,
    adding all videos that match the required filters to the download queue
    """
    logger.info("fetching submissions")

    async with aiohttp.ClientSession() as session:
        url = f"https://reddit.com/r/{subreddit}/new.json?limit={LIMIT}"

        async with session.get(url) as response:
            res_json = await response.json()
            if res_json.get("data") is None:
                logger.error("failed to load data from subreddit")
                return

            for _child in res_json["data"].get("children", []):
                child = _child["data"]

                submission = Submission(
                    child["id"],
                    child["url"],
                    child["title"],
                    child["link_flair_css_class"],
                )

                if submission.already_processed():
                    logger.debug(
                        f"{submission.id}: skipping already processed submission"
                    )
                    continue

                logger.debug(f"{submission.id}: processing")

                if submission.is_video() and submission.matches_wanted_teams():
                    logger.debug(f"{submission.id}: adding to queue")
                    submission.add_to_queue()

                submission.add_to_processed()


async def main():
    """
    Every 10 seconds re-fetch submissions
    """
    subreddit = os.environ.get("REDDIT_SUBREDDIT", "soccer")
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])

    while True:
        await fetch_submissions(subreddit)
        # here we wait 20 seconds because sometimes the clips uploaded take some time to
        # be processed by the host, which means we cannot download them.
        await asyncio.sleep(20)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker(bot))
            tg.create_task(worker(bot))

        # wait 20 seconds to avoid flooding reddit with too many requests
        clean_zset()
        await asyncio.sleep(Schedule().refresh_frequency)


if __name__ == "__main__":
    logger.info("Started r_soccer_goals bot")
    asyncio.run(main())
