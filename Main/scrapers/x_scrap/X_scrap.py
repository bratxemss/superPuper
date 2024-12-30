import json
from pathlib import Path
from Main.cookies.cookies import Cookies
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
        self.cookies_manager = Cookies(PATH / "cookies" / "cookies_holder" / "X_cookies_file" / "X_cookies_0.json")
        self.browser_manager.set_cookies(self.cookies_manager.get_cookie_data_from_file())

        self.email = DEFAULT_TWIT_EMAIL
        self.password = DEFAULT_TWIT_PASSWORD
        self.login = DEFAULT_TWIT_USER_NAME
        self.login_page = "https://x.com/login"
        self.gpt = GPT()

    async def check_login_asking(self):
        selector_first = 'input[autocomplete="on"][autocapitalize="none"][autocorrect="off"][inputmode="text"]'
        selector_second = 'input[autocomplete="current-password"]'
        return self.browser_manager.is_element_present(selector_first) or \
            self.browser_manager.is_element_present(selector_second)

    async def log_in(self):
        if self.browser_manager.wait_until_element_exists('input[autocomplete="username"]', timeout=15000):
            self.browser_manager.locator_fill('input[autocomplete="username"]', self.email)
            self.browser_manager.click_button("Next")
            if await self.check_login_asking():
                self.browser_manager.locator_fill(
                    'input[autocomplete="on"][autocapitalize="none"][autocorrect="off"][inputmode="text"]',
                    self.login
                )
                self.browser_manager.click_button("Next")
            self.browser_manager.locator_fill('input[autocomplete="current-password"]', self.password)
            self.browser_manager.click_button("Log in")
            self.browser_manager.click_button("Accept all cookies")
            self.browser_manager.run_async(self.cookies_manager.save_cookies_from_page(self.browser_manager.page))
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
        if not self.cookies_manager.get_cookie_data_from_file():
            self.browser_manager.navigate_to_url(self.login_page)
            await self.log_in()

    async def scrap(self):
        print(f"{self.name} scraping started")
        await self.get_cookies_and_authorize()
        profile_url = f"https://x.com/{self.name}"
        self.browser_manager.navigate_to_url(profile_url)
        user_id, description = await self.find_user_id_and_description()
        if user_id:
            tweets_request = TweetRequest(user_id)
            tweets = await tweets_request.get_all_tweets()

            gpt_response = await self.gpt.send_gpt_request(self.name, tweets, description)
            print(f"{self.name} INFO")
            print(gpt_response)
