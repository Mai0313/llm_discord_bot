import wave

import nextcord
from nextcord.ext import commands
import nextcord.opus


class AudioRecorder(nextcord.VoiceClient):
    def __init__(self, client: nextcord.client, channel: nextcord.VoiceChannel):
        super().__init__(client, channel)
        self.recording = False
        self.audio_data: list[bytes] = []

    def recv_voice_data(self, data: bytes) -> None:
        if self.recording:
            self.audio_data.append(data)

    async def start_recording(self) -> None:
        self.recording = True

    async def stop_recording(self) -> str:
        self.recording = False

        # 儲存音訊
        filename = "recorded_audio.wav"
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(2)
            wf.setsampwidth(2)
            wf.setframerate(48000)
            wf.writeframes(b"".join(self.audio_data))

        return filename


class RecordCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_client = None

    @nextcord.slash_command(
        name="join",
        description="讓機器人加入語音頻道（可選填頻道 ID）",
        dm_permission=True,
        nsfw=False,
    )
    async def join(self, interaction: nextcord.Interaction, channel_id: int | None = None) -> None:
        """讓機器人加入語音頻道, 頻道 ID 可選填"""
        # 確保機器人未在語音頻道中
        if self.voice_client and self.voice_client.is_connected():
            await interaction.response.send_message("機器人已在語音頻道內!", ephemeral=True)
            return

        channel = None
        if channel_id:
            # 根據 ID 取得頻道
            channel = interaction.guild.get_channel(channel_id)
            if not channel or not isinstance(channel, nextcord.VoiceChannel):
                await interaction.response.send_message(
                    "無效的頻道 ID, 請輸入有效的語音頻道 ID!", ephemeral=True
                )
                return
        else:
            # 如果沒有提供 ID, 使用者必須在語音頻道內
            if interaction.user.voice and interaction.user.voice.channel:
                channel = interaction.user.voice.channel
            else:
                await interaction.response.send_message(
                    "你需要在語音頻道內, 或提供一個頻道 ID!", ephemeral=True
                )
                return

        # 連接語音頻道
        self.voice_client = await channel.connect(cls=AudioRecorder)
        await interaction.response.send_message(f"已加入語音頻道: {channel.name}")

    @nextcord.slash_command(name="record", description="開始錄音", dm_permission=True, nsfw=False)
    async def record(self, interaction: nextcord.Interaction) -> None:
        """開始錄音"""
        if self.voice_client and isinstance(self.voice_client, AudioRecorder):
            await self.voice_client.start_recording()
            await interaction.response.send_message("開始錄音!")
        else:
            await interaction.response.send_message("機器人未在語音頻道內!", ephemeral=True)

    @nextcord.slash_command(
        name="stop", description="停止錄音並儲存", dm_permission=True, nsfw=False
    )
    async def stop(self, interaction: nextcord.Interaction) -> None:
        """停止錄音並儲存檔案"""
        if self.voice_client and isinstance(self.voice_client, AudioRecorder):
            filename = await self.voice_client.stop_recording()
            await interaction.response.send_message(f"錄音完成, 儲存為 `{filename}`")
        else:
            await interaction.response.send_message("沒有正在錄音的會話!", ephemeral=True)

    @nextcord.slash_command(
        name="leave", description="讓機器人離開語音頻道", dm_permission=True, nsfw=False
    )
    async def leave(self, interaction: nextcord.Interaction) -> None:
        """讓機器人離開語音頻道"""
        if self.voice_client:
            await self.voice_client.disconnect()
            self.voice_client = None
            await interaction.response.send_message("已離開語音頻道")
        else:
            await interaction.response.send_message("機器人不在語音頻道內!", ephemeral=True)


# 註冊 Cog
async def setup(bot: commands.Bot) -> None:
    bot.add_cog(RecordCog(bot), override=True)
