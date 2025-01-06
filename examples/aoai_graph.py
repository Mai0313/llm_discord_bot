from openai import OpenAI
from openai.types.images_response import ImagesResponse


def get_delle_image(api_key: str, prompt: str) -> ImagesResponse:
    client = OpenAI(api_key=api_key)
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
