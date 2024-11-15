from io import BytesIO
import os
import asyncio
import datetime

from PIL import Image
import anyio
import discord
import logfire
from discord.ext import commands
from src.sdk.llm import LLMServices
from rich.console import Console
from src.sdk.image import ImageGenerator
from src.types.config import Config

logfire.configure()

config = Config()
llm_services = LLMServices()
image_services = ImageGenerator()
console = Console()

# 啟用所有 Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# 進度條
async def update_progress(message: discord.Message, step: int, total_steps: int) -> None:
    progress = int((step / total_steps) * 100)
    progress_bar = f"進度: [{'█' * (progress // 10)}{'-' * (10 - progress // 10)}] {progress}%"
    await message.edit(content=f"圖片正在生成中...\n{progress_bar}")


async def log_message_to_file(message: discord.Message, save_dir: str) -> None:
    """將訊息記錄到檔案，包含附件和貼圖下載"""
    # 確保資料夾存在
    os.makedirs(save_dir, exist_ok=True)

    # 建立日誌檔案名稱
    log_file = os.path.join(save_dir, "log.txt")

    # 記錄訊息內容
    channel_info = f"{message.channel.name} ({message.channel.id})"
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
        channel_name=message.channel.name,
        channel_id=message.channel.id,
        message_content=message.content,
    )

    # 處理附件
    for attachment in message.attachments:
        attachment_path = os.path.join(save_dir, attachment.filename)
        await attachment.save(attachment_path)

    # 處理貼圖
    if message.stickers:
        for sticker in message.stickers:
            sticker_path = os.path.join(save_dir, f"sticker_{sticker.id}.png")
            await sticker.save(sticker_path)


@bot.event
async def on_ready() -> None:
    console.print(f"Logged in as {bot.user}")
    # 取得應用程式的 client_id 並生成邀請連結
    app_info = await bot.application_info()
    invite_url = (
        f"https://discord.com/oauth2/authorize?client_id={app_info.id}&permissions=8&scope=bot"
    )
    console.print(f"邀請連結: {invite_url}")


@bot.event
async def on_message(message: discord.Message) -> None:
    # 忽略機器人自己的訊息
    if message.author.bot:
        return

    # 生成保存路徑（依據日期）
    today = datetime.date.today().isoformat()
    save_dir = os.path.join("logs", today, f"{message.channel.name}_{message.channel.id}")

    # 記錄訊息
    await log_message_to_file(message, save_dir)

    # 繼續處理其他命令
    await bot.process_commands(message)


@bot.command()
async def gen(ctx: commands.Context, *, prompt: str) -> None:
    """生成圖片並標記發送訊息的人。"""
    # 回應使用者，開始生成圖片
    msg = await ctx.send(f"{ctx.author.mention} 圖片正在生成中...\n進度: [----------] 0%")
    total_steps = 5  # 模擬的進度階段數

    # 模擬進度條更新
    for i in range(1, total_steps + 1):
        await asyncio.sleep(1)  # 每秒更新一次
        await update_progress(msg, i, total_steps)

    # 請求 Hugging Face API 生成圖片
    try:
        image_bytes = await image_services.gen_image(prompt=prompt)
        bytes_io = BytesIO(image_bytes)
        image = Image.open(bytes_io)

        # 將圖片存為暫時檔案並發送
        with BytesIO() as image_binary:
            image.save(image_binary, format="PNG")
            image_binary.seek(0)

            # 編輯完成訊息並發送圖片
            await msg.edit(content=f"{ctx.author.mention} 圖片生成完成\nPrompt: `{prompt}`")
            await ctx.send(file=discord.File(fp=image_binary, filename="generated_image.png"))
    except Exception as e:
        await msg.edit(content=f"{ctx.author.mention} 圖片生成失敗\n錯誤: {e!s}")


@bot.command()
async def xai(ctx: commands.Context, *, prompt: str) -> None:
    response = llm_services.get_xai_reply(prompt=prompt)
    await ctx.send(f"{response.choices[0].message}")


@bot.command()
async def oai(ctx: commands.Context, *, prompt: str) -> None:
    response = llm_services.get_oai_reply(prompt=prompt)
    await ctx.send(f"{response.choices[0].message}")


@bot.command()
async def gai(ctx: commands.Context, *, prompt: str) -> None:
    response = llm_services.get_gai_reply(prompt=prompt)
    await ctx.send(f"{response.choices[0].message}")


if __name__ == "__main__":
    bot.run(token=config.discord_bot_token, log_handler=logfire.LogfireLoggingHandler())
