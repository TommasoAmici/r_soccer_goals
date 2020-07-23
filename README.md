![Tests](https://github.com/TommasoAmici/r_soccer_goals/workflows/Test/badge.svg)
![CI/CD](https://github.com/TommasoAmici/r_soccer_goals/workflows/CI/CD/badge.svg)

# Telegram-bot-r-soccer-goals

A Telegram bot that reposts Serie A goals (or any type of content) from /r/soccer/new (or other subreddits) to a [channel](https://t.me/golledisoccer).

## Usage

### With Docker

- Build the image with `docker build --pull --rm -f "Dockerfile" -t rsoccergoals:latest "."`
- Create a `.env` file with the required [environment variables](##Environment-variables).
- Run the image with `docker run --env-file .env rsoccergoals:latest`

### Without Docker

- Create a virtual environment with `python -m venv venv`
- Activate the virtual environment with `source venv/bin/activate`
- Install all the requirements with `python -m pip install -r requirements.txt`
- Set the required [environment variables](##Environment-variables).

## Environment variables

- `TELEGRAM_CHAT_ID`: chat to which the bot will send the video clips
- `TELEGRAM_BOT_TOKEN`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `REDDIT_USERNAME`
- `REDDIT_PASSWORD`
- `REDDIT_SUBREDDIT`: subreddit the bot will monitor for incoming posts
