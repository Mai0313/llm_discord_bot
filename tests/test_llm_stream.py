import pytest
from src.sdk.llm import LLMServices
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

llm_services = LLMServices()
prompt = "既然從地球發射火箭那麼困難, 為何我們不直接在太空中建造火箭呢?"


@pytest.mark.asyncio
async def test_get_oai_reply_stream() -> None:
    llm_services = LLMServices()
    async for res in llm_services.get_oai_reply_stream(prompt=prompt):
        assert isinstance(res, ChatCompletionChunk)


@pytest.mark.asyncio
async def test_get_xai_reply_stream() -> None:
    llm_services = LLMServices()
    async for res in llm_services.get_xai_reply_stream(prompt=prompt):
        assert isinstance(res, ChatCompletionChunk)


@pytest.mark.skip(reason="Not implemented")
@pytest.mark.asyncio
async def test_get_gai_reply_stream() -> None:
    llm_services = LLMServices()
    async for res in llm_services.get_gai_reply_stream(prompt=prompt):
        assert isinstance(res, ChatCompletionChunk)
