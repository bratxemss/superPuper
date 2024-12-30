import aiohttp
import asyncio
import json
import re

from pathlib import Path
from Main.headers_generator import HeadersGenerator


from Main.cookies.cookies import Cookies


PATH = Path(__file__).parent.parent.parent


async def get_bearer_token():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://abs.twimg.com/responsive-web/client-web/main.e46e1035.js") as response:
            text = await response.text()
            return re.search(r"s=\"([\w%]{104})\"", text)[1]


async def filter_tweet(text):
    text = text.replace("\n", " ")
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'http\S+|www\.\S+', '', text)
    text = re.sub(r'[^\w\s.,!?]', '', text)
    text = text.strip()
    return text


class TweetRequest:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.url = "https://x.com/i/api/graphql/TK4W-Bktk8AJk0L1QZnkrg/UserTweets"
        self.cookies_manager = Cookies(PATH/"cookies"/"cookies_holder"/"X_cookies_file"/"X_cookies_0.json")
        self.headers_generator = HeadersGenerator()
        self.bearer_token = None
        self.headers = None

        self.variables = {
            "userId": str(self.user_id),  # Идентификатор пользователя
            "count": 20,
            "cursor": None,
            "includePromotedContent": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withVoice": True,
            "withV2Timeline": True,
        }

        self.params = {
            "features": json.dumps({
                "profile_label_improvements_pcf_label_in_post_enabled": False,
                "rweb_tipjar_consumption_enabled": True,
                "responsive_web_graphql_exclude_directive_enabled": True,
                "verified_phone_label_enabled": False,
                "creator_subscriptions_tweet_preview_api_enabled": True,
                "responsive_web_graphql_timeline_navigation_enabled": True,
                "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
                "premium_content_api_read_enabled": False,
                "communities_web_enable_tweet_community_results_fetch": True,
                "c9s_tweet_anatomy_moderator_badge_enabled": True,
                "responsive_web_grok_analyze_button_fetch_trends_enabled": True,
                "articles_preview_enabled": True,
                "responsive_web_edit_tweet_api_enabled": True,
                "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
                "view_counts_everywhere_api_enabled": True,
                "longform_notetweets_consumption_enabled": True,
                "responsive_web_twitter_article_tweet_consumption_enabled": True,
                "tweet_awards_web_tipping_enabled": False,
                "creator_subscriptions_quote_tweet_preview_enabled": False,
                "freedom_of_speech_not_reach_fetch_enabled": True,
                "standardized_nudges_misinfo": True,
                "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
                "rweb_video_timestamps_enabled": True,
                "longform_notetweets_rich_text_read_enabled": True,
                "longform_notetweets_inline_media_enabled": True,
                "responsive_web_enhance_cards_enabled": False,
            }),
            "fieldToggles": json.dumps({"withArticlePlainText": False}),
        }

    async def initialize(self):
        self.bearer_token = await get_bearer_token()
        self.headers = {
            "Authorization": f"Bearer {self.bearer_token}",
            "User-Agent": await self.headers_generator.generate_allowed_agent(),
            "x-csrf-token": self.cookies_manager.get_value_from_cookie("ct0"),
            "cookie": self.cookies_manager.cookies_to_string(),
            "Referer": "https://x.com/",
            "Origin": "https://x.com",
        }

    def extract_data(self, tweet_data):
        texts = []
        if isinstance(tweet_data, dict):
            for key, value in tweet_data.items():
                if key == "full_text":
                    texts.append(value)
                elif isinstance(value, (dict, list)):
                    texts.extend(self.extract_data(value))
        elif isinstance(tweet_data, list):
            for item in tweet_data:
                texts.extend(self.extract_data(item))
        return texts

    async def get_all_tweets(self):
        all_tweets = set()
        current_cursor = None
        max_iterations = 100
        iteration = 0
        repeat_count = 0  # Счетчик повторений
        previous_count = 0  # Предыдущее количество твитов
        amount_of_requests = 0
        await self.initialize()

        async with aiohttp.ClientSession() as session:
            while iteration < max_iterations:
                self.variables["cursor"] = current_cursor
                self.params["variables"] = json.dumps(self.variables)

                try:
                    async with session.get(self.url, headers=self.headers, params=self.params) as response:
                        if response.status == 200:
                            response_json = await response.json()
                            amount_of_requests += 1
                            print(f"Request {amount_of_requests} completed")
                            tweets = self.extract_data(response_json)
                            for tweet in tweets:
                                all_tweets.add(await filter_tweet(tweet))

                            current_count = len(all_tweets)
                            if current_count == previous_count:
                                repeat_count += 1
                            else:
                                repeat_count = 0
                            previous_count = current_count

                            # if current_count >= 100:
                            #     return all_tweets

                            if repeat_count >= 2:
                                break

                            instructions = (
                                response_json.get("data", {})
                                .get("user", {})
                                .get("result", {})
                                .get("timeline_v2", {})
                                .get("timeline", {})
                                .get("instructions", [])
                            )

                            current_cursor = None
                            for instruction in instructions:
                                if isinstance(instruction, dict) and "entries" in instruction:
                                    for entry in instruction["entries"]:
                                        if entry.get("entryId", "").startswith("cursor-bottom-"):
                                            current_cursor = entry.get("content", {}).get("value")
                                            break
                                if current_cursor:
                                    break
                            if not current_cursor:
                                break

                            # Задержка между запросами
                            await asyncio.sleep(1)
                            iteration += 1

                        elif response.status == 400:
                            break

                        elif response.status == 429:
                            break

                except aiohttp.ClientError as e:
                    break
        print("FINISH")
        return all_tweets



