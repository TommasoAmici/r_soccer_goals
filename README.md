[![CI/CD](https://github.com/TommasoAmici/r_soccer_goals/actions/workflows/docker.yml/badge.svg)](https://github.com/TommasoAmici/r_soccer_goals/actions/workflows/docker.yml)

# r_soccer_goals

A Telegram bot that reposts Serie A goals (or any type of content) from /r/soccer/new (or other subreddits) to a channel.

## Usage

### With Docker

- Pull the image
  ```zsh
  docker pull tommasoamici/r_soccer_goals:latest
  ```

- Create a `.env` file with the required [environment variables](##Environment-variables).
- Run the image 
  ```zsh
  docker run --env-file .env r_soccer_goals:latest
  ```

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
- `REDDIT_SUBREDDIT`: subreddit the bot will monitor for incoming posts
- `TEAMS`: comma separated list of teams you want to receive goals for. e.g. "Juventus,Inter,Milan".
  Defaults to current Serie A teams.
