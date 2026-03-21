import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os

# ---------------- KEEP ALIVE SERVER (RENDER FIX) ----------------

from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

def keep_alive():
    Thread(target=run_web, daemon=True).start()

# ---------------- CONFIG ----------------

GUILD_ID = 948971532431015976
CONFIG_CHANNEL_ID = 1478282165618737266
VOUCHES_CHANNEL_ID = 1478334777533927456
ADMIN_ID = 458624557763526666

APPROVE_EMOJI = "✅"
DECLINE_EMOJI = "❌"

# ---------------- BOT SETUP ----------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

processed_messages = set()

# ---------------- READY ----------------

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print("Sync error:", e)

# ---------------- ERROR HANDLER ----------------

@bot.event
async def on_app_command_error(interaction: discord.Interaction, error):
    print("ERROR:", error)
    try:
        await interaction.followup.send("Something went wrong.", ephemeral=True)
    except:
        pass

# ---------------- VOUCH COMMAND ----------------

@tree.command(
    name="vouch",
    description="Submit a vouch",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    product="Product purchased",
    quantity="Quantity purchased",
    duration="Duration of service",
    proof="Upload proof image"
)
async def vouch(
    interaction: discord.Interaction,
    product: str,
    quantity: str,
    duration: str,
    proof: discord.Attachment
):

    print("Vouch used by:", interaction.user)

    await interaction.response.defer(ephemeral=True)

    if not proof.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        await interaction.followup.send(
            "Upload PNG/JPG proof only.",
            ephemeral=True
        )
        return

    config_channel = bot.get_channel(CONFIG_CHANNEL_ID)

    if not config_channel:
        await interaction.followup.send("Config channel not found.", ephemeral=True)
        return

    embed = discord.Embed(
        title="New Vouch Submission",
        color=discord.Color.blue()
    )

    embed.add_field(name="Product", value=product, inline=False)
    embed.add_field(name="Quantity", value=quantity, inline=True)
    embed.add_field(name="Duration", value=duration, inline=True)

    embed.set_image(url=proof.url)

    embed.set_footer(
        text=f"Submitted by {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    message = await config_channel.send(
        content=f"Vouch from {interaction.user.mention}",
        embed=embed
    )

    await message.add_reaction(APPROVE_EMOJI)
    await message.add_reaction(DECLINE_EMOJI)

    await interaction.followup.send(
        "Your vouch has been submitted for approval.",
        ephemeral=True
    )

# ---------------- REACTION HANDLER ----------------

@bot.event
async def on_raw_reaction_add(payload):

    if payload.user_id == bot.user.id:
        return

    if payload.channel_id != CONFIG_CHANNEL_ID:
        return

    if payload.user_id != ADMIN_ID:
        return

    if payload.message_id in processed_messages:
        return

    channel = bot.get_channel(payload.channel_id)
    if not channel:
        return

    message = await channel.fetch_message(payload.message_id)

    if not message.embeds:
        return

    emoji = str(payload.emoji)

    vouches_channel = bot.get_channel(VOUCHES_CHANNEL_ID)
    if not vouches_channel:
        return

    embed = message.embeds[0]

    # ✅ APPROVE
    if emoji == APPROVE_EMOJI:

        processed_messages.add(message.id)

        date = datetime.now().strftime("%d-%m-%Y")

        approved_embed = discord.Embed(
            title=f"New Vouch ({date})",
            color=discord.Color.green()
        )

        approved_embed.description = message.content

        for field in embed.fields:
            approved_embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )

        if embed.image:
            approved_embed.set_image(url=embed.image.url)

        guild = bot.get_guild(GUILD_ID)
        user = guild.get_member(payload.user_id)

        if user:
            approved_embed.set_footer(text=f"Approved by {user.display_name}")

        await vouches_channel.send(embed=approved_embed)
        await message.delete()

    # ❌ DECLINE
    elif emoji == DECLINE_EMOJI:

        processed_messages.add(message.id)
        await message.delete()

# ---------------- RUN ----------------

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("TOKEN missing")
    exit()

keep_alive()  # ✅ important for Render

bot.run(TOKEN)
