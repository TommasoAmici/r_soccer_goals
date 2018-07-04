"""
Stores all secret keys for services and application
"""


class reddit_settings:
    def __init__(self):
        self.client_id = ""
        self.client_secret = ""
        self.user_agent = ""
        self.username = ""
        self.password = ""
        self.subreddit = ""


class telegram_settings:
    def __init__(self):
        self.chat_id = ""
        self.bot_token = ""


class streamable_settings:
    def __init__(self):
        self.email = ""
        self.password = ""
