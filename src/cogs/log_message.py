from pathlib import Path
import datetime

import anyio
import discord
import logfire
from discord.ext import commands


class LogMessageCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # 忽略機器人自己的訊息
        if message.author.bot:
            return

        # 記錄訊息
        """將訊息記錄到檔案，包含附件和貼圖下載"""
        # 生成保存路徑（依據日期）
        today = datetime.date.today().isoformat()

        if isinstance(message.channel, discord.DMChannel):
            # 如果是私訊，使用用戶 ID 作為名稱
            channel_name = f"DM_{message.author.id}"
        else:
            # 如果是伺服器中的頻道，使用頻道名稱
            channel_name = f"{message.channel.name}_{message.channel.id}"

        save_dir = Path("logs") / today / channel_name

        # 確保資料夾存在
        save_dir.mkdir(parents=True, exist_ok=True)

        # 建立日誌檔案名稱
        log_file = save_dir / "log.txt"

        # 判斷是私訊還是伺服器頻道
        if isinstance(message.channel, discord.DMChannel):
            channel_info = f"DM_{message.author.id}"
        else:
            channel_info = f"{message.channel.name} ({message.channel.id})"

        # 記錄訊息內容
        message_info = f"{message.author} ({message.author.id}) at {message.created_at.strftime('%Y-%m-%d %H:%M:%S')} in {channel_info}:\n"
        message_content = f"{message.content}\n"
        log_entry = f"{message_info}{message_content}{'-' * 40}\n"

        # 使用 anyio 非同步寫入
        async with await anyio.open_file(log_file, mode="a", encoding="utf-8") as f:
            await f.write(log_entry)

        logfire.info(
            f"{message.author.name}: {message.content}",
            author_id=message.author.id,
            created_time=message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            channel_name=getattr(message.channel, "name", "DM"),
            channel_id=message.channel.id,
        )

        # 處理附件
        for attachment in message.attachments:
            attachment_path = save_dir / attachment.filename
            await attachment.save(attachment_path)

        # 處理貼圖
        if message.stickers:
            for sticker in message.stickers:
                sticker_path = save_dir / f"sticker_{sticker.id}.png"
                await sticker.save(sticker_path)

        # # 繼續處理其他命令
        # await self.bot.process_commands(message)


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LogMessageCogs(bot))
