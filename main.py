import asyncio
import logging
import os
from typing import Optional

import asyncpraw
import uvloop
import yt_dlp
from aiogram import Bot
from asyncpraw.models import Submission

from teams import blacklist_regex, teams_regex

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


def get_url(video_url: str) -> Optional[str]:
    result = {}
    with yt_dlp.YoutubeDL({"quiet": True, "no_check_certificate": True}) as ydl:
        # mostly to handle tweets
        try:
            result = ydl.extract_info(video_url, download=False)
        except:
            logger.error("Failed to extract video URL")
            return None
    if "entries" in result:
        # Can be a playlist or a list of videos
        video = result["entries"][0]
    else:
        video = result
    return video["url"]


def is_goal(submission: Submission) -> bool:
    return teams_regex.search(submission.title) and not blacklist_regex.search(
        submission.title
    )


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
    )
    if any(s in submission.url for s in streams):
        return is_goal(submission)
    return False


async def send(bot: Bot, submission: Submission):
    """
    For each item in queue, extracts direct url and sends it to telegram channel
    """
    try:
        url = get_url(submission.url)
    except KeyError:
        return
    if url is not None:
        logger.debug(f"sending video {url}")
        try:
            await bot.send_video(
                chat_id=os.environ["TELEGRAM_CHAT_ID"],
                video=url,
                caption=submission.title,
                disable_notification=True,
            )
        except:
            logger.exception("Failed to send video URL to channel")
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
    while True:
        submission: Submission = await queue.get()
        logger.debug(f"processing from queue: {submission.id}")
        await asyncio.sleep(30)
        await send(bot, submission)
        queue.task_done()


async def main() -> None:
    bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])

    queue = asyncio.Queue()
    # Create three worker tasks to process the queue concurrently.
    tasks = []
    for i in range(3):
        task = asyncio.create_task(worker(queue, bot))
        tasks.append(task)

    reddit = asyncpraw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
        password=os.environ["REDDIT_PASSWORD"],
        username=os.environ["REDDIT_USERNAME"],
    )
    reddit.read_only = True
    subreddit = await reddit.subreddit(os.environ["REDDIT_SUBREDDIT"])
    async for submission in subreddit.stream.submissions(skip_existing=True):
        logger.debug(f"Processing post {submission.id}")
        if is_video(submission):
            await queue.put(submission)


if __name__ == "__main__":
    logger.info("Started r_soccer_goals bot")
    asyncio.run(main())
