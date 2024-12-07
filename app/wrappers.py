# wrappers.py
import requests
from loguru import logger as log

def log_send(context, chat_id, message):
    """Logs an error and sends a Telegram message."""
    log.error(message)
    return context.bot.send_message(chat_id=chat_id, text=message)

def raise_(message):
    """Logs an error and raises an exception."""
    log.error(message)
    raise Exception(message)

def log_(obj, **kwargs):
    """Overloaded logging for different scenarios."""
    if "endpoint" in kwargs and "payload" in kwargs and "headers" in kwargs:
        log.debug(f"Sending request to {kwargs['endpoint']} with payload: {kwargs['payload']} and headers: {kwargs['headers']}")
    elif isinstance(obj, requests.Response):
        log.debug(f"Response status: {obj.status_code}, Headers: {obj.headers}, Content: {obj.text}")
    elif isinstance(obj, tuple) and len(obj) == 2:
        log.debug(f"YANDEX_OAUTH: {obj[0][:10]}... (truncated), YANDEX_COOKIE: {obj[1][:20]}... (truncated)")
