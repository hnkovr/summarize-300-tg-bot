# main2_Summarize300Client.py
import time
import requests
from app.wrappers import log_, raise_
from loguru import logger as log

class Summarize300Client:
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
        log_(None, endpoint=self.ENDPOINT, payload=json_payload, headers=self.headers)
        response = requests.post(self.ENDPOINT, json=json_payload, headers=self.headers)
        log_(response)

        if response.status_code == 401:
            raise_("Unauthorized: Invalid credentials.")
        elif response.status_code != 200:
            raise_(f"Unexpected HTTP status: {response.status_code}, Response: {response.text}")
        return response

    def _parse_article(self, url, data):
        assert "thesis" in data, f"{url}: Missing 'thesis' in response"
        self.buffer.add(f"<b>{data['title']}</b>\n\n")
        for point in data["thesis"]:
            self.buffer.add(f"• {point['content']}\n")
            if "link" in point:
                self.buffer.add(f"<a href=\"{point['link']}\">Link</a>\n")
        self.buffer.add("\n")

    def _parse_video(self, url, data):
        assert "keypoints" in data, f"{url}: Missing 'keypoints' in response"
        self.buffer.add(f"{data['title']}\n")
        for keypoint in data["keypoints"]:
            self.buffer.add(f"• {keypoint['content']}\n")
            for thesis in keypoint["theses"]:
                self.buffer.add(f"  - {thesis['content']}\n")

    def summarize(self, url):
        log.debug(f"Starting summarization for URL: {url}")
        json_payload = {"video_url" if "youtu" in url else "article_url": url}
        parse_fn = self._parse_video if "youtu" in url else self._parse_article

        retries, session_id = 0, None

        while retries < self.MAX_RETRIES:
            response = self.__send_request(json_payload)
            data = response.json()
            log.debug(f"Response JSON: {data}")

            if "status_code" not in data:
                raise_(f"Invalid API response for {url}: {data}")

            if data["status_code"] in (0, 2):
                parse_fn(url, data)
                return self.buffer

            if "poll_interval_ms" in data:
                time.sleep(data["poll_interval_ms"] / 1000)

            if not session_id:
                session_id = data.get("session_id")
                json_payload["session_id"] = session_id

            retries += 1

        raise_(f"Max retries exceeded for {url}")

class MessageBuffer:
    MAX_LIMIT = 4096

    def __init__(self):
        self.messages, self.current = [""], 0

    def add(self, message):
        if len(self.messages[self.current]) + len(message) > self.MAX_LIMIT:
            self.messages.append("")
            self.current += 1
        self.messages[self.current] += message

    def __iter__(self):
        return iter(self.messages)
