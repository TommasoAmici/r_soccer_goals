from telegram.ext import Updater
import telegram
import praw
import sched, time


teams = ['milan', 'inter', 'napoli', 'juventus', 'roma',
         'lazio', 'spal', 'udinese', 'sampdoria',  'sassuolo',
         'benevento', 'cagliari', 'crotone', 'verona',
         'hellas', 'atalanta', 'chievo', 'torino', 'fiorentina',
         'bologna']


def is_goal(post):
    if post.author == 'AutoModerator' or post.author == 'MatchThreadder':
        return False
    elif post.author == 'Meladroit1' or post.author == 'gemifra' or post.author == 'biffmila':
        if 'internacional' in post.title.lower():
            return False
        else:
            for team in teams:
                if team in post.title.lower():
                    return True
    else:
        return False


def aa_mirror(post):
    mirrors = []
    for comment in post.comments:
        if 'mirror' in comment.body.lower() or 'replay' in comment.body.lower() and len(comment.body) > 30:
            mirrors.append(comment)
        else:
            continue
    return mirrors


def check_soccer_new(reddit):
    to_channel = []
    for post in reddit.subreddit('soccer').new(limit=5):
        if len(post.title) > 100:
            continue
        else:
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
                bot.send_message(chat_id='@golledisoccer', text="{}\n{}".format(post.title,post.url), disable_notification=True)            
        elif isinstance(post, list):
            for comment in post:
                bot.send_message(chat_id='@golledisoccer', text=comment.body, parse_mode="markdown", disable_notification=True)
    s.enter(5, 1, check_goals_sched)


s = sched.scheduler(time.time, time.sleep)    
s.enter(5, 1, check_goals_sched)
s.run()
