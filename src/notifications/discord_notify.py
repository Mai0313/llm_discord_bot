import io
from typing import Optional
from pathlib import Path
import datetime

from PIL import Image
import httpx
import orjson
from pydantic import Field, ConfigDict

from src.notifications.base_notify import BaseNotify


class DiscordNotify(BaseNotify):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    avatar_url: str = Field(
        default="https://i.imgur.com/QoOwyXJ.png",
        title="Avatar URL",
        description="The URL of the avatar image.",
        frozen=False,
        deprecated=False,
    )
    target_image: Optional[Image.Image | str] = Field(
        default=None,
        title="Image Object",
        description="The image object to send.",
        frozen=False,
        deprecated=False,
    )
    discord_webhook_url: str = Field(
        ...,
        title="Discord Webhook URL",
        description="The URL of the Discord webhook to send notifications to.",
        frozen=False,
        deprecated=False,
    )

    async def _send_notify(self) -> None:
        timestamp = datetime.datetime.now().isoformat()  # ISO 8601 格式

        embed = {
            "author": {
                "name": "Notification Bot",
                "url": "https://mai0313.com",
                "icon_url": "https://i.imgur.com/fKL31aD.jpg",
            },
            "title": f"📢 {self.title}",
            "url": "https://mai0313.com",
            "description": self.description,
            "color": 14177041,
            "fields": [
                {"name": "更多資訊", "value": "[點擊這裡](https://mai0313.com)", "inline": True},
                {"name": "狀態更新", "value": "此通知為自動生成", "inline": True},
            ],
            "footer": {
                "text": f"時間: {timestamp}",
                "icon_url": "https://i.imgur.com/fKL31aD.jpg",
            },
            "timestamp": timestamp,
        }

        # 處理圖片
        files: dict[str, tuple[str, bytes | io.BytesIO, str]] = {}
        if isinstance(self.target_image, Image.Image):
            image_bytes = io.BytesIO()
            self.target_image.save(image_bytes, format=self.target_image.format or "PNG")
            image_bytes.seek(0)
            files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
            embed["image"] = {"url": "attachment://image.jpg"}
        elif isinstance(self.target_image, str):
            image_path = Path(self.target_image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            files = {"file": ("image.jpg", image_path.read_bytes(), "image/jpeg")}
            embed["image"] = {"url": "attachment://image.jpg"}

        payload = {"avatar_url": self.avatar_url, "content": self.content, "embeds": [embed]}

        # 發送請求到 Discord Webhook
        async with httpx.AsyncClient() as client:
            if files:
                response = await client.post(
                    url=self.discord_webhook_url,
                    data={"payload_json": orjson.dumps(payload).decode("utf-8")},
                    files=files,
                )
            else:
                response = await client.post(url=self.discord_webhook_url, json=payload)
            response.raise_for_status()  # 確保請求成功


if __name__ == "__main__":
    import asyncio

    notify = DiscordNotify(
        title="老大, 我已經幫您打完王朝了",
        content="",
        description="王朝已完成，將繼續為您採棉花。",
        target_image="./data/allstars/back.png",
        discord_webhook_url="...",
    )

    asyncio.run(notify.send_notify())
