import pytest
from src.sdk.llm import LLMServices
from openai.types.images_response import ImagesResponse
from openai.types.chat.chat_completion import ChatCompletion

prompt = "既然從地球發射火箭那麼困難, 為何我們不直接在太空中建造火箭呢?"


@pytest.fixture
def llm_services() -> LLMServices:
    return LLMServices()


@pytest.mark.asyncio
async def test_get_oai_reply(llm_services: LLMServices) -> None:
    response = await llm_services.get_oai_reply(prompt=prompt)
    assert isinstance(response, ChatCompletion)


@pytest.mark.asyncio
async def test_get_dalle_image(llm_services: LLMServices) -> None:
    response = await llm_services.get_dalle_image(prompt=prompt)
    assert isinstance(response, ImagesResponse)
