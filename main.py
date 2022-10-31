import asyncio
import logging
import os
from dataclasses import dataclass

import aiohttp
import uvloop
import yt_dlp
from aiogram import Bot

from teams import blacklist_regex, teams_regex

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

LIMIT = 10


@dataclass
class Submission:
    id: str
    url: str
    title: str


def get_url(video_url: str) -> str | None:
    result = {}
    with yt_dlp.YoutubeDL({"quiet": True, "no_check_certificate": True}) as ydl:
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
    return video.get("url")


def matches_wanted_teams(submission: Submission) -> bool:
    """Returns True if the submission's title matches the teams list"""
    is_wanted_team = teams_regex.search(submission.title) is not None
    is_blacklisted = blacklist_regex.search(submission.title)
    return is_wanted_team and not is_blacklisted


def is_video(submission: Submission) -> bool:
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
    if any(s in submission.url for s in streams):
        return True
    return False


async def send(bot: Bot, submission: Submission):
    """
    For each item in queue, extracts direct url and sends it to telegram channel
    """

    url = get_url(submission.url)

    if url is not None:
        logger.debug(f"{submission.id}: sending video {url}")
        try:
            await bot.send_video(
                chat_id=os.environ["TELEGRAM_CHAT_ID"],
                video=url,
                caption=submission.title,
                disable_notification=True,
            )
            return
        except:
            logger.exception("Failed to send video URL to channel")
            pass
    # if it fails to send video, send a link
    # don't send tweets as links
    if "twitter" not in submission.url:
        logger.info("sending as message", submission.title, submission.url)
        await bot.send_message(
            chat_id=os.environ["TELEGRAM_CHAT_ID"],
            text=f"{submission.title}\n\n{submission.url}",
            disable_notification=True,
        )


async def worker(queue: asyncio.Queue, bot: Bot):
    while not queue.empty():
        submission: Submission = await queue.get()
        logger.info(f"{submission.id}: processing from queue")
        await send(bot, submission)
        queue.task_done()


async def fetch_submissions(
    subreddit: str, queue: asyncio.Queue, already_processed: list[str]
):
    """
    Fetches the latest posts from the given subreddit and processes
    each submission, adding all videos that match the required filters to the download queue
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

                submission = Submission(child["id"], child["url"], child["title"])

                if submission.id in already_processed:
                    logger.debug(
                        f"{submission.id}: skipping already processed submission"
                    )
                    continue

                logger.debug(f"{submission.id}: processing")

                if is_video(submission) and matches_wanted_teams(submission):
                    logger.debug(f"{submission.id}: adding to queue")
                    await queue.put(submission)

                already_processed.append(submission.id)


async def main():
    """
    Every 10 seconds re-fetch submissions
    """
    subreddit = os.environ.get("REDDIT_SUBREDDIT", "soccer")
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])

    queue = asyncio.Queue()
    already_processed: list[str] = []

    while True:
        await fetch_submissions(subreddit, queue, already_processed)

        # since we limit each request to LIMIT submissions we can keep the list of already
        # processed items to a length of LIMIT
        already_processed = already_processed[-LIMIT:]

        # here we wait 20 seconds because sometimes the clips uploaded take some time to
        # be processed by the host, which means we cannot download them.
        await asyncio.sleep(20)

        async with asyncio.TaskGroup() as tg:
            tg.create_task(worker(queue, bot))
            tg.create_task(worker(queue, bot))

        # wait 20 seconds to avoid flooding reddit with too many requests
        await asyncio.sleep(20)


if __name__ == "__main__":
    logger.info("Started r_soccer_goals bot")
    asyncio.run(main())
