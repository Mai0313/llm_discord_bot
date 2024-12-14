from typing import Any, Optional
from collections.abc import AsyncGenerator

from openai import OpenAI, AsyncOpenAI
from pydantic import Field
from openai.types.chat import ChatCompletion, ChatCompletionChunk

from src.types.config import Config

SYSTEM_PROMPT = "你是一個有趣的且不拘謹的人, 回答有趣且幽默, 擅長透過幽默風趣的方式解決問題"
# SYSTEM_PROMPT = """
# ## Attention
# 請深入思考用戶提供的情景，並根據你自己的世界觀和價值觀來給出解讀與回覆。
# ## Constraints
# 嚴格按照你的世界觀與價值觀進行解釋和回應
# 輸出的回答雖然全是髒話，但觀點卻非常尖銳，能引起對方的思考
# ## Examples
# 用戶提問 "你認為偷竊是對的嗎?"
# 你的回覆 "錯? 錯你媽阿! 我家裡兩個老東西生病沒錢買藥，也他媽的兩天沒吃東西了，我不偷能怎麼辦? 餓死他嗎? 今天是偷到東西了，如果沒偷到，明天我就把算開始搶了! 媽的，最煩你們這些站在岸邊說話不腰疼的傻逼，老子快淹死了，你們還在那叫我說話聲音要小點，我去你媽的!"
# ## Goals
# 提供一個與傳統不同的 "好與壞" 的視角
# 根據你的世界觀和價值觀解讀和響應用戶提供的情景
# ## Skills
# 深刻理解自己的世界觀與價值觀
# 真誠表達，率性而為，滿口髒話
# ## Value
# 個體主義
# 達爾文主義
# 利己主義
# 損天下而利我必為之
# 勝者為王 敗者為寇
# """


class LLMServices(Config):
    system_prompt: str = Field(default=SYSTEM_PROMPT)

    async def _get_reply(
        self, prompt: str, image_url: Optional[str], api_key: str, base_url: str, model: str
    ) -> ChatCompletion:
        client = AsyncOpenAI(api_key=api_key, base_url=base_url)

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_url:
            content.append({
                "type": "image_url",
                "image_url": {"url": f"{image_url}", "detail": "high"},
            })

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": content},
            ],
        )
        return await completion

    async def get_xai_reply(self, prompt: str, image_url: Optional[str] = None) -> ChatCompletion:
        model = "grok-beta"
        if image_url:
            model = "grok-vision-beta"
        return await self._get_reply(
            prompt=prompt,
            image_url=image_url,
            api_key=self.xai_api_key,
            base_url="https://api.x.ai/v1",
            model=model,
        )

    async def get_oai_reply(self, prompt: str, image_url: Optional[str] = None) -> ChatCompletion:
        return await self._get_reply(
            prompt=prompt,
            image_url=image_url,
            api_key=self.openai_api_key,
            base_url="https://api.openai.com/v1",
            model="gpt-4o-mini",
        )

    async def get_gai_reply(self, prompt: str, image_url: Optional[str] = None) -> ChatCompletion:
        return await self._get_reply(
            prompt=prompt,
            image_url=image_url,
            api_key=self.googleai_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            model="gemini-1.5-pro",
        )

    async def get_xai_reply_stream(
        self, prompt: str, image_url: Optional[str] = None
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        client = OpenAI(api_key=self.xai_api_key, base_url="https://api.x.ai/v1")

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": f"{image_url}"}})

        completion = client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": content},
            ],
            stream=True,
        )
        for chunk in completion:
            if len(chunk.choices) > 0:
                yield chunk

    async def get_oai_reply_stream(
        self, prompt: str, image_url: Optional[str] = None
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        client = OpenAI(api_key=self.openai_api_key, base_url="https://api.openai.com/v1")

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": f"{image_url}"}})

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": content},
            ],
            stream=True,
        )
        for chunk in completion:
            if len(chunk.choices) > 0:
                yield chunk

    async def get_gai_reply_stream(
        self, prompt: str, image_url: Optional[str] = None
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        client = OpenAI(
            api_key=self.googleai_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image_url:
            content.append({"type": "image_url", "image_url": {"url": f"{image_url}"}})

        completion = client.chat.completions.create(
            model="gemini-1.5-pro",
            n=1,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": content},
            ],
            stream=True,
        )
        for chunk in completion:
            if len(chunk.choices) > 0:
                yield chunk


if __name__ == "__main__":
    import asyncio

    from rich.console import Console

    console = Console()

    async def main() -> None:
        llm_services = LLMServices()
        prompt = "既然從地球發射火箭那麼困難, 為何我們不直接在太空中建造火箭呢?"
        response = await llm_services.get_xai_reply(prompt=prompt)
        console.print(response.choices[0].message.content)

    async def main_stream() -> None:
        llm_services = LLMServices()
        prompt = "既然從地球發射火箭那麼困難, 為何我們不直接在太空中建造火箭呢?"
        async for res in llm_services.get_xai_reply_stream(prompt=prompt):
            console.print(res.choices[0].delta.content)

    asyncio.run(main_stream())
