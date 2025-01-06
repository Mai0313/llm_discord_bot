from discord.ext import commands

from src.sdk.llm import LLMServices


class ReplyGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices()

    @commands.command()
    async def oai(self, ctx: commands.Context, *, prompt: str) -> None:
        image_urls = None
        if ctx.message.attachments:
            # 取得附件的 URL
            image_urls = [attachment.url for attachment in ctx.message.attachments]
        response = await self.llm_services.get_oai_reply(prompt=prompt, image_urls=image_urls)

        await ctx.send(f"{ctx.author.mention} {response.choices[0].message.content}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReplyGeneratorCogs(bot))
