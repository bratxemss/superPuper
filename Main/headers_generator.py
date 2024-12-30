from fake_headers import Headers


class HeadersGenerator():

    async def generate_allowed_agent(self):
        from random import choice
        list_of_agents = ["chrome", "firefox", "opera"]
        headers = Headers(browser=choice(list_of_agents)).generate()
        print(headers)
        return headers["User-Agent"]


