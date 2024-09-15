[![CI/CD](https://github.com/TommasoAmici/r_soccer_goals/actions/workflows/docker.yml/badge.svg)](https://github.com/TommasoAmici/r_soccer_goals/actions/workflows/docker.yml)

# r_soccer_goals

A Telegram bot that reposts Serie A goals (or any type of content) from /r/soccer/new (or other subreddits) to a channel.

## Usage

### With Docker

Pull the image:

```sh
docker pull tommasoamici/r_soccer_goals:latest
```

Create a `.env` file with the required [environment variables](#environment-variables).

Run the image:

```sh
docker run --env-file .env r_soccer_goals:latest
```

### Without Docker

- Create a virtual environment with `python -m venv venv`
- Activate the virtual environment with `source venv/bin/activate`
- Install all the requirements with `python -m pip install -r requirements.txt`
- Set the required [environment variables](#environment-variables).

## Environment variables

- `TELEGRAM_CHAT_ID`: chat to which the bot will send the video clips
- `TELEGRAM_BOT_TOKEN`
- `REDDIT_CLIENT_ID`: reddit app client id (see this small [how-to](https://rymur.github.io/setup))
- `REDDIT_CLIENT_SECRET`:
- `REDDIT_SUBREDDIT`: subreddit the bot will monitor for incoming posts
- `TEAMS`: comma separated list of teams you want to receive goals for. e.g. "Juventus,Inter,Milan".
  Defaults to current Serie A teams.
- `DB_PATH`: path to the sqlite database file, defaults to `r_soccer_goals.db`
