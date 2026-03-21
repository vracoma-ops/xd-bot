# vouch.py
import discord
from discord.ext import commands, tasks
from flask import Flask
import threading
import os

# ------------------- CONFIG -------------------
TOKEN = os.environ.get("TOKEN")  # Set this in Render's environment variables
GUILD_ID = int(os.environ.get("GUILD_ID", "948971532431015976"))
CONFIG_CHANNEL_ID = int(os.environ.get("CONFIG_CHANNEL_ID", "1478282165618737266"))
VOUCHES_CHANNEL_ID = int(os.environ.get("VOUCHES_CHANNEL_ID", "1477973914914132092"))
APPROVE_EMOJI = "✅"
DECLINE_EMOJI = "❌"

# ------------------- DISCORD BOT -------------------
intents = discord.Intents.default()
intents.members = True           # Only enable if needed
intents.message_content = True   # Needed to read messages

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    heartbeat.start()  # Start heartbeat to keep bot alive

# ------------------- HEARTBEAT TASK -------------------
# Optional: ping self every 5 minutes to prevent idle disconnects
@tasks.loop(minutes=5)
async def heartbeat():
    print("Heartbeat: bot is alive")

# ------------------- VOUCH COMMAND -------------------
@bot.command()
async def vouch(ctx, user: discord.Member, product: str, rating: int):
    """Collect a vouch request."""
    if ctx.channel.id != CONFIG_CHANNEL_ID:
        await ctx.send("Use the correct channel to submit vouches.")
        return
    
    # Create an embed
    embed = discord.Embed(
        title=f"Vouch request for {user}",
        description=f"Product/Service: {product}\nRating: {rating}/5",
        color=discord.Color.blue()
    )
    msg = await ctx.send(embed=embed)
    
    # React for approval / decline
    await msg.add_reaction(APPROVE_EMOJI)
    await msg.add_reaction(DECLINE_EMOJI)

    await ctx.send("Vouch request submitted for review.")

# ------------------- FLASK KEEP-ALIVE -------------------
# Render requires a web server to keep free services alive
app = Flask("")

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

# ------------------- RUN BOTH -------------------
if __name__ == "__main__":
    # Start Flask in a separate thread
    threading.Thread(target=run_flask).start()
    
    # Run Discord bot
    bot.run(TOKEN)
