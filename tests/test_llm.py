import pytest
from src.sdk.llm import LLMServices
from openai.types.chat.chat_completion import ChatCompletion

llm_services = LLMServices()
prompt = "既然從地球發射火箭那麼困難, 為何我們不直接在太空中建造火箭呢?"


@pytest.mark.asyncio
async def test_get_oai_reply() -> None:
    llm_services = LLMServices()
    response = await llm_services.get_oai_reply(prompt=prompt)
    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio
async def test_get_xai_reply() -> None:
    llm_services = LLMServices()
    response = await llm_services.get_xai_reply(prompt=prompt)
    assert isinstance(response, ChatCompletion)


@pytest.mark.skip(reason="Not implemented")
@pytest.mark.asyncio
async def test_get_gai_reply() -> None:
    llm_services = LLMServices()
    response = await llm_services.get_gai_reply(prompt=prompt)
    assert isinstance(response, ChatCompletion)
