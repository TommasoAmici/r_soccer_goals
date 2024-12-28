import asyncio
import logging
import os
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus

import aiohttp
import asyncpraw
import uvloop
from aiogram import Bot
from aiogram.utils.exceptions import InvalidHTTPUrlContent, WrongFileIdentifier
from yt_dlp import YoutubeDL

from teams import blacklist_regex, teams_regex


class Queue:
    def __init__(self, db: sqlite3.Connection):
        self.conn = db
        self.cursor = self.conn.cursor()
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS queue (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                title TEXT NOT NULL,
                processed TIMESTAMP
            )
            """
        )

    def add(self, submission_id: str, url: str, title: str, *, processed=False):
        if processed:
            self.cursor.execute(
                """
                INSERT INTO queue (id, url, title, processed)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (submission_id, url, title),
            )
        else:
            self.cursor.execute(
                "INSERT INTO queue (id, url, title) VALUES (?, ?, ?)",
                (submission_id, url, title),
            )
        self.conn.commit()

    def pop(self):
        row = self.cursor.execute(
            "SELECT id, url, title FROM queue WHERE processed IS NULL"
        ).fetchone()
        if not row:
            return None
        self.cursor.execute(
            "UPDATE queue SET processed = CURRENT_TIMESTAMP WHERE id = ?", (row[0],)
        )
        self.conn.commit()
        return {
            "id": row[0],
            "url": row[1],
            "title": row[2],
        }

    def already_processed(self, submission_id: str) -> bool:
        self.cursor.execute(
            "SELECT 1 FROM queue WHERE id = ? AND processed IS NOT NULL",
            (submission_id,),
        )
        return self.cursor.fetchone() is not None

    def clear(self):
        self.cursor.execute(
            """
            DELETE FROM queue
            WHERE processed IS NOT NULL AND processed < DATETIME('now', '-3 day')
            """
        )
        self.conn.commit()

    def close(self):
        self.conn.close()


db = sqlite3.connect(os.getenv("DB_PATH", "r_soccer_goals.db"))
cache = Queue(db)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)

LIMIT = 10


@dataclass
class Submission:
    id: str
    url: str
    title: str
    flair: str | None

    @classmethod
    def pop(cls):
        submission = cache.pop()
        if submission is None:
            return None
        return Submission(
            submission["id"],
            submission["url"],
            submission["title"],
            None,
        )

    def add_to_queue(self, *, processed=False):
        cache.add(self.id, self.url, self.title, processed=processed)

    def already_processed(self) -> bool:
        return cache.already_processed(self.id)

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
            "caulse.com",
        )
        return bool(any(s in self.url for s in streams))

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
        self.now = datetime.now(tz=UTC)

    @property
    def is_saturday(self):
        return self.now.weekday() == 5

    @property
    def is_sunday(self):
        return self.now.weekday() == 6

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
        {"quiet": True, "no_check_certificate": True, "logger": logger},
    ) as ydl:
        # mostly to handle tweets
        try:
            result = ydl.extract_info(video_url, download=False)
        except:  # noqa: E722
            logger.exception("Failed to extract video URL")
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

    async with aiohttp.ClientSession() as session, session.head(
        video["url"],
        allow_redirects=True,
    ) as response:
        if response.status != HTTPStatus.OK:
            return None
        return str(response.url)


def is_image(url: str) -> bool:
    """Returns True if the URL points to a static image"""
    return any(
        url.endswith(ext)
        for ext in (
            ".jpg",
            ".png",
            ".jpeg",
        )
    )


async def send(bot: Bot, submission: Submission):
    """
    For each item in queue, extracts direct url and sends it to telegram channel
    """

    url = await get_url(submission.url)
    if url is None:
        return

    kwargs = {
        "chat_id": os.environ["TELEGRAM_CHAT_ID"],
        "caption": submission.title,
    }

    logger.debug("%s: sending %s", submission.id, url)
    if is_image(url):
        try:
            await bot.send_photo(photo=url, **kwargs)
        except (WrongFileIdentifier, InvalidHTTPUrlContent):
            logger.exception(
                "%s: failed to send photo to channel, url: %s", submission.id, url
            )
    else:
        try:
            await bot.send_video(video=url, **kwargs)
        except (WrongFileIdentifier, InvalidHTTPUrlContent):
            logger.exception(
                "%s: failed to send video to channel, url: %s",
                submission.id,
                url,
            )
            # if it fails to send video, send a message including the link
            # don't send tweets as links as they're more often than not just text
            if "twitter" not in submission.url:
                logger.debug("%s: sending as message", submission.id)
                await bot.send_message(
                    chat_id=kwargs["chat_id"],
                    text=f"{submission.title}\n\n{submission.url}",
                )


async def worker(bot: Bot):
    while True:
        submission = Submission.pop()
        if submission is None:
            return
        logger.info("%s: processing from queue", submission.id)
        await send(bot, submission)


async def fetch_submissions(subreddit: str):
    """
    Fetches the latest posts from the given subreddit using asyncpraw and processes
    each submission, adding all videos that match the required filters to the
    download queue
    """
    logger.info("fetching submissions")
    reddit = asyncpraw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent="r_soccer_goals_bot",
    )

    subreddit_instance = await reddit.subreddit(subreddit)
    async for submission in subreddit_instance.new(limit=LIMIT):
        logger.debug(
            "fetching submission id=%s url=%s title='%s'",
            submission.id,
            submission.url,
            submission.title,
        )
        submission_data = Submission(
            submission.id,
            submission.url,
            submission.title,
            submission.link_flair_css_class,
        )

        if submission_data.already_processed():
            logger.debug(
                "%s: skipping already processed submission",
                submission_data.id,
            )
            continue

        logger.debug("%s: processing", submission_data.id)

        if submission_data.is_video() and teams_regex.search(submission_data.title):
            logger.info("%s: adding to queue", submission_data.id)
            submission_data.add_to_queue()
        else:
            submission_data.add_to_queue(processed=True)


async def main():
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

        # avoid flooding reddit with too many requests
        cache.clear()
        await asyncio.sleep(Schedule().refresh_frequency)


if __name__ == "__main__":
    logger.info("Started r_soccer_goals bot")
    asyncio.run(main())
