import asyncio
import threading

from playwright.async_api import async_playwright, Page
from fake_headers import Headers





class BrowserManager:
    def __init__(self,cookies, headless=False):
        self.headless = headless
        self.cookies_manager = cookies
        self.cookies = asyncio.run(cookies.get_cookies_for_browser())
        self.headers = Headers(browser="chrome").generate()

        self._browser_context = None
        self.page: Page = None
        self._loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self.thread.start()

    def set_cookies(self, cookies):
        self.run_async(self._add_cookies(cookies))

    async def _add_cookies(self, cookies):
        if not self._browser_context:
            raise RuntimeError("Browser context is not initialized. Call start_browser() first.")
        await self._browser_context.add_cookies(cookies)

    def _start_async_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def run_async(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    async def _initialize_browser(self):
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=self.headless)
        self._browser_context = await browser.new_context(locale="en-US")
        user_agent = self.headers["User-Agent"]
        await self._browser_context.set_extra_http_headers({"User-Agent": user_agent})
        if self.cookies:
            await self._browser_context.add_cookies(self.cookies)

        self.page = await self._browser_context.new_page()

    def start_browser(self):
        self.run_async(self._initialize_browser())

    async def _navigate_to_url(self, url):
        if self.page:
            await self.page.goto(url, wait_until="domcontentloaded")
        else:
            raise RuntimeError("Browser is not initialized. Call start_browser() first.")

    def navigate_to_url(self, url: str):
        self.run_async(self._navigate_to_url(url))

    async def _click_button(self, text: str):
        try:
            locator = self.page.locator(f"button:has-text('{text}')")
            await locator.wait_for(state="visible", timeout=30000)  # Ждать появления элемента до 30 секунд
            await locator.click()

        except Exception as e:
            print(f"Ошибка при попытке найти и нажать на кнопку с текстом '{text}': {e}")
            raise

    def click_button(self, text: str):
        self.run_async(self._click_button(text))

    async def _wait_until_element_exists(self, selector: str, timeout: int = 15000, interval: int = 500):
        elapsed_time = 0

        while elapsed_time < timeout:
            if await self._is_element_present(selector):
                return True
            await asyncio.sleep(interval / 1000)  # Ожидание заданного интервала
            elapsed_time += interval

        return False

    async def _locator_fill(self, selector: str, value: str):
        await self.page.locator(selector).fill(value)

    def locator_fill(self, selector: str, value: str):
        self.run_async(self._locator_fill(selector, value))

    async def _locator_wait(self, selector: str, timeout: int = 15000):
        await self.page.locator(selector).wait_for(timeout=timeout)

    def locator_wait(self, selector: str, timeout: int = 15000):
        self.run_async(self._locator_wait(selector, timeout=timeout))

    def wait_until_element_exists(self, selector: str, timeout: int = 15000, interval: int = 500):
        return self.run_async(self._wait_until_element_exists(selector, timeout=timeout, interval=interval))

    async def _is_element_present(self, selector: str):
        return await self.page.query_selector(selector) is not None

    def is_element_present(self, selector: str):
        return self.run_async(self._is_element_present(selector))

    async def _get_element_text(self, selector: str):
        element = await self.page.query_selector(selector)
        if element:
            return await element.inner_text()
        return None

    def get_element_text(self, selector: str):
        return self.run_async(self._get_element_text(selector))

    def stop_browser(self):
        if self._browser_context:
            self.run_async(self._browser_context.close())
        self._loop.call_soon_threadsafe(self._loop.stop)
        self.thread.join()
