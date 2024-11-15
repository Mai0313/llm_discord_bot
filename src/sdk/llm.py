from openai import OpenAI
import logfire
from openai.types.chat.chat_completion import ChatCompletion

from src.types.config import Config

SYSTEM_PROMPT = "你是一個有趣的且不拘謹的人, 回答有趣且幽默, 擅長透過幽默風趣的方式解決問題"


class LLMServices(Config):
    def _get_models(self, client: OpenAI) -> str:
        model_list = client.models.list()
        models = [model.id for model in model_list.data]
        return ", ".join(models)

    def get_xai_reply(self, prompt: str) -> ChatCompletion:
        client = OpenAI(api_key=self.xai_api_key, base_url="https://api.x.ai/v1")
        models = self._get_models(client=client)
        logfire.info("Available models", models=models)

        completion = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return completion

    def get_oai_reply(self, prompt: str) -> ChatCompletion:
        client = OpenAI(api_key=self.openai_api_key, base_url="https://api.openai.com/v1")

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return completion

    def get_gai_reply(self, prompt: str) -> ChatCompletion:
        client = OpenAI(
            api_key=self.googleai_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        completion = client.chat.completions.create(
            model="gemini-1.5-pro",
            n=1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return completion


if __name__ == "__main__":
    prompt = "What is the meaning of life, the universe, and everything?"

    llm_services = LLMServices()
    res = llm_services.get_gai_reply(prompt=prompt)
