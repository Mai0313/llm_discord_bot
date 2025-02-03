from discord.ext import commands

from src.sdk.llm import LLMServices


class WebSearchCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices()

    @commands.command()
    async def search(self, ctx: commands.Context, *, prompt: str) -> None:
        try:
            response = await self.llm_services.get_search_result(prompt=prompt)
            await ctx.send(content=response.choices[0].message.content)
        except Exception as e:
            await ctx.send(content=f"搜尋時發生錯誤: {e!s}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WebSearchCogs(bot))
