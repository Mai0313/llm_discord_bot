from openai import OpenAI
import logfire

import autorootcwd
from src.types.config import Config


class LLMServices(Config):
    def _get_models(self, client: OpenAI) -> str:
        model_list = client.models.list()
        models = [model.id for model in model_list.data]
        return ", ".join(models)

    def get_xai_response(self, question: str) -> str:
        client = OpenAI(api_key=self.xai_api_key, base_url="https://api.x.ai/v1")
        models = self._get_models(client=client)
        logfire.info("Available models", models=models)

        completion = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {
                    "role": "system",
                    "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy.",
                },
                {"role": "user", "content": question},
            ],
        )
        return completion.choices[0].message

    def get_oai_response(self, question: str) -> str:
        client = OpenAI(api_key=self.openai_api_key, base_url="https://api.openai.com/v1")

        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy.",
                },
                {"role": "user", "content": question},
            ],
        )
        return completion.choices[0].message

    # def get_gai_response(self, question: str) -> str:
    #     client = OpenAI(
    #         api_key=self.googleai_api_key,
    #         base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    #     )

    #     completion = client.chat.completions.create(
    #         model="gemini-1.5-flash",
    #         n=1,
    #         messages=[
    #             {"role": "system", "content": "You are a helpful assistant."},
    #             {"role": "user", "content": question},
    #         ],
    #     )
    #     return completion.choices[0].message


if __name__ == "__main__":
    question = "What is the meaning of life, the universe, and everything?"

    llm_services = LLMServices()
    res = llm_services.get_oai_response(question=question)
