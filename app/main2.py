import os, sys
from pathlib import Path
from app.wrappers import log_send, log_
from app.main2_Summarize300Client import Summarize300Client

try:
    import dotenv, yaml
    dotenv.load_dotenv()
except ImportError:
    os.system('pip install pyyaml fastcore requests loguru python-dotenv') and sys.exit(1)

import re
from fastcore.foundation import Config
from loguru import logger as log
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

class AppConfig:
    DEFAULT_CONFIG = {
        "YANDEX_OAUTH": os.getenv("YANDEX_OAUTH"),
        "YANDEX_COOKIE": os.getenv("YANDEX_COOKIE"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "DEVELOPER_CHAT_ID": os.getenv("DEVELOPER_CHAT_ID"),
    }

    def __init__(self, config_path="config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_or_create_config()

    def _load_or_create_config(self):
        if self.config_path.exists():
            return yaml.safe_load(self.config_path.read_text())
        else:
            self.config_path.write_text(yaml.dump(self.DEFAULT_CONFIG))
            log.warning(f"No config found. Default config created at {self.config_path}.")
            return self.DEFAULT_CONFIG

    def __getattr__(self, item):
        return self.config.get(item)

async def send_message(context, chat_id, text):
    await context.bot.send_message(chat_id=chat_id, text=text)

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"Message from {update.effective_user.username}: {update.message.text}")
    urls = re.findall(r"(https?://[^\s&]+)", update.message.text)
    if not urls:
        await send_message(context, update.effective_chat.id, "Send a valid link to an article or YouTube video.")
        return

    client = Summarize300Client(
        oauth_token=context.bot_data["YANDEX_OAUTH"],
        cookie=context.bot_data["YANDEX_COOKIE"],
    )

    for url in urls:
        try:
            buffer = client.summarize(url)
            for msg in buffer:
                await send_message(context, update.effective_chat.id, msg)
        except Exception as e:
            await log_send(context, update.effective_chat.id, f"Error processing {url}: {e}")

def main():
    config = AppConfig()
    log_((config.YANDEX_OAUTH, config.YANDEX_COOKIE))
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

if __name__ == "__main__":
    main()
