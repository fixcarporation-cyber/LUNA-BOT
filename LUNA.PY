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
OWNER_ROLE_NAME = "owner"

def is_owner():
    async def predicate(ctx):
        role = discord.utils.get(ctx.author.roles, name=OWNER_ROLE_NAME)
        if role is None:
            await ctx.send(f"❌ You don't have permission! You need the **{OWNER_ROLE_NAME}** role to use this command.")
            return False
        return True
    return commands.check(predicate)

def check_owner_role(member):
    return any(role.name == OWNER_ROLE_NAME for role in member.roles)

# Helper function to find member by username/nickname
async def find_member(ctx, user_input):
    """Find a member by mention, username, or nickname"""
    # Check if it's a mention
    if len(ctx.message.mentions) > 0:
        return ctx.message.mentions[0]
    
    # Clean up input (remove extra spaces)
    search_name = user_input.strip().lower()
    
    # Try exact match first
    for member in ctx.guild.members:
        if member.name.lower() == search_name or (member.nick and member.nick.lower() == search_name):
            return member
    
    # Try partial match (contains)
    for member in ctx.guild.members:
        if search_name in member.name.lower() or (member.nick and search_name in member.nick.lower()):
            return member
    
    return None

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
    embed.add_field(name="🎁 What You Get", value="• Free Aimbot panel\n• 100% Safe\n• Regular updates", inline=False)
    embed.add_field(name="📊 Current Stats", value="95 subscribers • 15 videos", inline=True)
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

# ========== MODERATION COMMANDS (OWNER ONLY) ==========
@bot.command(name='timeout')
@is_owner()
async def timeout_member(ctx, *, args: str = None):
    """Timeout a member. Usage: !timeout @user OR !timeout username OR !timeout username minutes reason"""
    
    if args is None:
        await ctx.send("❌ Please specify a user! Example: `!timeout @user 5 reason` or `!timeout username 5 reason`")
        return
    
    parts = args.split()
    user_input = parts[0]
    
    # Parse duration and reason
    duration = 60  # default
    reason_start = 1
    
    if len(parts) > 1 and parts[1].isdigit():
        duration = int(parts[1])
        reason_start = 2
    
    reason = " ".join(parts[reason_start:]) if len(parts) > reason_start else "No reason provided"
    
    # Find member
    member = None
    
    # Check if it's a mention
    if len(ctx.message.mentions) > 0:
        member = ctx.message.mentions[0]
    else:
        # Search by username or nickname
        search_name = user_input.lower()
        for m in ctx.guild.members:
            if m.name.lower() == search_name or (m.nick and m.nick.lower() == search_name):
                member = m
                break
        
        # If not found, try partial match
        if member is None:
            for m in ctx.guild.members:
                if search_name in m.name.lower() or (m.nick and search_name in m.nick.lower()):
                    member = m
                    break
    
    if member is None:
        await ctx.send(f"❌ Could not find user: {user_input}")
        return
    
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
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to timeout this member!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='untimeout')
@is_owner()
async def untimeout_member(ctx, *, user_input: str):
    """Remove timeout from a member. Usage: !untimeout @user OR !untimeout username"""
    
    # Find member
    member = None
    
    if len(ctx.message.mentions) > 0:
        member = ctx.message.mentions[0]
    else:
        search_name = user_input.lower()
        for m in ctx.guild.members:
            if m.name.lower() == search_name or (m.nick and m.nick.lower() == search_name):
                member = m
                break
    
    if member is None:
        await ctx.send(f"❌ Could not find user: {user_input}")
        return
    
    try:
        await member.timeout(None)
        await ctx.send(f"✅ {member.mention} timeout has been removed!")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove timeout!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='kick')
@is_owner()
async def kick_member(ctx, *, args: str):
    """Kick a member. Usage: !kick @user OR !kick username reason"""
    
    parts = args.split()
    user_input = parts[0]
    reason = " ".join(parts[1:]) if len(parts) > 1 else "No reason provided"
    
    # Find member
    member = None
    
    if len(ctx.message.mentions) > 0:
        member = ctx.message.mentions[0]
    else:
        search_name = user_input.lower()
        for m in ctx.guild.members:
            if m.name.lower() == search_name or (m.nick and m.nick.lower() == search_name):
                member = m
                break
    
    if member is None:
        await ctx.send(f"❌ Could not find user: {user_input}")
        return
    
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
async def ban_member(ctx, *, args: str):
    """Ban a member. Usage: !ban @user OR !ban username reason"""
    
    parts = args.split()
    user_input = parts[0]
    reason = " ".join(parts[1:]) if len(parts) > 1 else "No reason provided"
    
    # Find member
    member = None
    
    if len(ctx.message.mentions) > 0:
        member = ctx.message.mentions[0]
    else:
        search_name = user_input.lower()
        for m in ctx.guild.members:
            if m.name.lower() == search_name or (m.nick and m.nick.lower() == search_name):
                member = m
                break
    
    if member is None:
        await ctx.send(f"❌ Could not find user: {user_input}")
        return
    
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
            if user.name.lower() == member_name_split[0].lower():
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

@bot.command(name='admin')
async def admin_commands(ctx):
    if not check_owner_role(ctx.author):
        await ctx.send(f"❌ You need the **{OWNER_ROLE_NAME}** role to view admin commands!")
        return
    embed = discord.Embed(title="🔒 Owner Commands", color=discord.Color.dark_red())
    embed.add_field(name="!timeout @user/username [min] [reason]", value="Timeout a member", inline=False)
    embed.add_field(name="!untimeout @user/username", value="Remove timeout", inline=False)
    embed.add_field(name="!kick @user/username [reason]", value="Kick a member", inline=False)
    embed.add_field(name="!ban @user/username [reason]", value="Ban a member", inline=False)
    embed.add_field(name="!unban username#1234", value="Unban a member", inline=False)
    embed.add_field(name="!clear [amount]", value="Delete messages", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='commands')
async def show_commands(ctx):
    embed = discord.Embed(title="📋 Available Commands", color=discord.Color.green())
    embed.add_field(name="!ping", value="Check bot latency", inline=False)
    embed.add_field(name="!subscribe", value="Get FIX CORPORATION YouTube link", inline=False)
    embed.add_field(name="!admin", value="Show owner commands", inline=False)
    embed.add_field(name="!commands", value="Show this help menu", inline=False)
    embed.add_field(name="🎬 Auto Features", value="• Type 'Luna' anywhere to get subscribe link!\n• Automatically shortens YouTube links", inline=False)
    await ctx.send(embed=embed)

# ========== ERROR HANDLING ==========
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument!")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ Error: {str(error)}")

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
