import logfire
from pydantic import Field
from pydantic_settings import BaseSettings

logfire.configure()


class Config(BaseSettings):
    openai_api_key: str = Field(
        ...,
        description="The api key from openai for calling models.",
        examples=["sk-proj-..."],
        alias="OPENAI_API_KEY",
        frozen=False,
        deprecated=False,
    )
    pplx_api_key: str = Field(
        ...,
        description="The api key from perplexity for calling models.",
        examples=["pplx-..."],
        alias="PERPLEXITY_API_KEY",
        frozen=False,
        deprecated=False,
    )
    bing_api_key: str = Field(
        ...,
        description="The api key from bing for calling models.",
        examples=["a9d67..."],
        alias="BING_API_KEY",
        frozen=False,
        deprecated=False,
    )
    huggingface_api_token: str = Field(
        ...,
        description="The api token from huggingface for calling models.",
        examples=["hf_zdZ..."],
        alias="HUGGINGFACE_API_TOKEN",
        frozen=False,
        deprecated=False,
    )
    discord_bot_token: str = Field(
        ...,
        description="The token from discord for calling models.",
        examples=["MTEz-..."],
        alias="DISCORD_BOT_TOKEN",
        frozen=False,
        deprecated=False,
    )
