from io import BytesIO
import os
import asyncio
import datetime

from PIL import Image
import anyio
import httpx
import discord
import logfire
from discord.ext import commands
from rich.console import Console

logfire.configure()

console = Console()

# 設定你的 Hugging Face API Token
API_URL = "https://api-inference.huggingface.co/models/strangerzonehf/Flux-Animex-v2-LoRA"
API_TOKEN = "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"  # noqa: S105
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

# 啟用所有 Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)


# 非同步查詢 Hugging Face API 的功能
async def query(payload: dict) -> bytes:
    async with httpx.AsyncClient() as client:
        response = await client.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        if response.status_code != 200:
            raise Exception(f"Failed to generate image: {response.status_code} {response.text}")
        return response.content


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
    # 回應使用者，開始生成圖片
    msg = await ctx.send("圖片正在生成中...\n進度: [----------] 0%")
    total_steps = 5  # 模擬的進度階段數

    # 模擬進度條更新
    for i in range(1, total_steps + 1):
        await asyncio.sleep(1)  # 每秒更新一次
        await update_progress(msg, i, total_steps)

    # 請求 Hugging Face API 生成圖片
    try:
        image_bytes = await query({"inputs": prompt})
        image = Image.open(BytesIO(image_bytes))

        # 將圖片存為暫時檔案並發送
        with BytesIO() as image_binary:
            image.save(image_binary, format="PNG")
            image_binary.seek(0)
            await msg.edit(content=f"圖片生成完成\nPrompt: `{prompt}`")
            await ctx.send(file=discord.File(fp=image_binary, filename="generated_image.png"))
    except Exception as e:
        await msg.edit(content=f"圖片生成失敗\n錯誤: {e!s}")


if __name__ == "__main__":
    # 啟動機器人 (記得替換為你的 Discord Bot Token)
    bot.run(
        token="MTEzNDkwNDk5NjE3ODE4MjIyNQ.GELWUx.9MJ4mY4OSo9Ty9U0WV9mwVypWIvTuTAIVyp-bs",  # noqa: S106
        log_handler=logfire.LogfireLoggingHandler(),
    )
