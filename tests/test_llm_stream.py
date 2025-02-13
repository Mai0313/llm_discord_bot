import pytest
from src.sdk.llm import LLMServices
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk

prompt = "既然從地球發射火箭那麼困難, 為何我們不直接在太空中建造火箭呢?"


@pytest.fixture
def llm_services() -> LLMServices:
    return LLMServices()


@pytest.mark.asyncio
async def test_get_oai_reply_stream(llm_services: LLMServices) -> None:
    async for response in llm_services.get_oai_reply_stream(prompt=prompt):
        assert isinstance(response, ChatCompletionChunk)
