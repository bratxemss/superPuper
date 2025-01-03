import asyncio
import os
import json
import datetime
import random
import shutil

from typing import Callable, Any


def check_file_exists(file_path):
    return os.path.exists(file_path)


def get_cookie_data_from_file(file_path: str):
    if check_file_exists(file_path):
        with open(file_path, "r") as f:
            try:
                cookies = json.load(f)
                return cookies
            except json.JSONDecodeError:
                print("Ошибка парсинга  Проверьте формат файла.")
                return {}
    return {}


class Cookies:
    def __init__(self):
        self.cookie_files_location = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies_holder")
        os.makedirs(self.cookie_files_location, exist_ok=True)
        self.key_words = self._get_cookie_files()

        self.cookie_files = self._parse_cookie_folder()
        self.cookies_in_use = {key: [] for key in self.key_words}

    def _get_cookie_files(self):
        return [name.split('_')[0] for name in os.listdir(self.cookie_files_location)]

    def _parse_cookie_folder(self):
        dict_of_files = {}

        for name in self.key_words:
            list_of_files = []
            cookies_holder_file = self.cookie_files_location + "\\" + name + "_cookies_file"

            if check_file_exists(cookies_holder_file):
                list_of_files.extend(os.listdir(cookies_holder_file))

            dict_of_files[name] = list_of_files if list_of_files else []
        return dict_of_files

    def _get_cookies_number(self, name: str):
        """
        name example: "X_cookies_0.json, X_cookies_2.json, X_cookies_3.json"
        """
        return int(self.cookie_files[name][-1].split("_")[-1].split(".")[0])

    def _choice_element(self, name: str):
        if len(self.cookies_in_use[name]) >= len(self.cookie_files[name]):
            oldest_element = self.cookies_in_use[name][0]
            self.cookies_in_use[name].pop(0)
            return oldest_element
        else:
            available_elements = [item for item in self.cookie_files[name] if item not in self.cookies_in_use[name]]
            return random.choice(available_elements) if available_elements else None

    def create_cookie_file(self, name: str, cookies: list[dict]):
        if name not in self.cookie_files:
            self.cookie_files[name] = []
            self.key_words.append(name)

        location = self.cookie_files_location + "\\" + name + "_cookies_file"
        last_number_in_file = self._get_cookies_number(name) + 1 if self.cookie_files[name] else 0

        os.makedirs(location, exist_ok=True)

        cookie_file = name + "_cookies_" + str(last_number_in_file) + ".json"
        file_path = location + "\\" + cookie_file

        with open(file_path, "w") as file:
            json.dump(cookies, file, indent=4, ensure_ascii=False)

        self.cookie_files[name].append(cookie_file)
        return file_path

    def delete_cookie_file(self, name: str, index: int, delete_all: bool = False):
        if name not in self.key_words:
            return None
        location = self.cookie_files_location + "\\" + name + "_cookies_file"
        if delete_all:
            self.key_words.remove(name)
            self.cookie_files.pop(name, None)
            return shutil.rmtree(location)
        if index >= len(self.cookie_files[name]):
            return None
        file_path = location + "\\" + self.cookie_files[name][index]
        os.remove(file_path)
        self.cookie_files[name].pop(index)

    def rewrite_cookie_file(self, name: str, index: int, cookies: list[dict]):
        location = self.cookie_files_location + "\\" + name + "_cookies_file"
        if index >= len(self.cookie_files[name]):
            return None
        file_path = location + "\\" + self.cookie_files[name][index]
        with open(file_path, "w") as file:
            json.dump(cookies, file, indent=4, ensure_ascii=False)
        return file_path

    def add_cookies_to_used(self, name: str, index: int):
        if name in self.key_words and index < len(self.cookie_files[name]):
            self.cookies_in_use[name].append(self.cookie_files[name][index])
            return self.cookies_in_use

    def remove_cookies_from_used(self, name: str, index: int):
        if name in self.cookies_in_use and index < len(self.cookies_in_use[name]):
            self.cookies_in_use[name].pop(index)
            return self.cookies_in_use

    def check_for_x(self):
        if self.cookie_files.get("X") is not None:
            return True
        return False

    def get_cookies_for_browser(self):
        """
        :return: list of path to cookies
        """
        list_of_path_to_cookies = []
        for name, value in self.cookie_files.items():
            element_for_use = self._choice_element(name)
            list_of_path_to_cookies.append(self.cookie_files_location + "\\" + name + "_cookies_file" + "\\" + element_for_use)
            self.cookies_in_use[name].append(element_for_use)
        list_of_cookies = []
        for cookie_path in list_of_path_to_cookies:
            list_of_cookies += (get_cookie_data_from_file(cookie_path))
        return list_of_cookies

    async def create_cookies_using_callable(self, func: Callable, *args, **kwargs) -> Any:
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

    def get_cookie_value(self, cookies: list[dict], key: str):
        for cookie in cookies:
            if cookie["name"] == key:
                return cookie["value"]
        return None

    def cookies_to_string(self, cookies: list[dict] | dict[str, str] | str | None = None,):
        if isinstance(cookies, list):
            return "; ".join(
                [f"{cookie['name']}={cookie['value']}" for cookie in cookies if 'name' in cookie and 'value' in cookie])
        elif isinstance(cookies, dict):
            return "; ".join([f"{key}={value}" for key, value in cookies.items()])
        return ""

    # def check_ticket_expiry(self):
    #     cookies = self.cookies
    #     if not cookies:
    #         return None
    #
    #     result = []
    #
    #     for cookie in cookies:
    #         if "expires" in cookie:
    #             expiry_timestamp = cookie["expires"]
    #         elif "maxAge" in cookie:
    #             expiry_timestamp = int(datetime.datetime.utcnow().timestamp()) + cookie["maxAge"]
    #         else:
    #             continue
    #
    #         result.append({cookie["name"]: expiry_timestamp})
    #     return result





