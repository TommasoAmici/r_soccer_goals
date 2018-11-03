from telegram.ext import Updater
import telegram
import praw
from requests import get
import uuid
import youtube_dl
from settings import telegram_settings, reddit_settings


def get_url(post):
    with youtube_dl.YoutubeDL({}) as ydl:
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
        "Frosinone",
        "Atalanta",
        "Chievo",
        "Genoa",
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
        "streamvi",
        "twitter",
    )
    if any(s in post.url for s in streams):
        if is_goal(post):
            return True
    return False


def send_video(bot, post, url):
    try:
        bot.send_video(
            chat_id=telegram_settings["chat_id"],
            video=url,
            caption=post.title,
            disable_notification=True,
            file_id=uuid.uuid4(),
        )
    except:
        return


def process_submission(post):
    """
    For each post 
    - determines if it's a goal
    - extracts direct url
    - sends to telegram channel
    """
    bot = telegram.Bot(token=telegram_settings["bot_token"])
    if is_video(post):
        url = get_url(post)
        if url is None:
            return
        else:
            send_video(bot, post, url)


def main():
    try:
        reddit = praw.Reddit(
            client_id=reddit_settings["client_id"],
            client_secret=reddit_settings["client_secret"],
            user_agent=reddit_settings["user_agent"],
            username=reddit_settings["username"],
            password=reddit_settings["password"],
        )
    except:
        main()
    subreddit = reddit.subreddit(reddit_settings["subreddit"])
    for submission in subreddit.stream.submissions():
        process_submission(submission)
        submission.hide()


if __name__ == "__main__":
    main()
