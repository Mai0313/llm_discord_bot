import os

import nextcord
from nextcord import Interaction
from nextcord.ext import commands

# from autogen.agents import WebSurferAgent
from src.sdk.llm import LLMServices

os.environ["ANONYMIZED_TELEMETRY"] = "false"


class WebSearchCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.llm_services = LLMServices()

    @nextcord.slash_command(
        name="search",
        description="This command will search the web based on the prompt given.",
        dm_permission=True,
        nsfw=False,
    )
    async def search(self, interaction: Interaction, *, prompt: str) -> None:
        try:
            response = await self.llm_services.get_search_result(prompt=prompt)
            await interaction.response.send_message(content=response.choices[0].message.content)
        except Exception as e:
            await interaction.response.send_message(content=f"搜尋時發生錯誤: {e!s}")

    # @nextcord.slash_command(
    #     name="web",
    #     description="This command will search the web based on the prompt given.",
    #     dm_permission=True,
    #     nsfw=False,
    # )
    # async def web(self, interaction: Interaction, *, prompt: str) -> None:
    #     web_researcher = WebSurferAgent(
    #         name="researcher",
    #         llm_config={"model": "gpt-4o-mini"},
    #         human_input_mode="NEVER",
    #         web_tool="browser_use",
    #         web_tool_kwargs={
    #             "browser_config": {"headless": True},
    #             "agent_kwargs": {"generate_gif": True},
    #         },
    #     )
    #     ag2_news_result = web_researcher.run(
    #         message=prompt, tools=web_researcher.tools, user_input=False
    #     )
    #     await interaction.response.send_message(content=ag2_news_result.summary)


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    bot.add_cog(WebSearchCogs(bot), override=True)
