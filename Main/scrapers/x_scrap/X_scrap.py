import json
from pathlib import Path
import asyncio

from Main.GPT import GPT
from Main.scrapers.x_scrap.utils import TweetRequest

PATH = Path(__file__).parent.parent.parent

DEFAULT_TWIT_EMAIL = "twanalyzefortwitter@gmail.com"
DEFAULT_TWIT_PASSWORD = "Hby2yPsivXRy"
DEFAULT_TWIT_USER_NAME = "twanalyze133266"


class X_Scraper:
    def __init__(self, name, browser_manager):
        self.name = name
        self.browser_manager = browser_manager
        self.cookies_manager = browser_manager.cookies_manager

        self.email = DEFAULT_TWIT_EMAIL
        self.password = DEFAULT_TWIT_PASSWORD
        self.login = DEFAULT_TWIT_USER_NAME
        self.login_page = "https://x.com/login"
        self.gpt = GPT()

    async def check_login_asking(self):
        selector_first = 'input[autocomplete="on"][autocapitalize="none"][autocorrect="off"][inputmode="text"]'

        # Убедимся, что создаются задачи, а не обычные типы
        task_first = self.browser_manager.wait_until_element_exists(selector_first, timeout=5000)
        if task_first:
            return True


    async def log_in(self):
        if self.browser_manager.wait_until_element_exists('input[autocomplete="username"]', timeout=15000):
            self.browser_manager.locator_fill('input[autocomplete="username"]', self.email)
            self.browser_manager.click_button("Next")
            print(await self.check_login_asking())
            if await self.check_login_asking():
                self.browser_manager.locator_fill(
                    'input[autocomplete="on"][autocapitalize="none"][autocorrect="off"][inputmode="text"]',
                    self.login
                )
                self.browser_manager.click_button("Next")
            self.browser_manager.locator_fill('input[autocomplete="current-password"]', self.password)
            self.browser_manager.click_button("Log in")
            self.browser_manager.click_button("Accept all cookies")
            print(self.browser_manager.page)
            cookies = self.browser_manager.run_async(self.browser_manager.page.context.cookies())
            print("Полученные cookies:", cookies)  # Отладочный вывод cookies
            self.cookies_manager.create_cookie_file("X", cookies)
            # для запуска любой асинхроной функции в browser_manager

    async def find_user_id_and_description(self):
        try:
            selector = '//script[@type="application/ld+json" and @data-testid="UserProfileSchema-test"]'
            self.browser_manager.wait_until_element_exists(selector, timeout=15000)
            json_data = self.browser_manager.get_element_text(selector)
            if not json_data:
                raise ValueError("JSON script is empty or not found.")
            data = json.loads(json_data)
            main_entity = data.get("mainEntity", {})
            identifier = main_entity.get("identifier")
            description = main_entity.get("description")
            return identifier, description
        except Exception as e:
            print(f"Error extracting user data: {e}")
            return None, None

    async def get_cookies_and_authorize(self):
        if not self.cookies_manager.check_for_x():
            self.browser_manager.navigate_to_url(self.login_page)
            await self.log_in()

    async def scrap(self):
        await self.get_cookies_and_authorize()
        profile_url = f"https://x.com/{self.name}"
        self.browser_manager.navigate_to_url(profile_url)
        user_id, description = await self.find_user_id_and_description()
        print(user_id)
        if user_id:
            print(f"{self.name} scraping started")
            print(self.browser_manager.cookies)
            tweets_request = TweetRequest(user_id)
            tweets = await tweets_request.get_all_tweets()

            gpt_response = await self.gpt.send_gpt_request(self.name, tweets, description)
            print(f"{self.name} INFO")
            print(gpt_response)
