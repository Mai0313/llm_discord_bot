from openai import OpenAI
from openai._legacy_response import HttpxBinaryResponseContent


def get_tts(api_key: str, prompt: str) -> HttpxBinaryResponseContent:
    client = OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        input=prompt, model="tts-1-hd", voice="alloy", response_format="mp3"
    )
    return response


if __name__ == "__main__":
    api_key = "..."
    prompt = "妳是大傻必"
    response = get_tts(api_key, prompt)
    with open("output.mp3", "wb") as f:
        f.write(response.content)
