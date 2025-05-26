import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional
import os
import aiohttp
from flask import Flask
from threading import Thread

# Flask server
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# Discord bot
intents = discord.Intents.default()
intents.members = True
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

# Slash command: /say channel: #channel message: "text"
@bot.tree.command(name="say", description="Bot sẽ gửi nội dung và ảnh (nếu có) vào kênh chỉ định")
@app_commands.describe(
    channel="Kênh muốn gửi tin",
    message="Nội dung tin nhắn",
    image="(Tùy chọn) Ảnh đính kèm"
)
async def say(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    message: str,
    image: Optional[discord.Attachment] = None
):
    user = interaction.guild.get_member(interaction.user.id)
    bot_member = interaction.guild.me

    if user is None:
        await interaction.response.send_message("Không thể xác định vai trò của bạn.", ephemeral=True)
        return

    if user.top_role <= bot_member.top_role:
        await interaction.response.send_message("Bạn cần có vai trò cao hơn bot để dùng lệnh này.", ephemeral=True)
        return

    # Gửi phản hồi trước (phản hồi bắt buộc)
    await interaction.response.send_message(f"Đang gửi vào {channel.mention}...", ephemeral=True)

    # Sau đó gửi vào kênh
    if image and image.content_type and image.content_type.startswith("image/"):
        await channel.send(content=message, file=await image.to_file())
    else:
        await channel.send(content=message)

@bot.tree.command(name="say_in_thread", description="Gửi tin vào một chủ đề cụ thể theo ID")
@app_commands.describe(
    thread_id="ID của chủ đề",
    message="Nội dung cần gửi",
    image="(Tùy chọn) Ảnh đính kèm"
)
async def say_in_thread(
    interaction: discord.Interaction,
    thread_id: str,
    message: str,
    image: Optional[discord.Attachment] = None
):
    guild = interaction.guild
    user = guild.get_member(interaction.user.id)
    bot_member = guild.me

    # Kiểm tra vai trò
    if user is None or bot_member is None:
        await interaction.response.send_message("Không thể xác định vai trò.", ephemeral=True)
        return

    if user.top_role <= bot_member.top_role:
        await interaction.response.send_message("Bạn cần có vai trò **cao hơn bot** để dùng lệnh này.", ephemeral=True)
        return

    # Tìm chủ đề theo ID
    try:
        thread = guild.get_thread(int(thread_id))
    except ValueError:
        await interaction.response.send_message("ID không hợp lệ.", ephemeral=True)
        return

    if thread is None:
        await interaction.response.send_message("Không tìm thấy chủ đề có ID đó.", ephemeral=True)
        return

    await interaction.response.send_message(f"Đang gửi vào chủ đề **{thread.name}**...", ephemeral=True)

    # Gửi nội dung và ảnh (nếu có)
    if image and image.content_type and image.content_type.startswith("image/"):
        await thread.send(content=message, file=await image.to_file())
    else:
        await thread.send(content=message)    
    

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name='hello-goodbye')
    role_channel = discord.utils.get(member.guild.text_channels, name='role')  # Tên kênh chọn role

    if member.bot:
        role = discord.utils.get(member.guild.roles, name="Bot")
        if role:
            await member.add_roles(role)

    elif channel:
        role_mention = role_channel.mention if role_channel else "`role`"

        embed = discord.Embed(
            title="👋 Chào mừng một đồng môn mới đã đặt chân vào lãnh địa!",
            description=(
                f"{member.mention} đã tham gia server **{member.guild.name}**!\n\n"
                "🌟 Nơi bạn có thể giao lưu với dàn nhân sự và fan của team chắc vậy.\n\n"
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

@bot.event
async def on_member_update(before, after):
    booster_role = discord.utils.get(after.guild.roles, name="Server Booster")

    if booster_role:
        if booster_role not in before.roles and booster_role in after.roles:
            channel = discord.utils.get(after.guild.text_channels, name='boost-server')
            if channel:
                embed = discord.Embed(
                    title="💎 BOOST SERVER!",
                    description=(
                        f"{after.mention}, cảm ơn bạn đã ủng hộ cho server **{after.guild.name}** của tụi mình! 💖"
                    ),
                    color=0xff99cc
                )

                embed.set_thumbnail(url=after.avatar.url if after.avatar else after.default_avatar.url)

                embed.set_image(url="https://gifdb.com/images/thumbnail/thank-you-anime-girl-cute-dance-love-vjx4h36muzs0rps0.gif")

                embed.set_footer(text="Cảm ơn vì sự ủng hộ của bạn!")

                await channel.send(embed=embed)



import os
TOKEN = os.environ.get("DISCORD_TOKEN") # Đảm bảo đã đặt biến môi trường này
keep_alive()    
bot.run(TOKEN)
