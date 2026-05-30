import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
import os
import re
import aiohttp
from flask import Flask
from threading import Thread

# Flask web server
app = Flask('')
@app.route('/')
def home():
    return "✅ Luna Bot is alive!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ========== CONFIGURATION ==========
# REPLACE THIS WITH YOUR ACTUAL DISCORD USER ID
# Right-click on your name in Discord -> Copy User ID
OWNER_USER_ID = 1232243863423418432  # <- CHANGE THIS NUMBER!

def is_owner():
    """Check if user is the bot owner by user ID"""
    async def predicate(ctx):
        if ctx.author.id != OWNER_USER_ID:
            await ctx.send(f"❌ You don't have permission! Only the bot owner can use this command.")
            return False
        return True
    return commands.check(predicate)

# ========== YOUTUBE FUNCTIONS ==========
async def process_youtube_channel(url):
    channel_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/@([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/c/([a-zA-Z0-9_-]+)'
    ]
    for pattern in channel_patterns:
        match = re.search(pattern, url)
        if match:
            channel_identifier = match.group(1)
            return {
                'type': 'channel',
                'handle': f"@{channel_identifier}",
                'url': f"https://youtube.com/@{channel_identifier}",
                'clean_url': f"https://youtube.com/@{channel_identifier}"
            }
    return None

async def shorten_youtube_link(url):
    video_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)'
    ]
    for pattern in video_patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://youtu.be/{video_id}"
    return None

async def send_subscribe_embed(channel, channel_handle="@FIXCORPORATION"):
    embed = discord.Embed(
        title="🎯 Don't Forget to Subscribe!",
        description=f"Check out **{channel_handle}** on YouTube!",
        color=discord.Color.gold()
    )
    embed.add_field(name="📺 Channel Link", value=f"https://youtube.com/{channel_handle}", inline=False)
    embed.add_field(name="🎁 What You Get", value="• Free Aimbot panel\n• 100% Safe\n• Trusted Panel Seller", inline=False)
    embed.add_field(name="📊 Current Stats", value="98 subscribers • 16 videos", inline=True)
    embed.set_footer(text="Subscribe, like, and stay tuned for more!")
    await channel.send(embed=embed)

# ========== MAIN ON_MESSAGE ==========
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if 'luna' in message.content.lower():
        await send_subscribe_embed(message.channel, "@FIXCORPORATION")
        return
    
    youtube_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/\S+'
    youtube_links = re.findall(youtube_pattern, message.content)
    
    for link in youtube_links:
        channel_info = await process_youtube_channel(link)
        if channel_info:
            embed = discord.Embed(
                title="📺 YouTube Channel Detected",
                description=f"**Channel:** {channel_info['handle']}\n**Link:** {channel_info['clean_url']}",
                color=discord.Color.purple()
            )
            embed.add_field(name="💡 Tip", value="Subscribe to support the channel!", inline=False)
            await message.channel.send(embed=embed)
            break
        
        short_link = await shorten_youtube_link(link)
        if short_link:
            embed = discord.Embed(
                title="🔗 YouTube Link Shortened",
                description=f"**Shortened:** {short_link}",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            break
    
    await bot.process_commands(message)

# ========== MODERATION COMMANDS ==========
@bot.command(name='timeout')
@is_owner()
async def timeout_member(ctx, member: discord.Member, duration: int = 60, *, reason: str = "No reason provided"):
    try:
        timeout_duration = timedelta(minutes=duration)
        await member.timeout(timeout_duration, reason=reason)
        
        embed = discord.Embed(
            title="⏰ Member Timed Out",
            description=f"{member.mention} has been timed out!",
            color=discord.Color.orange()
        )
        embed.add_field(name="Duration", value=f"{duration} minutes", inline=True)
        embed.add_field(name="Reason", value=reason, inline=True)
        # Moderator field removed - only shows Duration and Reason
        await ctx.send(embed=embed)
        
        try:
            await member.send(f"⚠️ You have been timed out in **{ctx.guild.name}** for {duration} minutes.\nReason: {reason}")
        except:
            pass
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to timeout this member!")

@bot.command(name='untimeout')
@is_owner()
async def untimeout_member(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"✅ {member.mention} timeout has been removed!")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove timeout!")

@bot.command(name='kick')
@is_owner()
async def kick_member(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    if member == ctx.author:
        await ctx.send("❌ You cannot kick yourself!")
        return
    try:
        await member.kick(reason=reason)
        await ctx.send(f"✅ {member.mention} has been kicked!\nReason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to kick this member!")

@bot.command(name='ban')
@is_owner()
async def ban_member(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    if member == ctx.author:
        await ctx.send("❌ You cannot ban yourself!")
        return
    try:
        await member.ban(reason=reason)
        await ctx.send(f"✅ {member.mention} has been banned!\nReason: {reason}")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to ban this member!")

@bot.command(name='unban')
@is_owner()
async def unban_member(ctx, *, member_name):
    try:
        banned_users = [entry async for entry in ctx.guild.bans()]
        member_name_split = member_name.split('#')
        for ban_entry in banned_users:
            user = ban_entry.user
            if user.name == member_name_split[0]:
                await ctx.guild.unban(user)
                await ctx.send(f"✅ Unbanned {user.mention}")
                return
        await ctx.send(f"❌ Could not find banned user: {member_name}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='clear')
@is_owner()
async def clear(ctx, amount=5):
    if amount > 100:
        amount = 100
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'✅ Deleted {amount} messages!', delete_after=3)

# ========== REGULAR COMMANDS ==========
@bot.command(name='subscribe')
async def subscribe_reminder(ctx):
    await send_subscribe_embed(ctx.channel, "@FIXCORPORATION")

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='commands')
async def show_commands(ctx):
    embed = discord.Embed(title="📋 Available Commands", color=discord.Color.green())
    embed.add_field(name="!ping", value="Check bot latency", inline=False)
    embed.add_field(name="!subscribe", value="Get FIX CORPORATION YouTube link", inline=False)
    embed.add_field(name="!timeout @user [min] [reason]", value="Timeout a member", inline=False)
    embed.add_field(name="!untimeout @user", value="Remove timeout", inline=False)
    embed.add_field(name="!kick @user [reason]", value="Kick a member", inline=False)
    embed.add_field(name="!ban @user [reason]", value="Ban a member", inline=False)
    embed.add_field(name="!clear [amount]", value="Delete messages", inline=False)
    embed.add_field(name="🎬 Auto Features", value="• Type 'Luna' anywhere to get subscribe link!\n• Automatically shortens YouTube links", inline=False)
    embed.set_footer(text="Made for FIX CORPORATION")
    await ctx.send(embed=embed)

# ========== ERROR HANDLING ==========
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument! Example: `!{ctx.command.name} @user`")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found! Please mention a valid user.")

# ========== BOT STARTUP ==========
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    print(f'📊 Bot is in {len(bot.guilds)} guilds')
    await bot.change_presence(activity=discord.Game(name="Type 'Luna' for YouTube link!"))

# ========== RUN BOT ==========
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN environment variable not found!")
    else:
        keep_alive()
        print("🚀 Starting bot...")
        bot.run(TOKEN)
