from openai import OpenAI


def get_xai_response(api_key: str, question: str) -> None:
    client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")

    completion = client.chat.completions.create(
        model="grok-beta",
        messages=[
            {
                "role": "system",
                "content": "You are Grok, a chatbot inspired by the Hitchhikers Guide to the Galaxy.",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    print(completion.choices[0].message)


if __name__ == "__main__":
    api_key = (
        "xai-DXMhKNnVX1wEPdxy1oziThWPMljZPOJlkJUmYzAlNqq265Yjzgq2ValOBQ6ooS1dLZQcp6hkysw1WaDC"
    )
    question = "What is the meaning of life, the universe, and everything?"
    get_xai_response(api_key=api_key, question=question)
