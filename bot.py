import os
import asyncio
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

# load the token from .env
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# set up intents so the bot can read messages and see members
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# words for autocomplete
WORD_BANK = [
    "python", "programming", "discord", "developer", "database",
    "documentation", "deployment", "debugging",
]

# chatbot replies
CHAT_RESPONSES = {
    "hello": "hey whats up",
    "hi": "hi!",
    "how are you": "im a bot so i dont really have feelings lol",
    "bye": "see ya",
    "help": "try !ping, !autocomplete, !reddit, or !chat",
}

# keywords that trigger a meme
MEME_TRIGGERS = {
    "python": "https://imgur.com/gallery/albino-python-5FfmeSA#/t/python",
    "bug": "https://imgur.com/gallery/is-dangerous-WqDlXuw#/t/bug",
    "discord": "https://imgur.com/gallery/discord-notification-icon-1000x1000-pixels-UxQWd#/t/discordapp",
}


# runs when bot is ready
@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


# milestone 1 - ping pong
@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"pong! {latency}ms")


# milestone 2 - autocomplete a word
@bot.command()
async def autocomplete(ctx, prefix=""):
    if not prefix:
        await ctx.send("usage: !autocomplete <word>")
        return
    matches = [w for w in WORD_BANK if w.startswith(prefix.lower())]
    if matches:
        await ctx.send(f"completions: {', '.join(matches[:5])}")
    else:
        await ctx.send("no matches found")


# milestone 2 - get top post from a subreddit
@bot.command()
async def reddit(ctx, subreddit="programming"):
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=1&t=day"
    headers = {"User-Agent": "mybot/1.0"}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                data = await resp.json()
        except Exception:
            await ctx.send("something went wrong")
            return
    posts = data.get("data", {}).get("children", [])
    if not posts:
        await ctx.send("no posts found")
        return
    post = posts[0]["data"]
    title = post.get("title", "no title")
    link = f"https://reddit.com{post.get('permalink', '')}"
    await ctx.send(f"**{title}**\n{link}")


# milestone 2 - simple chatbot
@bot.command()
async def chat(ctx, *, message=""):
    if not message:
        await ctx.send("say something: !chat <message>")
        return
    for key, reply in CHAT_RESPONSES.items():
        if key in message.lower():
            await ctx.send(reply)
            return
    await ctx.send("idk what to say lol")


# milestone 3 - welcome message when someone joins
@bot.event
async def on_member_join(member):
    # try to dm them
    try:
        await member.send(f"hey {member.name} welcome to the server!")
    except:
        pass
    # also post in general
    channel = discord.utils.get(member.guild.text_channels, name="general")
    if channel:
        await channel.send(f"everyone welcome {member.mention}!")


# milestone 3 - see who is playing the same game
@bot.command()
async def gamealert(ctx):
    games = {}
    for member in ctx.guild.members:
        if member.bot:
            continue
        for activity in member.activities:
            if isinstance(activity, discord.Game):
                games.setdefault(activity.name, []).append(member.display_name)
    # only show games with 2+ players
    shared = {g: p for g, p in games.items() if len(p) >= 2}
    if not shared:
        await ctx.send("nobody is playing the same game rn")
        return
    msg = "people playing the same game:\n"
    for game, players in shared.items():
        msg += f"{game}: {', '.join(players)}\n"
    await ctx.send(msg)


# milestone 3 - post a meme when certain words are said
@bot.event
async def on_message(message):
    # ignore the bot itself
    if message.author.bot:
        return
    for keyword, meme in MEME_TRIGGERS.items():
        if keyword in message.content.lower():
            await message.channel.send(meme)
            break
    # make sure other commands still work
    await bot.process_commands(message)


bot.run(TOKEN)
