

OPENAI_API_KEY = ""

from openai import AsyncOpenAI
import tiktoken


class GPT(AsyncOpenAI):
    def __init__(self, model: str = "gpt-3.5-turbo"):

        super().__init__(api_key=OPENAI_API_KEY)

        self.model = model
        self.encoding = tiktoken.encoding_for_model(self.model)
        self.max_amount_request_tokens = 3096 #full is 4096 but we need 1k for an answer
        self.min_token_amount = 0
        self.cost = []

    async def check_token_amount(self, data: list):
        list_of_valid_messages = [[]]
        list_created = 0
        token_amount = 0

        for message in data:
            message_tokens = len(self.encoding.encode(message))
            token_amount += message_tokens

            if not (self.max_amount_request_tokens - 200 <= token_amount <= self.max_amount_request_tokens + 200):
                list_of_valid_messages[list_created].append(message)
            else:
                list_of_valid_messages.append([])
                list_created += 1
                token_amount = 0

        else:
            self.min_token_amount += (self.max_amount_request_tokens - token_amount)

            if self.min_token_amount > 400:
                self.min_token_amount = 400

        return list_of_valid_messages

    async def generate_question(self, user: str, user_tweets: list, description: str, previous_answer: str = ""):
        try:
            user_input = f"Posts: '{'. '.join(user_tweets)}', Description: '{description}', username: '{user}', previous answer: '{previous_answer}'"

            if self.min_token_amount <= 0:
                content = "Based on the following data provide a brief summary about this person. Include their interests, personality, and any notable traits. Use English language."
            else:
                content = "Based on the following data provide a brief summary about this person. Include their interests, personality, and any notable traits. Use English language. You should get about 2-3 paragraphs with 5-6 sentences each of information and a conclusion "

            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",
                 "content": content},
                {"role": "user", "content": user_input}
            ]

            answer = await self.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1500)

            # usage = answer.usage
            # prompt_tokens = usage.prompt_tokens
            # completion_tokens = usage.completion_tokens
            #
            # # Расчет стоимости (в зависимости от модели - GPT-3.5-turbo)
            # price_per_1k_tokens_prompt = 0.0015
            # price_per_1k_tokens_completion = 0.002
            #
            # cost_prompt = (prompt_tokens / 1000) * price_per_1k_tokens_prompt
            # cost_completion = (completion_tokens / 1000) * price_per_1k_tokens_completion
            # total_cost = cost_prompt + cost_completion

            # self.cost.append(total_cost)

            return answer.choices[0].message.content

        except Exception as ex:
            import traceback
            print("Error in get_response:", traceback.format_exc())
            return "An error occurred while processing your request."

    async def send_gpt_request(self, user: str, user_tweets: list, description: str):
        response = ""
        valid_data = await self.check_token_amount(user_tweets)
        iteration = 0

        for data in valid_data:
            if data and iteration == 0:
                response = await self.generate_question(user, data, description)
            elif data and iteration > 0:
                response = await self.generate_question(user, data, description, previous_answer=response)
            iteration += 1

        return response



