import os

import discord
from discord import app_commands
from discord.ext import commands
from autogen.agents import WebSurferAgent

from src.sdk.llm import LLMServices

os.environ["ANONYMIZED_TELEMETRY"] = "false"


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

    @app_commands.command(
        name="search",
        description="This command will search the web based on the prompt given.",
        nsfw=False,
    )
    async def search_slash(self, interaction: discord.Interaction, *, prompt: str) -> None:
        try:
            response = await self.llm_services.get_search_result(prompt=prompt)
            await interaction.response.send_message(content=response.choices[0].message.content)
        except Exception as e:
            await interaction.response.send_message(content=f"搜尋時發生錯誤: {e!s}")

    @commands.command()
    async def web(self, ctx: commands.Context, *, prompt: str) -> None:
        web_researcher = WebSurferAgent(
            name="researcher",
            llm_config={"model": "gpt-4o-mini"},
            human_input_mode="NEVER",
            web_tool="browser_use",
            web_tool_kwargs={
                "browser_config": {"headless": True},
                "agent_kwargs": {"generate_gif": True},
            },
        )
        ag2_news_result = web_researcher.run(
            message=prompt, tools=web_researcher.tools, user_input=False
        )
        ctx.send(content=ag2_news_result.summary)

    @app_commands.command(
        name="web",
        description="This command will search the web based on the prompt given.",
        nsfw=False,
    )
    async def web_slash(self, interaction: discord.Interaction, *, prompt: str) -> None:
        web_researcher = WebSurferAgent(
            name="researcher",
            llm_config={"model": "gpt-4o-mini"},
            human_input_mode="NEVER",
            web_tool="browser_use",
            web_tool_kwargs={
                "browser_config": {"headless": True},
                "agent_kwargs": {"generate_gif": True},
            },
        )
        ag2_news_result = web_researcher.run(
            message=prompt, tools=web_researcher.tools, user_input=False
        )
        interaction.response.send_message(content=ag2_news_result.summary)


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WebSearchCogs(bot))
