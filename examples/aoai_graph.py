from openai import AzureOpenAI
from openai.types.images_response import ImagesResponse


def get_delle_image(api_key: str, prompt: str) -> ImagesResponse:
    client = AzureOpenAI(
        api_key=api_key,
        api_version="2024-02-01",
        azure_deployment="dall-e-3",
        azure_endpoint="https://weich-m5l8mzbx-swedencentral.cognitiveservices.azure.com",
    )
    response = client.images.generate(
        prompt=prompt,
        model="dall-e-3",
        quality="standard",
        response_format="url",
        size="1024x1024",
        style="vivid",
    )
    return response


if __name__ == "__main__":
    api_key = "..."
    prompt = "A painting of a sunset over a mountain"
    response = get_delle_image(api_key, prompt)
