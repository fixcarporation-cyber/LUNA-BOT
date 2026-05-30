import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime
import os
import re
import aiohttp

# Bot setup with command prefix
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Function to handle YouTube channel links
async def process_youtube_channel(url):
    """
    Process YouTube channel URLs and return formatted info
    """
    channel_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/@([a-zA-Z0-9_-]+)',  # @handle format
        r'(?:https?://)?(?:www\.)?youtube\.com/channel/([a-zA-Z0-9_-]+)',  # Channel ID format
        r'(?:https?://)?(?:www\.)?youtube\.com/c/([a-zA-Z0-9_-]+)'  # /c/ format
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

# Function to handle YouTube video links
async def shorten_youtube_link(url):
    """
    Convert YouTube video links to youtu.be format
    """
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

# Main on_message event with channel support
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Check for YouTube links
    youtube_pattern = r'(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/\S+'
    youtube_links = re.findall(youtube_pattern, message.content)
    
    for link in youtube_links:
        # Check if it's a channel link first
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
        
        # If not a channel, try video shortening
        short_link = await shorten_youtube_link(link)
        if short_link:
            embed = discord.Embed(
                title="🔗 YouTube Link Shortened",
                description=f"**Original:** {link}\n**Shortened:** {short_link}",
                color=discord.Color.red()
            )
            await message.channel.send(embed=embed)
            break
    
    # Rest of your existing on_message logic
    msg_lower = message.content.lower()
    
    responses = {
        'hello': ['Hello! 👋', 'Hi there! 😊', 'Hey! How are you?'],
        'hi': ['Hello! 👋', 'Hi there! 😊', 'Hey! How are you?'],
        'bye': ['Goodbye! 👋', 'See you later!', 'Take care! 😊'],
        'how are you': ['I\'m doing great, thanks for asking! 🤖', 'All systems operational! 👍', 'I\'m fantastic! How about you?'],
        'good': ['That\'s great to hear! 🎉', 'Awesome! 😊', 'Wonderful!'],
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

# New command: Get channel info
@bot.command(name='channel')
async def channel_info(ctx, *, handle_or_url):
    """Get information about a YouTube channel"""
    # Check if it's a handle or URL
    if not handle_or_url.startswith('http'):
        handle_or_url = f"https://youtube.com/@{handle_or_url.replace('@', '')}"
    
    channel_info = await process_youtube_channel(handle_or_url)
    if channel_info:
        embed = discord.Embed(
            title="📺 YouTube Channel Information",
            description=f"**Channel Handle:** {channel_info['handle']}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Channel URL", value=channel_info['clean_url'], inline=False)
        embed.add_field(name="💡 Pro Tip", value="Use `!subscribe` to get a reminder!", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Invalid YouTube channel link! Use format: `@channelname` or full URL")

# Command: Subscribe reminder for your channel
@bot.command(name='Luna give me youtube link')
async def subscribe_reminder(ctx, channel_handle=None):
    """Get reminder to subscribe to FIX CORPORATION"""
    if not channel_handle:
        channel_handle = "@FIXCORPORATION"
    
    embed = discord.Embed(
        title="🎯 Don't Forget to Subscribe!",
        description=f"Check out **{channel_handle}** on YouTube!",
        color=discord.Color.gold()
    )
    embed.add_field(name="📺 Channel Link", value=f"https://youtube.com/{channel_handle}", inline=False)
    embed.add_field(name="🎁 What You Get", value="• Free Aimbot panel\n• 100% Safe\n• Regular updates", inline=False)
    embed.add_field(name="📊 Current Stats", value="95 subscribers • 15 videos", inline=True)
    embed.set_footer(text="Subscribe, like, and stay tuned for more!")
    
    await ctx.send(embed=embed)

# Command: Promote your channel
@bot.command(name='promote')
async def promote_channel(ctx):
    """Promote FIX CORPORATION channel"""
    embed = discord.Embed(
        title="🚀 Check Out FIX CORPORATION!",
        description="**Your source for gaming content and tools!**",
        color=discord.Color.blue(),
        url="https://youtube.com/@FIXCORPORATION"
    )
    embed.add_field(name="🎮 Content", value="• Gaming tutorials\n• Aimbot panels\n• Safe tools", inline=True)
    embed.add_field(name="📈 Growth", value="95+ subscribers\n15+ videos", inline=True)
    embed.add_field(name="🔗 Link", value="https://youtube.com/@FIXCORPORATION", inline=False)
    embed.set_thumbnail(url="https://img.youtube.com/vi/default/mqdefault.jpg")
    
    await ctx.send(embed=embed)

# Command: Video info (existing)
@bot.command(name='ytinfo')
async def youtube_info(ctx, *, url):
    """Get information about a YouTube video"""
    video_id = None
    patterns = [
        r'v=([a-zA-Z0-9_-]+)',
        r'youtu\.be/([a-zA-Z0-9_-]+)',
        r'shorts/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        await ctx.send("❌ Could not extract video ID from the link!")
        return
    
    short_link = f"https://youtu.be/{video_id}"
    embed = discord.Embed(
        title="📹 YouTube Video Info",
        color=discord.Color.red()
    )
    embed.add_field(name="Short Link", value=short_link, inline=False)
    embed.add_field(name="Video ID", value=video_id, inline=True)
    embed.add_field(name="💡 Tip", value="Check out FIX CORPORATION for more content!", inline=False)
    await ctx.send(embed=embed)

# Command: List all commands (updated)
@bot.command(name='commands')
async def show_commands(ctx):
    embed = discord.Embed(
        title="📋 Available Commands",
        description="Here's what I can do!",
        color=discord.Color.green()
    )
    
    commands_list = {
        "!ping": "Check bot latency",
        "!echo <message>": "Repeat your message",
        "!clear <amount>": "Delete messages (Admin only)",
        "!userinfo [@user]": "Get user information",
        "!serverinfo": "Get server information",
        "!roll <XdY>": "Roll dice (e.g., 2d20)",
        "!8ball <question>": "Ask the magic 8ball",
        "!calc <expression>": "Basic calculator (2+2)",
        "!channel <@handle>": "Get YouTube channel info",
        "!subscribe": "Get reminder to subscribe to FIX CORPORATION",
        "!promote": "Promote the FIX CORPORATION channel",
        "!ytinfo <url>": "Get YouTube video information",
        "!commands": "Show this help menu"
    }
    
    for cmd, desc in commands_list.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.add_field(
        name="🎬 Auto Features",
        value="• Automatically detects YouTube videos & channels\n• Creates short links for videos\n• Promotes FIX CORPORATION content",
        inline=False
    )
    
    embed.set_footer(text="Made for FIX CORPORATION • Subscribe for free aimbot!")
    await ctx.send(embed=embed)

# The rest of your existing commands (ping, clear, userinfo, etc.) remain the same
# ... [keep all your other command functions from previous code] ...

# Run the bot
if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN environment variable not found!")
        print("📝 Please set DISCORD_TOKEN in Render dashboard → Environment tab")
    else:
        keep_alive()
        print("🚀 Starting bot...")
        bot.run(TOKEN)
