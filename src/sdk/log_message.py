from pathlib import Path
import datetime

import pandas as pd
import logfire
import nextcord
from pydantic import Field, BaseModel, ConfigDict, computed_field
import sqlalchemy
from sqlalchemy import create_engine
from nextcord.message import Attachment, StickerItem

from src.types.database import DatabaseConfig


class MessageLogger(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    message: nextcord.Message
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    @computed_field
    @property
    def engine(self) -> sqlalchemy.Engine:
        engine = create_engine(self.database.postgres.postgres_dsn, echo=True)
        return engine

    async def log(self) -> None:
        """Log a message to a CSV file and save attachments and stickers to disk."""
        # 避免記錄到機器人自己的訊息
        if self.message.author.bot:
            return

        # 判斷頻道類型並獲取頻道名稱
        channel_name = await self._get_channel_name(self.message)

        # 產生今日資料夾，作為附件和貼圖的存放路徑
        today = datetime.date.today().isoformat()
        base_dir = Path("data") / today / channel_name

        # 保存附件與貼圖
        attachment_paths = await self._save_attachments(self.message.attachments, base_dir)
        sticker_paths = await self._save_stickers(self.message.stickers, base_dir)

        # 紀錄到 logfire
        logfire.info(
            f"{self.message.author.name}: {self.message.content}",
            author=self.message.author.name,
            created_time=self.message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            channel_name=channel_name,
            channel_id=getattr(self.message.channel, "id", None),
        )

        # 寫入 CSV（或改成寫入資料庫）
        await self._save_message_data(self.message, attachment_paths, sticker_paths)

    async def _get_channel_name(self, message: nextcord.Message) -> str:
        """Determine if the message is from a direct message (DM) or a server channel, and return the corresponding name.

        Args:
            message (discord.Message): The message object to check.

        Returns:
            str: The name of the channel or DM, formatted as "DM_<author_id>" for DMs or "<channel_name>_<channel_id>" for server channels.
        """
        if isinstance(message.channel, nextcord.DMChannel):
            return f"DM_{message.author.id}"
        return f"{message.channel.name}_{message.channel.id}"

    async def _save_attachments(self, attachments: list[Attachment], base_dir: Path) -> list[str]:
        """Save attachments to the specified directory and return a list of file paths.

        Args:
            attachments (list[Attachment]): A list of Attachment objects to be saved.
            base_dir (Path): The base directory where attachments will be saved.

        Returns:
            list[str]: A list of file paths where the attachments were saved.
        """
        saved_paths = []
        for attachment in attachments:
            filepath = base_dir / attachment.filename
            base_dir.mkdir(parents=True, exist_ok=True)
            await attachment.save(filepath)
            saved_paths.append(str(filepath))
        return saved_paths

    async def _save_stickers(self, stickers: list[StickerItem], base_dir: Path) -> list[str]:
        """Downloads and saves stickers to the specified directory, and returns a list of file paths.

        Args:
            stickers (list[StickerItem]): A list of StickerItem objects to be saved.
            base_dir (Path): The base directory where the stickers will be saved.

        Returns:
            list[str]: A list of file paths where the stickers were saved.

        Raises:
            discord.NotFound: If a sticker is not found.
        """
        saved_paths = []
        for sticker in stickers:
            filepath = base_dir / f"sticker_{sticker.id}.png"
            try:
                base_dir.mkdir(parents=True, exist_ok=True)
                await sticker.save(filepath)
                saved_paths.append(str(filepath))
            except nextcord.NotFound:
                logfire.warn("Sticker is not found", sticker_id=sticker.id)
        return saved_paths

    async def _save_message_data(
        self, message: nextcord.Message, attachment_paths: list[str], sticker_paths: list[str]
    ) -> None:
        """Saves message data to a CSV file.

        Args:
            message (discord.Message): The Discord message object containing the message details.
            attachment_paths (list[str]): A list of file paths for the message attachments.
            sticker_paths (list[str]): A list of file paths for the message stickers.

        Returns:
            None
        """
        message_data = {
            "author": [message.author.name],
            "author_id": [str(message.author.id)],
            "content": [message.content],
            "created_at": [message.created_at.isoformat()],
            "channel_name": [getattr(message.channel, "name", "DM")],
            "channel_id": [str(getattr(message.channel, "id", None))],
            "attachments": [";".join(attachment_paths)],
            "stickers": [";".join(sticker_paths)],
        }
        message_df = pd.DataFrame(message_data)
        message_df = message_df.astype(str)

        # 寫入 CSV (append 模式，不覆蓋既有資料)
        message_df.to_csv("./data/llmbot_message.csv", mode="a", header=False, index=False)

        # 或改用 to_sql 寫入資料庫：
        # df.to_sql("llmbot_message", con=self.engine, if_exists="append", index=False)

        # # 繼續處理其他命令
        # await self.bot.process_commands(message)
