import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime, timedelta
import os
import re
import aiohttp

# Bot setup with command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# ========== CONFIGURATION ==========
# Change this to your actual owner role name
OWNER_ROLE_NAME = "Owner"

def is_owner():
    """Check if user has owner role"""
    async def predicate(ctx):
        role = discord.utils.get(ctx.author.roles, name=OWNER_ROLE_NAME)
        if role is None:
            await ctx.send(f"❌ You don't have permission! You need the **{OWNER_ROLE_NAME}** role to use this command.")
            return False
        return True
    return commands.check(predicate)

def check_owner_role(member):
    """Returns True if member has owner role"""
    return any(role.name == OWNER_ROLE_NAME for role in member.roles)

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

# ========== MAIN ON_MESSAGE EVENT ==========
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
            embed.set_footer(text="Channel link processed successfully!")
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
    
    msg_lower = message.content.lower()
    
    responses = {
        'hello': ['Hello! 👋', 'Hi there! 😊', 'Hey! How are you?'],
        'hi': ['Hello! 👋', 'Hi there! 😊', 'Hey! How are you?'],
        'bye': ['Goodbye! 👋', 'See you later!', 'Take care! 😊'],
        'how are you': ['I\'m fantastic! How about you?'],
        'good': ['That\'s great to hear! 🎉', 'Awesome! 😊', 'Wonderful!'],
        'i am fine': ['That\'s good to hear! 😊', 'Glad you\'re doing well! 👍', 'Awesome! Keep smiling! 😄'],
        'i\'m fine': ['That\'s good to hear! 😊', 'Glad you\'re doing well! 👍', 'Awesome! Keep smiling! 😄'],
        'fine': ['Great! 😊', 'Good to know! 👍', 'Awesome! 😄'],
        'i am good': ['That\'s wonderful! 🎉', 'So happy to hear that! 😊', 'Excellent! 👍'],
        'bad': ['Sorry to hear that! 😔 Hope things get better soon!', 'I\'m here if you want to talk! 💬'],
        'thanks': ['You\'re welcome! 😊', 'My pleasure!', 'Anytime! 👍'],
        'help': ['Type !commands to see all my commands!', 'How can I help you today?'],
        'who are you': ['I\'m a Discord bot created with Python! 🤖', 'Your friendly neighborhood bot! 😊'],
        'joke': [
            'Why don\'t scientists trust atoms? Because they make up everything! 😂',
            'What do you call a fake noodle? An impasta! 🍝',
            'Why did the scarecrow win an award? He was outstanding in his field! 🌾'
        ]
    }
    
    for keyword, response_list in responses.items():
        if keyword in msg_lower:
            response = random.choice(response_list)
            await message.channel.send(response)
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
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await ctx.send(embed=embed)
        
        try:
            await member.send(f"⚠️ You have been timed out in **{ctx.guild.name}** for {duration} minutes.\nReason: {reason}")
        except:
            pass
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to timeout this member!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='untimeout')
@is_owner()
async def untimeout_member(ctx, member: discord.Member):
    try:
        await member.timeout(None)
        await ctx.send(f"✅ {member.mention} timeout has been removed!")
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to remove timeout from this member!")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='kick')
@is_owner()
async def kick_member(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    if member == ctx.author:
        await ctx.send("❌ You cannot kick yourself!")
        return
    if member.guild_permissions.administrator:
        await ctx.send("❌ You cannot kick an administrator!")
        return
    try:
        embed = discord.Embed(
            title="👢 Member Kicked",
            description=f"{member.mention} has been kicked!",
            color=discord.Color.red()
        )
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await member.kick(reason=reason)
        await ctx.send(embed=embed)
        try:
            await member.send(f"⚠️ You have been kicked from **{ctx.guild.name}**.\nReason: {reason}")
        except:
            pass
    except discord.Forbidden:
        await ctx.send("❌ I don't have permission to kick this member!")

@bot.command(name='ban')
@is_owner()
async def ban_member(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    if member == ctx.author:
        await ctx.send("❌ You cannot ban yourself!")
        return
    if member.guild_permissions.administrator:
        await ctx.send("❌ You cannot ban an administrator!")
        return
    try:
        embed = discord.Embed(
            title="🔨 Member Banned",
            description=f"{member.mention} has been banned!",
            color=discord.Color.dark_red()
        )
        embed.add_field(name="Reason", value=reason, inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        await member.ban(reason=reason)
        await ctx.send(embed=embed)
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
            if user.name == member_name_split[0] and (len(member_name_split) == 1 or user.discriminator == member_name_split[1]):
                await ctx.guild.unban(user)
                await ctx.send(f"✅ Unbanned {user.mention}")
                return
        await ctx.send(f"❌ Could not find banned user: {member_name}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

@bot.command(name='warn')
@is_owner()
async def warn_member(ctx, member: discord.Member, *, reason: str = "No reason provided"):
    embed = discord.Embed(
        title="⚠️ Member Warned",
        description=f"{member.mention} has been warned!",
        color=discord.Color.yellow()
    )
    embed.add_field(name="Reason", value=reason, inline=True)
    embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
    await ctx.send(embed=embed)
    try:
        await member.send(f"⚠️ You have been warned in **{ctx.guild.name}**.\nReason: {reason}")
    except:
        pass

# ========== ADMIN HELP ==========
@bot.command(name='admin')
async def admin_commands(ctx):
    if not check_owner_role(ctx.author):
        await ctx.send(f"❌ You need the **{OWNER_ROLE_NAME}** role to view admin commands!")
        return
    embed = discord.Embed(
        title="🔒 Owner/Admin Commands",
        description=f"These commands are only available to users with the **{OWNER_ROLE_NAME}** role.",
        color=discord.Color.dark_red()
    )
    admin_commands_list = {
        "!timeout @user [min] [reason]": "Timeout a member",
        "!untimeout @user": "Remove timeout",
        "!kick @user [reason]": "Kick a member",
        "!ban @user [reason]": "Ban a member",
        "!unban username#1234": "Unban a member",
        "!warn @user [reason]": "Warn a member",
        "!clear [amount]": "Delete messages"
    }
    for cmd, desc in admin_commands_list.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    embed.set_footer(text="Use these commands responsibly!")
    await ctx.send(embed=embed)

# ========== REGULAR COMMANDS ==========
@bot.command(name='channel')
async def channel_info(ctx, *, handle_or_url):
    if not handle_or_url.startswith('http'):
        handle_or_url = f"https://youtube.com/@{handle_or_url.replace('@', '')}"
    channel_info_data = await process_youtube_channel(handle_or_url)
    if channel_info_data:
        embed = discord.Embed(
            title="📺 YouTube Channel Information",
            description=f"**Channel Handle:** {channel_info_data['handle']}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Channel URL", value=channel_info_data['clean_url'], inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Invalid YouTube channel link!")

@bot.command(name='subscribe')
async def subscribe_reminder(ctx, channel_handle=None):
    if not channel_handle:
        channel_handle = "@FIXCORPORATION"
    await send_subscribe_embed(ctx.channel, channel_handle)

@bot.command(name='promote')
async def promote_channel(ctx):
    embed = discord.Embed(
        title="🚀 Check Out FIX CORPORATION!",
        description="**Your source for gaming content and tools!**",
        color=discord.Color.blue(),
        url="https://youtube.com/@FIXCORPORATION"
    )
    embed.add_field(name="🎮 Content", value="• Gaming tutorials\n• Aimbot panels\n• Safe tools", inline=True)
    embed.add_field(name="📈 Growth", value="95+ subscribers\n15+ videos", inline=True)
    embed.add_field(name="🔗 Link", value="https://youtube.com/@FIXCORPORATION", inline=False)
    await ctx.send(embed=embed)

@bot.command(name='ytinfo')
async def youtube_info(ctx, *, url):
    video_id = None
    patterns = [r'v=([a-zA-Z0-9_-]+)', r'youtu\.be/([a-zA-Z0-9_-]+)', r'shorts/([a-zA-Z0-9_-]+)']
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    if not video_id:
        await ctx.send("❌ Could not extract video ID!")
        return
    short_link = f"https://youtu.be/{video_id}"
    embed = discord.Embed(title="📹 YouTube Video Info", color=discord.Color.red())
    embed.add_field(name="Short Link", value=short_link, inline=False)
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')

@bot.command(name='echo')
async def echo(ctx, *, message):
    await ctx.send(message)

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount=5):
    if amount > 100:
        amount = 100
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f'✅ Deleted {amount} messages!', delete_after=3)

@bot.command(name='userinfo')
async def userinfo(ctx, member: discord.Member = None):
    member = member or ctx.author
    embed = discord.Embed(title=f"User Info: {member.name}", color=member.color, timestamp=datetime.now())
    embed.add_field(name="ID", value=member.id, inline=True)
    embed.add_field(name="Joined Discord", value=member.created_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d"), inline=True)
    embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='roll')
async def roll(ctx, dice: str = "1d6"):
    try:
        rolls, limit = map(int, dice.split('d'))
        if rolls > 100:
            await ctx.send("❌ Too many rolls!")
            return
        if limit > 1000:
            await ctx.send("❌ Dice too big!")
            return
        results = [random.randint(1, limit) for _ in range(rolls)]
        total = sum(results)
        if rolls == 1:
            await ctx.send(f"🎲 You rolled: **{total}**")
        else:
            await ctx.send(f"🎲 Rolls: {results}\nTotal: **{total}**")
    except:
        await ctx.send("❌ Invalid format! Use: `!roll 2d20`")

@bot.command(name='serverinfo')
async def serverinfo(ctx):
    guild = ctx.guild
    embed = discord.Embed(title=f"Server Info: {guild.name}", color=discord.Color.blue(), timestamp=datetime.now())
    embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
    embed.add_field(name="Members", value=guild.member_count, inline=True)
    embed.add_field(name="Channels", value=len(guild.channels), inline=True)
    embed.add_field(name="Roles", value=len(guild.roles), inline=True)
    if guild.icon:
        embed.set_thumbnail(url=guild.icon.url)
    await ctx.send(embed=embed)

@bot.command(name='8ball')
async def eight_ball(ctx, *, question):
    responses_list = [
        "Yes! 🎯", "No ❌", "Maybe 🤔", "Definitely! ✅",
        "Ask again later 🔮", "Not likely ❎", "Of course! 😊"
    ]
    await ctx.send(f"🎱 Question: {question}\nAnswer: {random.choice(responses_list)}")

@bot.command(name='calc')
async def calculate(ctx, *, expression):
    try:
        allowed_chars = set("0123456789+-*/(). ")
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            await ctx.send(f"🧮 {expression} = **{result}**")
        else:
            await ctx.send("❌ Invalid characters!")
    except:
        await ctx.send("❌ Invalid expression!")

@bot.command(name='commands')
async def show_commands(ctx):
    embed = discord.Embed(title="📋 Available Commands", description="Here's what I can do!", color=discord.Color.green())
    commands_list = {
        "!ping": "Check bot latency",
        "!subscribe": "Get FIX CORPORATION info",
        "!commands": "Show this help menu",
        "!admin": "Show admin commands (Owner only)"
    }
    for cmd, desc in commands_list.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    embed.add_field(name="🎬 Auto Features", value="• Type 'Luna' to get subscribe info!\n• Shortens YouTube links", inline=False)
    embed.set_footer(text="Made for FIX CORPORATION")
    await ctx.send(embed=embed)

# ========== ERROR HANDLING ==========
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument!")
    elif isinstance(error, commands.CommandNotFound):
        pass
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Member not found!")
    else:
        await ctx.send(f"❌ Error: {str(error)}")

# ========== BOT STARTUP ==========
@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    print(f'📊 Bot is in {len(bot.guilds)} guilds')
    await bot.change_presence(activity=discord.Game(name="Welcome to Fixcorporation"))

# ========== RUN BOT ==========
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN environment variable not found!")
        print("📝 Please set DISCORD_TOKEN in Render dashboard → Environment tab")
    else:
        print("🚀 Starting bot...")
        bot.run(TOKEN)
