import logging
import os
import re
import time
import uuid

import praw
import telegram
import youtube_dl
from telegram.ext import Updater

from teams import teams_regex


def get_url(post):
    with youtube_dl.YoutubeDL({"quiet": True, "no_check_certificate": True}) as ydl:
        # mostly to handle tweets
        try:
            result = ydl.extract_info(post.url, download=False)
        except:
            return None
    if "entries" in result:
        # Can be a playlist or a list of videos
        video = result["entries"][0]
    else:
        video = result
    return video["url"]


blacklist = re.compile(r"(Youth|Primavera|U\d+|Inter Miami)\b")


def is_goal(post):
    # add space to detect word boundary (\b) in regex
    title = post.title + " "
    return any(
        team.search(title) and not blacklist.search(title) for team in teams_regex
    )


def is_video(post):
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
    if any(s in post.url for s in streams):
        if is_goal(post):
            return True
    return False


def send_video(bot, post, url):
    try:
        bot.send_video(
            chat_id=os.environ["TELEGRAM_CHAT_ID"],
            video=url,
            caption=post.title,
            disable_notification=True,
            file_id=uuid.uuid4(),
        )
    except Exception as e:
        logging.error(e)
        return


def process_submission(post):
    """
    For each post
    - determines if it's a goal
    - extracts direct url
    - sends to telegram channel
    """
    try:
        bot = telegram.Bot(token=os.environ["TELEGRAM_BOT_TOKEN"])
    except Exception as e:
        logging.error(e)
        raise e
    if is_video(post):
        url = get_url(post)
        if url is None:
            return
        else:
            send_video(bot, post, url)


def main():
    logging.info("Started r_soccer_goals bot")
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
            logging.info(f"Processing post {submission.id}")
            process_submission(submission)
    except Exception as e:
        logging.error(e)
        time.sleep(3)
        main()


if __name__ == "__main__":
    main()
