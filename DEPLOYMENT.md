# Deployment Guide for Senpai Bot

This document explains how to get the bot running locally, on a VPS, in a Docker container, and on Heroku.  Follow the section that matches your target environment.

---

## Prerequisites

1. **Python 3.11+** installed (or use the Docker image which includes Python).
2. A Telegram bot token from BotFather and API credentials from https://my.telegram.org.
3. A running MongoDB instance (Atlas recommended) and connection string.
4. If using AI features, a Groq API key from https://groq.com.
5. Configure `senpai_bot/config.py` with all required fields (see comments in file).
6. Install dependencies will fetch `apscheduler` which is used for periodic tasks such as resetting monthly scores.


## Local development

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp senpai_bot/config.py.example senpai_bot/config.py  # or edit directly
# fill in credentials
python -m senpai_bot.main
```

Bot will start and log "Senpai Bot is running...".  Interact with it on Telegram.

---

## Running in Docker

1. Build the image:
   ```bash
docker build -t senpai-bot:latest .
```
2. Run the container with environment variables or bind-mount a config file:
   ```bash
docker run -d --name senpai \
  -v $PWD/senpai_bot/config.py:/app/senpai_bot/config.py \
  -e MONGO_URI="your_uri" \
  -e BOT_TOKEN="your_token" \
  senpai-bot:latest
```

3. Logs:
   ```bash
docker logs -f senpai
```

---

## Deploying to a VPS

1. Provision a Linux server (Ubuntu/Debian/CentOS).
2. Install Python, Git, and Docker (optional).
3. Clone repository:
   ```bash
git clone <your-repo-url>
cd SenpaiChat
```
4. Copy `config.py` and fill credentials.
5. Install dependencies and run as service:
   ```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nohup python -m senpai_bot.main &
```
   or use `systemd` unit:
   ```ini
   [Unit]
   Description=Senpai Telegram Bot
   After=network.target

   [Service]
   User=youruser
   WorkingDirectory=/path/to/SenpaiChat
   ExecStart=/path/to/venv/bin/python -m senpai_bot.main
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
6. Ensure firewall allows outgoing connections (MongoDB, Groq).

---

## Deploying to Heroku

1. Install the Heroku CLI and log in: `heroku login`.
2. Create an app: `heroku create senpai-bot`.
3. Add MongoDB addon or configure `MONGO_URI` as config var.
4. Add necessary config vars:
   ```bash
heroku config:set BOT_TOKEN=yourtoken API_ID=... API_HASH=... OWNER_ID=... \
  GROQ_API_KEY=... BOT_USERNAME=... BOT_STICKER_PACK=... CHAT_HISTORY_LIMIT=12
```
5. Push repository to Heroku:
   ```bash
git push heroku main
```
6. Scale the worker (or web) dyno:
   ```bash
heroku ps:scale web=1
```
   (web dyno is fine; the bot runs in the same process.)
7. View logs: `heroku logs --tail`.

---

## Maintenance notes

- **Updating code:** pull new commits and restart process/container.
- **Database backups:** configure MongoDB export.
- **Secrets:** rotate tokens by editing `config.py` or using env vars.

Good luck deploying Senpai Bot!  🛠️
