import discord
from discord.ext import commands


class TemplateCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        # 忽略來自機器人的訊息
        if message.author.bot:
            return

        # 如果訊息內容是 "debug"，對該訊息按讚
        if message.content.lower() == "debug":
            await message.add_reaction("🤬")

        # # 繼續處理其他命令
        # await self.bot.process_commands(message)

    @commands.command()
    async def ping(self, ctx: commands.Context) -> None:
        await ctx.send("Pong!")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TemplateCogs(bot))
