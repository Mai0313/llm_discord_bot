import nextcord
from nextcord import Interaction, SlashOption
from nextcord.ext import commands

from src.sdk.llm import LLMServices
from src.types.config import Config


class ImageGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.llm_services = LLMServices()

    @nextcord.slash_command(
        name="graph",
        description="This command will generate an image based on the prompt given.",
        dm_permission=True,
        nsfw=False,
    )
    async def graph(
        self, interaction: Interaction, prompt: str = SlashOption(description="Enter your prompt")
    ) -> None:
        await interaction.response.defer()
        await interaction.followup.send(content="正在生成圖片...")

        try:
            response = await self.llm_services.get_dalle_image(prompt=prompt)
            await interaction.followup.send(
                content=f"{interaction.user.mention}\n{response.data[0].url}"
            )
        except Exception as e:
            await interaction.followup.send(content=f"生成圖片時發生錯誤: {e!s}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    bot.add_cog(ImageGeneratorCogs(bot), override=True)
