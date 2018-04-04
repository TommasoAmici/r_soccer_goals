from telegram.ext import Updater
import telegram
import praw
import sched, time
import logging


def is_goal(post):
    teams = ['milan', 'inter', 'napoli', 'juve', 'roma',
             'lazio', 'spal', 'udinese', 'sampdoria', 'sassuolo',
             'benevento', 'cagliari', 'crotone', 'verona',
             'hellas', 'atalanta', 'chievo', 'torino', 'fiorentina',
             'bologna']
    to_drop = ['internacional', 'match']
    if any(drop in post.title.lower() for drop in to_drop):
        return False
    else:
        for team in teams:
            if team in post.title.lower():
                return True
            else:
                continue


def aa_mirror(post):
    mirrors = []
    for c in post.comments:
        if ('mirror' in c.body.lower() or 'replay' in c.body.lower() and len(c.body) > 30) and 'aa' in c.body.lower():
            mirrors.append(c)
        else:
            continue
    return mirrors


def check_soccer_new(reddit):
    to_channel = []
    streams = ['streamable', 'flixtc', 'mixtape', 'v.reddit', 'clippituser', 'streamja']
    posts = [p for p in reddit.subreddit('soccer').new(limit=15) if any(s in p.url for s in streams)]
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
    bot_token = ''
    bot = telegram.Bot(token=bot_token)
    updater = Updater(bot_token)
    reddit = praw.Reddit(client_id="",
                         client_secret="",
                         user_agent="",
                         username='',
                         password='')
    to_channel = check_soccer_new(reddit)
    for post in to_channel:
        if isinstance(post, praw.models.reddit.submission.Submission):
            try:
                bot.send_document(chat_id='@golledisoccer', document=post.url, caption=post.title, disable_notification=True)
            except:
                bot.send_message(chat_id='@golledisoccer',
                                 text="{}\n{}".format(post.title, post.url),
                                 parse_mode='markdown', disable_notification=True)            
        elif isinstance(post, list):
            for comment in post:
                bot.send_message(chat_id='@golledisoccer',
                                 text='**AA/Mirror**\n{}'.format(comment.body),
                                 parse_mode="markdown",
                                 disable_notification=True)
    s.enter(5, 1, check_goals_sched)


if __name__ == "__main__":
    logging.info('Starting /r/soccer_golle_bot')
    s = sched.scheduler(time.time, time.sleep)    
    s.enter(5, 1, check_goals_sched)
    s.run()
