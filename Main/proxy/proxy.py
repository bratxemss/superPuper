import aiohttp
import ssl


class ProxyHandlerAsync:
    def __init__(self):
        self.proxy_host = "brd.superproxy.io"
        self.proxy_port = 33335
        self.proxy_username = "brd-customer-hl_2b02ff87-zone-germany"
        self.proxy_password = "i05bihf6l1ml"
        self.proxy_url = f"https://{self.proxy_host}:{self.proxy_port}"
        self.proxy_auth = aiohttp.BasicAuth(self.proxy_username, self.proxy_password)

    async def fetch_url(self, url, ignore_ssl=False, ssl_certificate_path=None):
        ssl_context = None
        if ssl_certificate_path:
            ssl_context = ssl.create_default_context(cafile=ssl_certificate_path)
        elif ignore_ssl:
            ssl_context = False

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                print(f"Отправляем запрос через прокси на {url}")
                async with session.get(
                        url,
                        proxy=self.proxy_url,
                        proxy_auth=self.proxy_auth
                ) as response:
                    if response.status == 200:
                        print(f"Статус: {response.status}")
                        return await response.text()
                    else:
                        print(f"Ошибка: {response.status}")
                        return None
            except aiohttp.ClientError as e:
                print(f"Ошибка при подключении: {e}")
                return None

