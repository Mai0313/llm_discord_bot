from discord import app_commands
from discord.ext import commands

from src.sdk.llm import LLMServices

llm_services = LLMServices()


class ReplyGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="xai", description="Generate text based on the prompt.")
    async def xai(self, ctx: commands.Context, *, prompt: str = "") -> None:
        # 檢查是否有附件
        if ctx.message.attachments:
            # 取得附件的 URL（假設只有一個圖片）
            image_url = ctx.message.attachments[0].url
            # await ctx.send(f"收到圖片: {image_url}")
            # 在這裡你可以進一步處理圖片 URL，例如傳遞給 llm_services 或其他服務
            response = await llm_services.get_xai_reply(prompt=prompt, image=image_url)
        else:
            # 如果沒有圖片附件，僅處理文字提示
            response = await llm_services.get_xai_reply(prompt=prompt)

        # 回應處理結果
        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")

    @commands.command()
    async def oai(self, ctx: commands.Context, *, prompt: str) -> None:
        if ctx.message.attachments:
            # 取得附件的 URL（假設只有一個圖片）
            image_url = ctx.message.attachments[0].url
            # await ctx.send(f"收到圖片，URL 為: {image_url}")
            # 在這裡你可以進一步處理圖片 URL，例如傳遞給 llm_services 或其他服務
            response = await llm_services.get_oai_reply(prompt=prompt, image=image_url)
        else:
            # 如果沒有圖片附件，僅處理文字提示
            response = await llm_services.get_oai_reply(prompt=prompt)

        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")

    @commands.command()
    async def gai(self, ctx: commands.Context, *, prompt: str) -> None:
        if ctx.message.attachments:
            # 取得附件的 URL（假設只有一個圖片）
            image_url = ctx.message.attachments[0].url
            # await ctx.send(f"收到圖片，URL 為: {image_url}")
            # 在這裡你可以進一步處理圖片 URL，例如傳遞給 llm_services 或其他服務
            response = await llm_services.get_gai_reply(prompt=prompt, image=image_url)
        else:
            # 如果沒有圖片附件，僅處理文字提示
            response = await llm_services.get_gai_reply(prompt=prompt)
        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReplyGeneratorCogs(bot))
