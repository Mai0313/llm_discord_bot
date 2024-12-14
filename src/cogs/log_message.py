from pathlib import Path
import datetime

import pandas as pd
import discord
import logfire
from sqlalchemy import create_engine
from discord.ext import commands

from src.types.database import DatabaseConfig


class LogMessageCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        database = DatabaseConfig()
        self.engine = create_engine(database.postgres.postgres_dsn, echo=True)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # 忽略機器人自己的訊息
        if message.author.bot:
            return

        # 記錄訊息
        """將訊息記錄到檔案，包含附件和貼圖下載"""
        # 生成保存路徑（依據日期）
        today = datetime.date.today().isoformat()

        # 判斷是私訊還是伺服器頻道
        if isinstance(message.channel, discord.DMChannel):
            # 如果是私訊，使用用戶 ID 作為名稱
            channel_name = f"DM_{message.author.id}"
        else:
            # 如果是伺服器中的頻道，使用頻道名稱
            channel_name = f"{message.channel.name}_{message.channel.id}"

        save_dir = Path("data") / today / channel_name

        # 確保資料夾存在
        save_dir.mkdir(parents=True, exist_ok=True)

        logfire.info(
            f"{message.author.name}: {message.content}",
            author=message.author.name,
            created_time=message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            channel_name=getattr(message.channel, "name", "DM"),
            channel_id=message.channel.id,
        )

        # 準備訊息資料作為 DataFrame
        # 包含附件和貼圖
        attachment_paths = []
        for attachment in message.attachments:
            attachment_path = save_dir / attachment.filename
            await attachment.save(attachment_path)
            attachment_paths.append(str(attachment_path))

        sticker_paths = []
        if message.stickers:
            for sticker in message.stickers:
                sticker_path = save_dir / f"sticker_{sticker.id}.png"
                try:
                    await sticker.save(sticker_path)
                    sticker_paths.append(str(sticker_path))
                except discord.NotFound:
                    logfire.warn("Sticker is not found", sticker_id=sticker.id)

        message_data = {
            "author": [message.author.name],
            "author_id": [message.author.id],
            "content": [message.content],
            "created_at": [message.created_at],
            "channel_name": [getattr(message.channel, "name", "DM")],
            "channel_id": [getattr(message.channel, "id", None)],
            "attachments": [";".join(attachment_paths) if attachment_paths else ""],
            "stickers": [";".join(sticker_paths) if sticker_paths else ""],
        }
        message_df = pd.DataFrame(message_data)

        # 統一寫入資料庫
        await self.__write2postgres(message_df)

        # # 繼續處理其他命令
        # await self.bot.process_commands(message)

    async def __write2postgres(self, message_df: pd.DataFrame) -> None:
        try:
            message_df.to_sql(
                name="llmbot_message", con=self.engine, if_exists="append", index=False
            )
        except Exception as e:
            logfire.error("Error writing to database", error=str(e))


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LogMessageCogs(bot))
