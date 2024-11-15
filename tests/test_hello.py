import pytest
from src.template.hello import hello_fn, a_hello_fn


def test_hello():
    hello = hello_fn()
    assert hello.name == "Wei"
    assert hello.content == "Hello, World!"


@pytest.mark.asyncio
async def test_a_hello():
    hello = await a_hello_fn()
    assert hello.name == "Wei"
    assert hello.content == "Hello, World!"
