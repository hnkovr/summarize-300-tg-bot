# /Users/Shared/github/@hnkovr/summarize-300-tg-bot/app/main2_Summarize300Client.py
# vk15: https://chatgpt.com/c/66dee005-3754-8009-8603-116933ec9d69

import time

import requests
from loguru import logger as log


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
        log.debug(f"Summarize300Client initialized with headers: {self.headers}")

    def __send_request(self, json_payload):
        """Sends a POST request to the Yandex API."""
        log.debug(f"Sending request to {self.ENDPOINT} with payload: {json_payload}")
        log.debug(f"Request headers: {self.headers}")
        response = requests.post(self.ENDPOINT, json=json_payload, headers=self.headers)

        # Log response details
        log.debug(f"Response status code: {response.status_code}")
        log.debug(f"Response headers: {response.headers}")
        log.debug(f"Response content: {response.text}")

        if response.status_code == 401:
            log.error("Unauthorized: Check your YANDEX_OAUTH or YANDEX_COOKIE.")
            raise Exception("Unauthorized: Invalid credentials.")
        elif response.status_code != 200:
            log.error(f"Unexpected HTTP status: {response.status_code}, Response: {response.text}")
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        return response

    def _parse_article(self, url, data):
        """Parses the article summarization response."""
        if "thesis" not in data:
            raise ValueError(f"{url}: Missing 'thesis' in response")
        self.buffer.add(f"<b>{data['title']}</b>\n\n")
        for point in data["thesis"]:
            self.buffer.add(f"• {point['content']}\n")
            if "link" in point:
                self.buffer.add(f"<a href=\"{point['link']}\">Link</a>\n")
        self.buffer.add("\n")

    def _parse_video(self, url, data):
        """Parses the video summarization response."""
        if "keypoints" not in data:
            raise ValueError(f"{url}: Missing 'keypoints' in response")
        self.buffer.add(f"{data['title']}\n")
        for keypoint in data["keypoints"]:
            self.buffer.add(f"• {keypoint['content']}\n")
            for thesis in keypoint["theses"]:
                self.buffer.add(f"  - {thesis['content']}\n")

    def summarize(self, url):
        """Summarizes the given URL."""
        log.debug(f"Starting summarization for URL: {url}")
        json_payload = {"video_url" if "youtu" in url else "article_url": url}
        parse_fn = self._parse_video if "youtu" in url else self._parse_article

        log.debug(f"Assigned parse function: {parse_fn.__name__}")

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



class MessageBuffer:
    """Handles message batching for Telegram messages."""
    MAX_LIMIT = 4096  # Telegram message character limit

    def __init__(self):
        self.messages, self.current = [""], 0

    def add(self, message: str):
        if len(self.messages[self.current]) + len(message) > self.MAX_LIMIT:
            self.messages.append("")
            self.current += 1
        self.messages[self.current] += message

    def __iter__(self):
        return iter(self.messages)


