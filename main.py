import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional, Union
import os
import aiohttp
from flask import Flask
from threading import Thread

# 🟢 Flask server
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def keep_alive():
    def run():
        port = int(os.environ.get("PORT", 8080))
        app.run(host='0.0.0.0', port=port)
    t = Thread(target=run)
    t.daemon = True
    t.start()

# 🟢 Discord bot setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # ✅ Bắt buộc để đọc nội dung tin nhắn

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name="hoa ở vườn hoa bách hợp"
    )
    await bot.change_presence(status=discord.Status.online, activity=activity)
    print(f'Bot đã đăng nhập dưới tên: {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Error syncing: {e}")

@bot.tree.command(name="say", description="Lily sẽ gửi nội dung hoặc ảnh (hoặc cả hai) vào kênh hoặc chủ đề được chọn")
@app_commands.describe(
    channel="Kênh văn bản hoặc chủ đề cần gửi tin",
    message="(Tùy chọn) Nội dung tin nhắn",
    image="(Tùy chọn) Ảnh đính kèm"
)
async def say(
    interaction: discord.Interaction,
    channel: Union[discord.TextChannel, discord.Thread],
    message: Optional[str] = None,
    image: Optional[discord.Attachment] = None
):
    guild = interaction.guild
    user = guild.get_member(interaction.user.id)
    bot_member = guild.me

    if user is None or bot_member is None:
        await interaction.response.send_message("Không thể xác định vai trò của ngài~", ephemeral=True)
        return

    if user.top_role <= bot_member.top_role:
        await interaction.response.send_message("Ngài phải mạnh hơn nữa để sai khiến Lily~", ephemeral=True)
        return

    if not message and not image:
        await interaction.response.send_message("Ngài cần nhập tin nhắn hoặc thả ảnh nữa~", ephemeral=True)
        return

    # ✅ Giữ tương tác sống
    await interaction.response.defer(ephemeral=True)

    try:
        if image:
            if image.size > 8 * 1024 * 1024:
                await interaction.followup.send("❌ Ảnh vượt quá giới hạn 8MB.", ephemeral=True)
                return

            if image.content_type and image.content_type.startswith("image/"):
                file = await image.to_file()
                await channel.send(content=message, file=file)
            else:
                await interaction.followup.send("❌ File không phải ảnh hợp lệ.", ephemeral=True)
                return
        else:
            await channel.send(content=message)

        await interaction.followup.send("✅Lily đã làm theo lời của ngài~!", ephemeral=True)

    except Exception as e:
        await interaction.followup.send(f"❌ Lỗi khi gửi: `{e}`", ephemeral=True)



@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name='hello-goodbye')
    role_channel = discord.utils.get(member.guild.text_channels, name='role')  # Tên kênh chọn role

    if channel:
        role_mention = role_channel.mention if role_channel else "`role`"

        embed = discord.Embed(
            title=f"👋 Chào mừng đồng môn **{member.display_name}** đã đặt chân vào lãnh địa!",
            description=(
                f"{member.mention} đã tham gia server **{member.guild.name}**!\n\n"
                "🌟 Nơi bạn có thể giao lưu với dàn nhân sự và fan của team, chắc vậy.\n\n"
                f"📌 **Nhớ sang kênh {role_mention} để chọn vai trò và có thể nhắn trong server nhé!**"
            ),
            color=0x00ffcc
        )

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)

        embed.set_image(url="https://get.wallhere.com/photo/anime-anime-girls-sky-clouds-school-uniform-Yuru-Yuri-Akaza-Akari-Yoshikawa-Chinatsu-Funami-Yui-Toshinou-Kyouko-cloud-screenshot-extreme-sport-250233.jpg")

        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = discord.utils.get(member.guild.text_channels, name='hello-goodbye')
    if channel:
        embed = discord.Embed(
            title="👋 Tạm biệt!",
            description=(
                f"💨 {member.name} đã rời khỏi **{member.guild.name}**...\n"
                "Mong có dịp gặp lại bạn trong tương lai!"
            ),
            color=0xff5555
        )

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)
        else:
            embed.set_thumbnail(url=member.default_avatar.url)

        embed.set_image(url="https://i.ibb.co/Ngk051kP/lily2-waifu2x-art-noise3-scale.png")

        embed.set_footer(text="Một người rời đi, nhiều kỷ niệm ở lại...")

        await channel.send(embed=embed)

# 🟢 Khởi động bot
TOKEN = os.environ.get("DISCORD_TOKEN")  # Đảm bảo đã đặt biến môi trường này
keep_alive()
bot.run(TOKEN)
