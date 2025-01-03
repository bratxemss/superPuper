import aiohttp
from typing import Dict, Any
from Main.proxy.proxy import ProxyHandlerAsync


class RequestWithProxy:
    def __init__(self, url: str, headers: Dict[str, str] = None, params: Dict[str, Any] = None):

        self.url = url
        self.headers = headers or {}
        self.params = params or {}
        self.proxy_handler = ProxyHandlerAsync()

    async def fetch_json(self) -> Dict[str, Any]:
        ssl_context = False

        connector = aiohttp.TCPConnector(ssl=ssl_context)

        async with aiohttp.ClientSession(connector=connector) as session:
            try:
                print(f"Send request with proxy to {self.url}")
                async with session.get(
                        self.url,
                        headers=self.headers,
                        params=self.params,
                        proxy=self.proxy_handler.proxy_url,
                        proxy_auth=self.proxy_handler.proxy_auth
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        print(f"Error {response.status}: {response.content}")
            except aiohttp.ClientError as e:
                print(f"Error while connecting throe proxy: {e}")

        return {}
