import logging
import os
import re
import time
from typing import Optional

import praw
import telegram
import youtube_dl
from praw.models import Submission

from teams import teams_regex

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_url(submission: Submission) -> Optional[str]:
    with youtube_dl.YoutubeDL({"quiet": True, "no_check_certificate": True}) as ydl:
        # mostly to handle tweets
        try:
            result = ydl.extract_info(submission.url, download=False)
        except:
            return None
    if "entries" in result:
        # Can be a playlist or a list of videos
        video = result["entries"][0]
    else:
        video = result
    return video["url"]


blacklist = re.compile(r"(Youth|Primavera|U\d+|Inter Miami)\b")


def is_goal(submission: Submission) -> bool:
    # add space to detect word boundary (\b) in regex
    title = submission.title + " "
    return any(
        team.search(title) and not blacklist.search(title) for team in teams_regex
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
        if is_goal(submission):
            return True
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


def process_submission(submission: Submission) -> None:
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
        url = get_url(submission)
        if url is None:
            return
        else:
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
