import asyncio
import os
import json
import datetime
from typing import Callable, Any


def check_file_exists(file_path):
    return os.path.exists(file_path)


def get_min_second_element(data):
    if not data:
        return None
    return min(data, key=lambda x: x[1])


class Cookies:
    def __init__(self,cookies_file):
        self.cookies_file = cookies_file
        self.cookies = self.get_cookie_data_from_file()
        self.cookies_with_timer = self.check_ticket_expiry()
        self.file_exists = check_file_exists(self.cookies_file)

    async def save_cookies_from_page(self, page):
        cookies = await page.context.cookies()
        with open(self.cookies_file, "w") as f:
            json.dump(cookies, f, indent=4, ensure_ascii=False)
        return cookies

    async def load_cookies_to_context(self, context, cookies):
        if cookies:
            await context.add_cookies(cookies)

    def get_value_from_cookie(self,cookie_name):
        for cookie in self.cookies:
            if cookie["name"] == cookie_name:
                return cookie["value"]

    def get_cookie_data_from_file(self):
        if check_file_exists(self.cookies_file):
            with open(self.cookies_file, "r") as f:
                try:
                    cookies = json.load(f)
                    return cookies
                except json.JSONDecodeError:
                    print("Ошибка парсинга  Проверьте формат файла.")
                    return {}
        return {}

    def cookies_to_string(self):
        cookies = self.get_cookie_data_from_file()
        if isinstance(cookies, list):
            return "; ".join(
                [f"{cookie['name']}={cookie['value']}" for cookie in cookies if 'name' in cookie and 'value' in cookie])
        elif isinstance(cookies, dict):
            return "; ".join([f"{key}={value}" for key, value in cookies.items()])
        return ""

    def check_ticket_expiry(self):
        cookies = self.cookies
        if not cookies:
            return None

        result = []

        for cookie in cookies:
            if "expires" in cookie:
                expiry_timestamp = cookie["expires"]
            elif "maxAge" in cookie:
                expiry_timestamp = int(datetime.datetime.utcnow().timestamp()) + cookie["maxAge"]
            else:
                continue

            result.append({cookie["name"]: expiry_timestamp})
        return result

    async def check_authorize_timer(self, main_key):
        data = []
        if self.cookies_with_timer:
            for cookie in self.cookies_with_timer:
                for key, value in cookie.items():
                    if key == main_key:
                        data.append([key, value])
        data = get_min_second_element(data)
        if data is None or len(data) < 2:
            return True
        if data[1] <= int(datetime.datetime.now(datetime.UTC).timestamp()):
            return True
        return False

    async def call_authorize_timer_on_func(self, func: Callable, *args, **kwargs) -> Any:
        if await self.check_authorize_timer("auth_token"):
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

