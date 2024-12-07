# /Users/Shared/github/@hnkovr/summarize-300-tg-bot/app/main2.py
# vk15: https://chatgpt.com/c/66dee005-3754-8009-8603-116933ec9d69

import os, sys

from app.main2_Summarize300Client import Summarize300Client, MessageBuffer

try:
    import loguru, dotenv;

    dotenv.load_dotenv()
    import requests
    import yaml
except ImportError:
    os.system('pip install pyyaml fastcore requests loguru python-dotenv'), sys.exit(1)

import re
import time
from fastcore.foundation import Config
from loguru import logger as log
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters


class AppConfig:
    """Handles application configuration using a `config.yaml` file."""
    DEFAULT_CONFIG = {
        "YANDEX_OAUTH": os.environ['YANDEX_OAUTH'],
        "YANDEX_COOKIE": os.environ['YANDEX_COOKIE'],
        "TELEGRAM_BOT_TOKEN": os.environ['TELEGRAM_BOT_TOKEN'],
        "DEVELOPER_CHAT_ID": os.environ['DEVELOPER_CHAT_ID'],
    }

    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.config = self._load_or_create_config()

    def _load_or_create_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.DEFAULT_CONFIG, f)
            log.warning(f"No config found. Default config created at {self.config_path}.")
            return self.DEFAULT_CONFIG

    def __getattr__(self, item):
        return self.config.get(item)


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"Message from {update.effective_user.username}: {update.message.text}")
    urls = re.findall(r"(https?://[^\s&]+)", update.message.text)
    if not urls:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Send a valid link to an article or YouTube video.",
        )
        return

    client = Summarize300Client(
        oauth_token=context.bot_data["YANDEX_OAUTH"],
        cookie=context.bot_data["YANDEX_COOKIE"],
    )

    for url in urls:
        try:
            buffer = client.summarize(url)
            for msg in buffer:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        except Exception as e:
            log.error(f"Error processing {url}: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Error processing your request.")


def main():
    config = AppConfig()

    # Log key configuration values for debugging
    log.debug(f"YANDEX_OAUTH: {config.YANDEX_OAUTH[:10]}... (truncated)")
    log.debug(f"YANDEX_COOKIE: {config.YANDEX_COOKIE[:20]}... (truncated)")

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()
    app.bot_data.update(
        {
            "YANDEX_OAUTH": config.YANDEX_OAUTH,
            "YANDEX_COOKIE": config.YANDEX_COOKIE,
            "DEVELOPER_CHAT_ID": config.DEVELOPER_CHAT_ID,
        }
    )
    app.add_handler(MessageHandler(filters.TEXT, message_handler))
    app.run_polling()


class Summarize300Client:
    """Handles interactions with Yandex's summarization API."""
    ENDPOINT = "https://300.ya.ru/api/generation"
    MAX_RETRIES = 100

    def __init__(self, oauth_token, cookie):
        self.headers = {
            "Authorization": f"OAuth {oauth_token}",
            "Cookie": cookie,
            "Content-Type": "application/json",
        }
        self.buffer = MessageBuffer()

    def __send_request(self, json_payload):
        """Sends a POST request to the Yandex API."""
        log.debug(f"Sending request to {self.ENDPOINT} with payload: {json_payload}")
        log.debug(f"Request headers: {self.headers}")
        response = requests.post(self.ENDPOINT, json=json_payload, headers=self.headers)

        # Log response status and headers
        log.debug(f"Response status code: {response.status_code}")
        log.debug(f"Response headers: {response.headers}")
        log.debug(f"Response content: {response.text}")

        # Check for unauthorized or other issues
        if response.status_code == 401:
            log.error("Unauthorized: Check your YANDEX_OAUTH or YANDEX_COOKIE.")
            raise Exception("Unauthorized: Invalid credentials.")
        elif response.status_code != 200:
            log.error(f"Unexpected HTTP status: {response.status_code}, Response: {response.text}")
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        return response

    def summarize(self, url):
        """Summarizes the given URL."""
        json_payload = {"video_url" if "youtu" in url else "article_url": url}
        parse_fn = self._parse_video if "youtu" in url else self._parse_article
        retries, session_id = 0, None

        while retries < self.MAX_RETRIES:
            response = self.__send_request(json_payload)
            data = response.json()
            log.debug(f"Response JSON: {data}")

            if "status_code" not in data:
                log.error(f"Invalid API response for {url}: {data}")
                raise Exception("Invalid API response")

            if data["status_code"] in (0, 2):
                parse_fn(url, data)
                return self.buffer

            # Log retry attempts and wait time
            if "poll_interval_ms" in data:
                poll_interval_ms = data["poll_interval_ms"]
                log.debug(f"Poll interval: {poll_interval_ms}ms")
                time.sleep(poll_interval_ms / 1000)

            if not session_id:
                session_id = data.get("session_id")
                json_payload["session_id"] = session_id
                log.debug(f"Session ID set to: {session_id}")

            retries += 1
            log.debug(f"Retrying... Attempt {retries}/{self.MAX_RETRIES}")

        log.error(f"Max retries exceeded for {url}")
        raise Exception("Max retries exceeded")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles incoming Telegram messages."""
    log.info(f"Message from {update.effective_user.username}: {update.message.text}")
    urls = re.findall(r"(https?://[^\s&]+)", update.message.text)
    if not urls:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Send a valid link to an article or YouTube video.",
        )
        return

    client = Summarize300Client(
        oauth_token=context.bot_data["YANDEX_OAUTH"],
        cookie=context.bot_data["YANDEX_COOKIE"],
    )

    for url in urls:
        try:
            log.debug(f"Processing URL: {url}")
            buffer = client.summarize(url)
            for msg in buffer:
                log.debug(f"Sending message: {msg[:100]}... (truncated)")
                await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)
        except Exception as e:
            log.error(f"Error processing {url}: {e}")
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Error processing your request.")


if __name__ == "__main__":
    main()



