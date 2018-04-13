from telegram.ext import Updater
import telegram
import praw
import sched, time
import logging
from requests import get
import json
from pystreamable import StreamableApi
from bs4 import BeautifulSoup


def get_streamable_direct(url):
    u = url
    video_id = url.replace("https://streamable.com/", "")
    api = StreamableApi("", "")
    try:
        return "https:{}".format(api.get_info(video_id)["files"]["mp4"]["url"])

    except:
        return u


def get_streamja_direct(url):
    video_id = url.replace("https://streamja.com/", "")
    return "https://cdnja.b-cdn.net/mp4/{}/{}.mp4".format(
        video_id[:2].lower(), video_id
    )


def get_clippuser_direct(url):
    video_id = url.replace("https://www.clippituser.tv/c/", "")
    return "https://clips.clippit.tv/{}/720.mp4".format(video_id)


def make_soup(url):
    page = get(url)
    if page.status_code != 200:
        return None
    return BeautifulSoup(page.text, "html.parser")


def get_flixtc_direct(url):
    soup = make_soup(url)
    return soup.find('meta', attrs={'property': 'og:video:secure_url'})['content']


def is_goal(post):
    teams = [
        "Milan",
        "Inter",
        "Napoli",
        "Juve",
        "Roma",
        "Lazio",
        "Spal",
        "Udinese",
        "Sampdoria",
        "Sassuolo",
        "Benevento",
        "Cagliari",
        "Crotone",
        "Verona",
        "Hellas",
        "Atalanta",
        "Chievo",
        "Torino",
        "Fiorentina",
        "Bologna",
    ]
    to_drop = ["internacional", "match", "Romario"]
    if any(drop in post.title.lower() for drop in to_drop):
        return False

    elif any(team in post.title for team in teams):
        return True

    else:
        return False


def aa_mirror(post):
    mirrors = []
    for c in post.comments:
        if (
            "mirror" in c.body.lower()
            or "replay" in c.body.lower()
            and len(c.body) > 30
        ) and "aa" in c.body.lower():
            mirrors.append(c)
        else:
            continue

    return mirrors


def check_soccer_new(reddit):
    to_channel = []
    streams = [
        "streamable",
        "flixtc",
        "mixtape",
        "v.redd",
        "clippituser",
        "streamja",
        "a.pomfe.co",
    ]
    posts = [
        p
        for p in reddit.subreddit("soccer").new(limit=10)
        if any(s in p.url for s in streams)
    ]
    for post in posts:
        if is_goal(post):
            to_channel.append(post)
            try:
                to_channel.append(aa_mirror(post))
            except:
                pass
            post.hide()
            break

        else:
            continue

    return to_channel


def check_goals_sched():
    bot_token = ""
    bot = telegram.Bot(token=bot_token)
    updater = Updater(bot_token)
    try:
        reddit = praw.Reddit(
            client_id="",
            client_secret="",
            user_agent="",
            username="",
            password="",
        )
    except:
        s.enter(5, 1, check_goals_sched)
    try:
        to_channel = check_soccer_new(reddit)
    except:
        s.enter(5, 1, check_goals_sched)
    for post in to_channel:
        if isinstance(post, praw.models.reddit.submission.Submission):
            if "streamable" in post.url:
                url = get_streamable_direct(post.url)
            elif "streamja" in post.url:
                url = get_streamja_direct(post.url)
            elif "clippituser" in post.url:
                url = get_clippuser_direct(post.url)
            elif "flixtc" in post.url:
                try:
                    url = get_flixtc_direct(post.url)
                except:
                    pass
            else:
                url = post.url
            try:
                bot.send_document(
                    chat_id="@golledisoccer",
                    document=url,
                    caption=post.title,
                    disable_notification=True,
                )
            except:
                bot.send_message(
                    chat_id="@golledisoccer",
                    text="{}\n{}".format(post.title, post.url),
                    parse_mode="markdown",
                    disable_notification=True,
                )
        elif isinstance(post, list):
            for comment in post:
                bot.send_message(
                    chat_id="@golledisoccer",
                    text="**AA/Mirror**\n{}".format(comment.body),
                    parse_mode="markdown",
                    disable_notification=True,
                )
    s.enter(5, 1, check_goals_sched)


if __name__ == "__main__":
    logging.info("Starting /r/soccer_golle_bot")
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    s = sched.scheduler(time.time, time.sleep)
    s.enter(5, 1, check_goals_sched)
    s.run()
