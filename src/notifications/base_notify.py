# ABC for notification classes


import logfire
from pydantic import Field
from pydantic_settings import BaseSettings


class BaseNotify(BaseSettings):
    title: str = Field(
        ...,
        title="Title",
        description="The title of the notification message.",
        frozen=True,
        deprecated=False,
    )
    content: str = Field(
        default="",
        title="Content",
        description="The content of the notification message.",
        frozen=True,
        deprecated=False,
    )
    description: str = Field(
        ...,
        title="Description",
        description="The description of the notification message.",
        frozen=True,
        deprecated=False,
    )

    async def _send_notify(self) -> None:
        pass

    async def send_notify(self) -> None:
        try:
            await self._send_notify()
        except Exception:
            logfire.error("Failed to send Discord notification.")
