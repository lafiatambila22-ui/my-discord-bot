"""
Discord Bot — All 3 Milestones
================================
Milestone 1: Registration + ping/pong
Milestone 2: autocomplete, reddit top post, simple chatbot
Milestone 3: welcome DM, game-alert announcer, keyword meme poster

Setup
-----
1. pip install discord.py aiohttp python-dotenv
2. Create a .env file: DISCORD_TOKEN=your_token_here
3. In the Discord Developer Portal → Bot → Privileged Gateway Intents,
   enable  "Server Members Intent"  and  "Message Content Intent".
4. python bot.py
"""

import os
import random
import asyncio
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# ── Intents ────────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True   # needed to read message text
intents.members = True           # needed for on_member_join

bot = commands.Bot(command_prefix="!", intents=intents)

# ── Milestone 3 config ─────────────────────────────────────────────────────────
# Edit these to match your server's channel names / IDs
ANNOUNCE_CHANNEL_NAME = "general"          # channel for game alerts & memes
WELCOME_CHANNEL_NAME  = "welcome"          # optional: public welcome channel

# Keyword → meme URL mapping (add your own!)
MEME_TRIGGERS = {
    "python":  "https://i.imgur.com/removed.png",  # replace with real URLs
    "discord": "https://i.imgur.com/removed.png",
    "bug":     "https://i.imgur.com/removed.png",
}

# Simple autocomplete word list (expand as needed)
WORD_BANK = [
    "python", "programming", "discord", "developer", "database",
    "documentation", "deployment", "debugging", "dependency",
]

# Tiny chatbot response map (Milestone 2)
CHAT_RESPONSES = {
    "hello":   "Hey there! 👋",
    "hi":      "Hi! What's up?",
    "how are you": "I'm a bot, but I'm doing great! 🤖",
    "bye":     "See you later! 👋",
    "help":    "Try !ping, !autocomplete <word>, !reddit <subreddit>, or !chat <message>!",
}


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE 1 — Ping / Pong
# ══════════════════════════════════════════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅  Logged in as {bot.user} (ID: {bot.user.id})")
    print("─" * 40)


@bot.command(name="ping")
async def ping(ctx):
    """Classic ping/pong — replies with bot latency."""
    latency_ms = round(bot.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency: **{latency_ms} ms**")


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE 2 — Existing project features
# ══════════════════════════════════════════════════════════════════════════════

@bot.command(name="autocomplete")
async def autocomplete(ctx, prefix: str = ""):
    """
    !autocomplete <prefix>
    Suggests words from WORD_BANK that start with the given prefix.
    """
    if not prefix:
        await ctx.send("Usage: `!autocomplete <word_prefix>`")
        return

    matches = [w for w in WORD_BANK if w.startswith(prefix.lower())]

    if matches:
        formatted = ", ".join(f"`{m}`" for m in matches[:5])
        await ctx.send(f"💡 Completions for **{prefix}**: {formatted}")
    else:
        await ctx.send(f"❌ No completions found for **{prefix}**.")


@bot.command(name="reddit")
async def reddit(ctx, subreddit: str = "programming"):
    """
    !reddit [subreddit]
    Fetches the top post from the given subreddit (default: programming).
    Uses Reddit's public JSON API — no API key required.
    """
    url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=1&t=day"
    headers = {"User-Agent": "DiscordBot/1.0"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=8)) as resp:
                if resp.status != 200:
                    await ctx.send(f"⚠️ Couldn't reach r/{subreddit} (HTTP {resp.status}).")
                    return
                data = await resp.json()
        except asyncio.TimeoutError:
            await ctx.send("⏱️ Request timed out. Try again in a moment.")
            return
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
            return

    posts = data.get("data", {}).get("children", [])
    if not posts:
        await ctx.send(f"No posts found in r/{subreddit}.")
        return

    post = posts[0]["data"]
    title  = post.get("title", "No title")
    author = post.get("author", "unknown")
    score  = post.get("score", 0)
    link   = f"https://reddit.com{post.get('permalink', '')}"

    embed = discord.Embed(
        title=title[:256],
        url=link,
        color=0xFF4500,
    )
    embed.set_footer(text=f"👤 u/{author}  •  ⬆️ {score:,}  •  r/{subreddit}")
    await ctx.send(embed=embed)


@bot.command(name="chat")
async def chat(ctx, *, message: str = ""):
    """
    !chat <message>
    Simple keyword-based chatbot reply.
    """
    if not message:
        await ctx.send("Usage: `!chat <your message>`")
        return

    lower = message.lower().strip()
    for key, reply in CHAT_RESPONSES.items():
        if key in lower:
            await ctx.send(reply)
            return

    # Fallback: echo + acknowledge
    await ctx.send(f"🤔 You said: *{message}*  — I'm still learning! Try `!chat help`.")


# ══════════════════════════════════════════════════════════════════════════════
# MILESTONE 3 — Brand-new custom commands
# ══════════════════════════════════════════════════════════════════════════════

# ── 3a. Welcome DM on member join ─────────────────────────────────────────────

@bot.event
async def on_member_join(member: discord.Member):
    """
    Sends a personalized DM to every new member and posts a public
    welcome message in the configured welcome channel.
    """
    guild = member.guild

    # Private DM welcome
    try:
        await member.send(
            f"👋 Welcome to **{guild.name}**, {member.mention}!\n\n"
            "Here are a few things you can do:\n"
            "• Type `!ping` to test the bot\n"
            "• Type `!reddit` for today's top programming post\n"
            "• Type `!chat hello` to say hi\n\n"
            "Enjoy the server! 🎉"
        )
    except discord.Forbidden:
        pass  # user has DMs disabled — that's okay

    # Public welcome in #welcome channel (if it exists)
    welcome_ch = discord.utils.get(guild.text_channels, name=WELCOME_CHANNEL_NAME)
    if welcome_ch:
        await welcome_ch.send(
            f"🎊 Everyone welcome {member.mention} to **{guild.name}**! "
            f"We now have **{guild.member_count}** members. Say hi! 👋"
        )


# ── 3b. Game alert — announce when two members share a game ───────────────────

@bot.command(name="gamealert")
async def gamealert(ctx):
    """
    !gamealert
    Scans all online members' activities. If two or more people are playing
    the same game, it posts a shout-out so they can group up.
    """
    game_players: dict[str, list[str]] = {}

    for member in ctx.guild.members:
        if member.bot or member.status == discord.Status.offline:
            continue
        for activity in member.activities:
            if isinstance(activity, discord.Game):
                game_name = activity.name
                game_players.setdefault(game_name, []).append(member.display_name)

    shared = {g: p for g, p in game_players.items() if len(p) >= 2}

    if not shared:
        await ctx.send("🎮 No shared games right now. Check back later!")
        return

    embed = discord.Embed(
        title="🎮 Who's playing the same game?",
        color=0x5865F2,
    )
    for game, players in shared.items():
        names = ", ".join(players)
        embed.add_field(name=game, value=names, inline=False)
    embed.set_footer(text="Tip: jump in and group up!")

    await ctx.send(embed=embed)


# ── 3c. Keyword listener — post a meme for trigger words ──────────────────────

@bot.event
async def on_message(message: discord.Message):
    """
    Listens for trigger keywords in every message.
    If found, replies with the corresponding meme image URL.
    Also calls process_commands so other !commands still work.
    """
    # Ignore the bot's own messages
    if message.author.bot:
        return

    content_lower = message.content.lower()

    for keyword, meme_url in MEME_TRIGGERS.items():
        if keyword in content_lower:
            # Only respond once per message (first match wins)
            await message.channel.send(meme_url)
            break  # remove this break if you want ALL matching memes

    # IMPORTANT: let other commands run after this event
    await bot.process_commands(message)


# ══════════════════════════════════════════════════════════════════════════════
# Run the bot
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not TOKEN:
        raise RuntimeError(
            "DISCORD_TOKEN not found. "
            "Create a .env file with: DISCORD_TOKEN=your_token_here"
        )
    bot.run(TOKEN)
