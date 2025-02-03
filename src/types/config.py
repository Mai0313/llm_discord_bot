import logfire
from pydantic import Field
from pydantic_settings import BaseSettings

logfire.configure(send_to_logfire=False)


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
    discord_bot_token: str = Field(
        ...,
        description="The token from discord for calling models.",
        examples=["MTEz-..."],
        alias="DISCORD_BOT_TOKEN",
        frozen=False,
        deprecated=False,
    )
