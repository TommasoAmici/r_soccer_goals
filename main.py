import logging
import os
import re
import threading
import time
from typing import Optional

import praw
import telegram
import youtube_dl
from praw.models import Submission
from youtube_dl.utils import DownloadError

from teams import teams_regex

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_url(submission: Submission, retries: int) -> Optional[str]:
    result = {}
    with youtube_dl.YoutubeDL({"quiet": True, "no_check_certificate": True}) as ydl:
        # mostly to handle tweets
        try:
            result = ydl.extract_info(submission.url, download=False)
        except DownloadError:
            # When it fails downloading it may be the case that video
            # wasn't ready yet, let's try again in a minute (#5)
            timer = threading.Timer(60.0, process_submission, [submission, retries - 1])
            timer.start()
            return None
        except Exception as e:
            logger.error(e)
            return None
    if "entries" in result:
        # Can be a playlist or a list of videos
        video = result["entries"][0]
    else:
        video = result
    return video["url"]


blacklist = re.compile(r"(Youth|Primavera|U\d+|Inter Miami)\b")


def is_goal(submission: Submission) -> bool:
    return teams_regex.search(submission.title) and not blacklist.search(
        submission.title
    )


def is_video(submission: Submission) -> bool:
    streams = (
        "streamja",
        "streamye",
        "streamable",
        "clippituser",
        "mixtape",
        "flixtc",
        "streamgoals",
        "v.redd",
        "a.pomfe.co",
        "kyouko.se",
        "streamvi",
        "twitter",
        "sporttube",
        "stream",
        "streamwo",
    )
    if any(s in submission.url for s in streams):
        return is_goal(submission)
    return False


def send_video(bot: telegram.Bot, submission: Submission, url: str) -> None:
    try:
        bot.send_video(
            chat_id=os.environ["TELEGRAM_CHAT_ID"],
            video=url,
            caption=submission.title,
            disable_notification=True,
        )
    except Exception as e:
        logger.error(e)
        return


def process_submission(submission: Submission, retries=3) -> None:
    """
    For each submission
    - determines if it's a goal
    - extracts direct url
    - sends to telegram channel
    """
    try:
        bot = telegram.Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    except Exception as e:
        logger.error(e)
        raise e
    if is_video(submission):
        url = get_url(submission, retries)
        if url is not None:
            send_video(bot, submission, url)


def main() -> None:
    logger.info("Started r_soccer_goals bot")
    try:
        reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ["REDDIT_USER_AGENT"],
            password=os.environ["REDDIT_PASSWORD"],
            username=os.environ["REDDIT_USERNAME"],
        )
        reddit.read_only = True
        subreddit = reddit.subreddit(os.environ["REDDIT_SUBREDDIT"])
        for submission in subreddit.stream.submissions(skip_existing=True):
            logger.info(f"Processing post {submission.id}")
            process_submission(submission)
    except Exception as e:
        logger.error(e)
        time.sleep(3)
        main()


if __name__ == "__main__":
    main()
