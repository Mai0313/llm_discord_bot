import os
import asyncio
from datetime import datetime

import discord
from discord.ext import commands


class VoiceRecorder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_clients: dict[int, discord.VoiceClient] = {}
        self.recording_tasks = {}

    @commands.command()
    async def join(self, ctx: commands.Context) -> None:
        """讓機器人加入語音頻道"""
        if ctx.author.voice is None:
            await ctx.send("你需要先加入一個語音頻道！")
            return

        channel = ctx.author.voice.channel
        if ctx.guild.id in self.voice_clients:
            await ctx.send("機器人已經在語音頻道內！")
            return

        self.voice_clients[ctx.guild.id] = await channel.connect()
        await ctx.send(f"已加入語音頻道：{channel.name}")

    @commands.command()
    async def leave(self, ctx: commands.Context) -> None:
        """讓機器人離開語音頻道"""
        if ctx.guild.id in self.voice_clients:
            await self.voice_clients[ctx.guild.id].disconnect()
            del self.voice_clients[ctx.guild.id]
            await ctx.send("已離開語音頻道！")
        else:
            await ctx.send("機器人不在語音頻道內！")

    @commands.command()
    async def record(self, ctx: commands.Context) -> None:
        """開始錄音"""
        if ctx.guild.id not in self.voice_clients:
            await ctx.send("機器人尚未加入語音頻道！")
            return

        voice_client = self.voice_clients[ctx.guild.id]

        if voice_client.is_listening():
            await ctx.send("已經在錄音中！")
            return

        filename = f"recordings/{ctx.guild.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pcm"
        os.makedirs("recordings", exist_ok=True)

        audio_buffer = []

        class AudioRecorder(discord.AudioSink):
            def write(self, data) -> None:
                audio_buffer.append(data)

        audio_sink = AudioRecorder()
        voice_client.listen(audio_sink)

        async def recording_task() -> None:
            await ctx.send("開始錄音...")
            while voice_client.is_listening():
                await asyncio.sleep(1)

            with open(filename, "wb") as f:
                for chunk in audio_buffer:
                    f.write(chunk)

            await ctx.send(f"錄音完成，已儲存為 `{filename}`")

        self.recording_tasks[ctx.guild.id] = self.bot.loop.create_task(recording_task())

    @commands.command()
    async def stop(self, ctx: commands.Context) -> None:
        """停止錄音"""
        if ctx.guild.id not in self.voice_clients:
            await ctx.send("機器人不在語音頻道內！")
            return

        voice_client = self.voice_clients[ctx.guild.id]

        if not voice_client.is_listening():
            await ctx.send("目前沒有錄音進行中！")
            return

        voice_client.stop_listening()

        if ctx.guild.id in self.recording_tasks:
            self.recording_tasks[ctx.guild.id].cancel()
            del self.recording_tasks[ctx.guild.id]

        await ctx.send("錄音已停止！")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoiceRecorder(bot))
