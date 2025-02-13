import discord
from discord import app_commands
from discord.ext import commands

from src.sdk.llm import LLMServices
from src.types.config import Config


class ImageGeneratorCogs(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.config = Config()
        self.llm_services = LLMServices()

    @app_commands.command(
        name="graph",
        description="This command will generate an image based on the prompt given.",
        nsfw=False,
    )
    async def graph(self, interaction: discord.Interaction, *, prompt: str) -> None:
        await interaction.response.send_message(content="正在生成圖片...")
        try:
            response = await self.llm_services.get_dalle_image(prompt=prompt)
            await interaction.response.edit_message(
                content=f"{interaction.message.author.mention}\n{response.data[0].url}"
            )
        except Exception as e:
            await interaction.response.edit_message(content=f"生成圖片時發生錯誤: {e!s}")


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageGeneratorCogs(bot))
