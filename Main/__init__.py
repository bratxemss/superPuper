import asyncio
from Main.scrapers.x_scrap.X_scrap import X_Scraper
from Main.browser.browser_manager import BrowserManager

if __name__ == "__main__":
    name = "rasmushansen"
    name2 = "saifedean"
    BM = BrowserManager()

    BM.start_browser()

    obj = X_Scraper(name, BM)
    obj2 = X_Scraper(name2, BM)


    async def main():
       # await obj.scrap()
        await obj2.scrap()


    asyncio.run(main())
