from openai import OpenAI, AzureOpenAI
from rich.console import Console

console = Console()


def get_search_result(api_key: str, question: str) -> str:
    client = OpenAI(api_key=api_key, base_url="https://api.perplexity.ai")
    response = client.chat.completions.create(
        model="llama-3.1-sonar-large-128k-online",
        messages=[
            {
                "role": "system",
                "content": "You are an artificial intelligence assistant and you need to engage in a helpful, detailed, polite conversation with a user.",
            },
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message


if __name__ == "__main__":
    api_key = "..."
    question = "幫我找一下新竹有啥好吃的消夜"
    response = get_search_result(api_key, question)
    console.print(response)
