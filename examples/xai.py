from openai import OpenAI


def get_xai_response(api_key: str, question: str) -> str:
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

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
