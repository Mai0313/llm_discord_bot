import os
import logging
from pathlib import Path
import secrets
import platform

import logfire

logfire.configure(send_to_logfire=False, scrubbing=False)

from logfire import LogfireLoggingHandler
import nextcord
from nextcord.ext import tasks, commands
from src.types.config import Config
from src.sdk.log_message import MessageLogger

logging.getLogger("sqlalchemy.engine.Engine").disabled = True


class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or("!"),
            intents=nextcord.Intents.all(),  # 啟用所有 Intents
            help_command=None,
            description="A Discord bot made with Nextcord.",
        )
        self.config = Config()
        self.logger = logging.getLogger("nextcord.state")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(LogfireLoggingHandler())

    async def on_connect(self) -> None:
        logfire.info("Bot Connected", bot_name=self.user.name, bot_id=self.user.id)

    async def on_ready(self) -> None:
        app_info = await self.application_info()
        await self.setup_hook()
        invite_url = (
            f"https://discord.com/oauth2/authorize?client_id={app_info.id}&permissions=8&scope=bot"
        )

        logfire.info("Bot Started", bot_name=self.user.name, bot_id=self.user.id)
        logfire.info(f"Invite Link: {invite_url}")

    async def on_guild_available(self, guild: nextcord.Guild) -> None:
        return await super().on_guild_available(guild)

    async def load_cogs(self) -> None:
        cog_path = Path("./src/cogs")
        cog_files = [
            f"src.cogs.{f.stem}" for f in cog_path.glob("*.py") if not f.stem.startswith("__")
        ]
        self.load_extensions(cog_files, stop_at_error=True)
        # for cog_file in cog_files:
        #     filename = f"src.cogs.{cog_file}"
        #     self.load_extension(filename)
        logfire.info("Cogs Loaded", cog_files=", ".join(cog_files))

    @tasks.loop(minutes=1.0)
    async def status_task(self) -> None:
        """Setup the game status task of the bot."""
        statuses = ["your mama"]
        random_status = secrets.choice(statuses)
        await self.change_presence(activity=nextcord.Game(random_status))
        logfire.info("Status Changed", new_status=self.activity.name)

    @status_task.before_loop
    async def before_status_task(self) -> None:
        """Before starting the status changing task, we make sure the bot is ready"""
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        """This will just be executed when the bot starts the first time."""
        logfire.info(
            "Logged in",
            bot_name=self.user.name,
            discord_version=nextcord.__version__,
            python_version=platform.python_version(),
            system=f"{platform.system()} {platform.release()} ({os.name})",
        )
        await self.load_cogs()
        guild_id = None
        if self.config.discord_test_server_id:
            guild_id = self.get_guild(self.config.discord_test_server_id)
        # await self.tree.sync(guild=guild)
        await self.sync_application_commands(guild_id=guild_id)
        self.status_task.start()

    async def on_message(self, message: nextcord.Message) -> None:
        """The code in this event is executed every time someone sends a message, with or without the prefix

        :param message: The message that was sent.
        """
        if message.author == self.user or message.author.bot:
            return
        await MessageLogger(message=message).log()
        await self.process_commands(message)

    async def on_command_completion(self, context: commands.Context) -> None:
        """The code in this event is executed every time a normal command has been *successfully* executed.

        :param context: The context of the command that has been executed.
        """
        await MessageLogger(message=context.message).log()
        full_command_name = context.command.qualified_name
        split = full_command_name.split(" ")
        executed_command = str(split[0])
        logfire.info("Command Received", command=executed_command)
        if context.guild is not None:
            logfire.info(
                f"Executed {executed_command} command in {context.guild.name} (ID: {context.guild.id}) by {context.author} (ID: {context.author.id})"
            )
        else:
            logfire.info(
                f"Executed {executed_command} command by {context.author} (ID: {context.author.id}) in DMs"
            )

    async def on_command_error(
        self,
        context: commands.Context,
        error: commands.CommandOnCooldown
        | commands.NotOwner
        | commands.MissingPermissions
        | commands.BotMissingPermissions
        | commands.MissingRequiredArgument,
    ) -> None:
        """The code in this event is executed every time a normal valid command catches an error.

        :param context: The context of the normal command that failed executing.
        :param error: The error that has been faced.
        """
        if isinstance(error, commands.CommandOnCooldown):
            minutes, seconds = divmod(error.retry_after, 60)
            hours, minutes = divmod(minutes, 60)
            hours = hours % 24
            embed = nextcord.Embed(
                description=f"**Please slow down** - You can use this command again in {f'{round(hours)} hours' if round(hours) > 0 else ''} {f'{round(minutes)} minutes' if round(minutes) > 0 else ''} {f'{round(seconds)} seconds' if round(seconds) > 0 else ''}.",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.NotOwner):
            embed = nextcord.Embed(description="You are not the owner of the bot!", color=0xE02B2B)
            await context.send(embed=embed)
            if context.guild:
                logfire.warn(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the guild {context.guild.name} (ID: {context.guild.id}), but the user is not an owner of the bot."
                )
            else:
                logfire.warn(
                    f"{context.author} (ID: {context.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
                )
        elif isinstance(error, commands.MissingPermissions):
            embed = nextcord.Embed(
                description="You are missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to execute this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.BotMissingPermissions):
            embed = nextcord.Embed(
                description="I am missing the permission(s) `"
                + ", ".join(error.missing_permissions)
                + "` to fully perform this command!",
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = nextcord.Embed(
                title="Error!",
                # We need to capitalize because the command arguments have no capital letter in the code and they are the first word in the error message.
                description=str(error).capitalize(),
                color=0xE02B2B,
            )
            await context.send(embed=embed)
        else:
            raise error


if __name__ == "__main__":
    config = Config()
    bot = DiscordBot()
    bot.run(token=config.discord_bot_token)
