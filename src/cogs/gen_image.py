from io import BytesIO
import asyncio

from PIL import Image
import httpx
import discord
from discord.ext import commands

from src.types.config import Config


class ImageGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()

    async def gen_image(self, prompt: str) -> bytes:
        async with httpx.AsyncClient(
            base_url="https://api-inference.huggingface.co/models"
        ) as client:
            response = await client.post(
                url="/strangerzonehf/Flux-Animex-v2-LoRA",
                headers={"Authorization": f"Bearer {self.config.huggingface_api_token}"},
                json={"inputs": prompt},
                timeout=60,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to generate image: {response.status_code} {response.text}"
                )
            return response.content

    @commands.command()
    async def gen(self, ctx: commands.Context, *, prompt: str) -> None:
        """生成圖片並標記發送訊息的人。"""
        msg = await ctx.send(f"{ctx.author.mention} 圖片正在生成中...\n進度: [----------] 0%")
        total_steps = 5  # 模擬的進度階段數

        # 模擬進度條更新
        for step in range(1, total_steps + 1):
            progress = int((step / total_steps) * 100)
            progress_bar = (
                f"進度: [{'█' * (progress // 10)}{'-' * (10 - progress // 10)}] {progress}%"
            )
            await msg.edit(content=f"圖片正在生成中...\n{progress_bar}")
            await asyncio.sleep(5)  # 每5秒更新一次

        # 請求 Hugging Face API 生成圖片
        try:
            image_bytes = await self.gen_image(prompt=prompt)
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


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageGeneratorCogs(bot))
