import aiohttp
import asyncio
import json
import re

from pathlib import Path
from Main.proxy.request_with_proxy import RequestWithProxy

from Main.cookies.cookies_manager import Cookies


PATH = Path(__file__).parent.parent.parent


async def get_bearer_token():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://abs.twimg.com/responsive-web/client-web/main.e46e1035.js") as response:
            text = await response.text()
            return re.search(r"s=\"([\w%]{104})\"", text)[1]


def filter_tweet(text):
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
        self.cookies_manager = Cookies()
        self.cookies = ""
        self.bearer_token = None

        self.variables = {
            "userId": str(self.user_id),
            "count": 25,
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
            "x-csrf-token": self.cookies_manager.get_cookie_value(self.cookies_manager.get_cookies_for_browser(),"ct0"),
            "cookie": self.cookies_manager.cookies_to_string(self.cookies_manager.get_cookies_for_browser()),
            "Referer": "https://x.com/",
            "Origin": "https://x.com",
        }
        return True

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
        max_iterations = 15
        iteration = 0
        repeat_count = 0
        previous_count = 0
        amount_of_requests = 0

        if await self.initialize():
            while iteration < max_iterations:
                self.variables["cursor"] = current_cursor
                self.params["variables"] = json.dumps(self.variables)
                response = await RequestWithProxy(url=self.url, headers=self.headers,
                                                  params=self.params).fetch_json()

                amount_of_requests += 1
                print(f"Request {amount_of_requests} completed")

                tweets = self.extract_data(response)
                for tweet in tweets:
                    all_tweets.add(filter_tweet(tweet))

                current_count = len(all_tweets)

                if current_count == previous_count:
                    repeat_count += 1
                else:
                    repeat_count = 0
                previous_count = current_count

                if current_count >= 150 or repeat_count >= 1:
                    break

                instructions = (
                    response.get("data", {})
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

                await asyncio.sleep(0.5)
                iteration += 1
                print(len(all_tweets))
            return all_tweets


if __name__ == "__main__":
    test = TweetRequest(36030921)
    print(asyncio.run(test.get_all_tweets()))


