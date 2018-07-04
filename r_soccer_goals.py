from telegram.ext import Updater
import telegram
import praw
from requests import get
import json
from pystreamable import StreamableApi
from bs4 import BeautifulSoup
import uuid
from settings import telegram_settings, reddit_settings, streamable_settings


def make_soup(url):
    page = get(url)
    if page.status_code != 200:
        return None
    else:
        return BeautifulSoup(page.text, "html.parser")


def get_streamable_direct(url):
    streamable_settings = streamable_settings()
    video_id = url.replace("https://streamable.com/", "")
    api = StreamableApi(streamable_settings.email, streamable_settings.password)
    try:
        u = "https:{}".format(api.get_info(video_id)["files"]["mp4"]["url"])
    except:
        u = url
    return u


def get_streamja_direct(url):
    soup = make_soup(url)
    return soup.source.get("src")


def get_clippuser_direct(url):
    soup = make_soup(url)
    return soup.find("div", attrs={"id": "player-container"}).get("data-hd-file")


def get_flixtc_direct(url):
    soup = make_soup(url)
    return soup.find("meta", attrs={"property": "og:video:secure_url"})["content"]


def get_streamgoals_direct(url):
    return url.replace("video", "cache") + ".mp4"


def is_goal(post):
    teams = (
        "Milan",
        "Inter ",
        "Inter-",
        "Inter)",
        "Inter]",
        "Inter.",
        "Inter,",
        "Internazionale",
        "Napoli",
        "Juve",
        "Roma,",
        "Roma)",
        "Roma]",
        "Roma.",
        "Roma-",
        "Roma ",
        "Lazio",
        "Spal",
        "Udinese",
        "Sampdoria",
        "Sassuolo",
        "Empoli",
        "Cagliari",
        "Parma",
        "Verona",
        "Frosinone",
        "Atalanta",
        "Chievo",
        "Torino",
        "Fiorentina",
        "Bologna",
    )
    to_drop = ("Internacional", "Romario", "Romania")
    if any(drop in post.title for drop in to_drop):
        return False
    elif any(team in post.title for team in teams):
        return True
    else:
        return False


def is_video(post):
    streams = (
        "streamja",
        "streamable",
        "clippituser",
        "mixtape",
        "flixtc",
        "streamgoals",
        "v.redd",
        "a.pomfe.co",
        "kyouko.se",
    )
    if any(s in post.url for s in streams):
        if is_goal(post):
            return True
    return False


def process_submission(post):
    """
    For each post 
    - determines if it's a goal
    - extracts direct url
    - sends to telegram channel
    """
    telegram_settings = telegram_settings()
    bot = telegram.Bot(token=telegram_settings.bot_token)
    updater = Updater(telegram_settings.bot_token)
    if is_video(post):
        if "streamable" in post.url:
            url = get_streamable_direct(post.url)
        elif "streamja" in post.url:
            url = get_streamja_direct(post.url)
        elif "clippituser" in post.url:
            url = get_clippuser_direct(post.url)
        elif "flixtc" in post.url:
            url = get_flixtc_direct(post.url)
        elif "streamgoals" in post.url:
            url = get_streamgoals_direct(post.url)
        else:
            url = post.url
        try:
            bot.send_video(
                chat_id=telegram_settings.chat_id,
                video=url,
                caption=post.title,
                disable_notification=True,
                file_id=uuid.uuid4(),
            )
        except:
            return


def main():
    reddit_settings = reddit_settings()
    try:
        reddit = praw.Reddit(
            client_id=reddit_settings.client_id,
            client_secret=reddit_settings.client_secret,
            user_agent=reddit_settings.user_agent,
            username=reddit_settings.username,
            password=reddit_settings.password,
        )
    except:
        main()
    subreddit = reddit.subreddit(reddit_settings.subreddit)
    for submission in subreddit.stream.submissions():
        process_submission(submission)


if __name__ == "__main__":
    main()
