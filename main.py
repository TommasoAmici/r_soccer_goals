import asyncio
import logging
import os
from typing import Optional

import asyncpraw
import yt_dlp
from aiogram import Bot
from asyncpraw.models import Submission

from teams import blacklist_regex, teams_regex

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_url(submission: Submission) -> Optional[str]:
    result = {}
    with yt_dlp.YoutubeDL({"quiet": True, "no_check_certificate": True}) as ydl:
        # mostly to handle tweets
        try:
            result = ydl.extract_info(submission.url, download=False)
        except Exception as e:
            logger.error(e)
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


async def send_video(bot: Bot, submission: Submission, url: str) -> None:
    logger.info("sending video", submission.title, url)
    bot.send_video(
        chat_id=os.environ["TELEGRAM_CHAT_ID"],
        video=url,
        caption=submission.title,
        disable_notification=True,
    )


async def process_submission(bot: Bot, submission: Submission) -> None:
    """
    For each submission
    - determines if it's a goal
    - extracts direct url
    - sends to telegram channel
    """
    if is_video(submission):
        url = get_url(submission)
        if url is not None:
            try:
                await send_video(bot, submission, url)
            except Exception as e:
                logger.error(e)
                # if it fails to send video, send a link
                # don't send tweets as links
                if "twitter" not in submission.url:
                    logger.info("sending as message", submission.title, submission.url)
                    bot.send_message(
                        chat_id=os.environ["TELEGRAM_CHAT_ID"],
                        text=f"{submission.title}\n\n{submission.url}",
                        disable_notification=True,
                    )


async def main() -> None:
    logger.info("Started r_soccer_goals bot")
    try:
        bot = Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
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
            logger.info(f"Processing post {submission.id}")
            await process_submission(bot, submission)
    except Exception as e:
        logger.error(e)
        await asyncio.sleep(3)
        asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())
