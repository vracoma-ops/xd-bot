import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import os
import threading
import time
import requests

# ---------------- KEEP ALIVE WEB SERVER ----------------
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Vouch bot is running!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Start web server
threading.Thread(target=run_web, daemon=True).start()


# ---------------- SELF PING SYSTEM ----------------
def self_ping():
    while True:
        try:
            url = os.getenv("RENDER_URL")
            if url:
                requests.get(url)
                print("Self ping sent")
        except Exception as e:
            print("Ping failed:", e)

        time.sleep(300)  # every 5 minutes

threading.Thread(target=self_ping, daemon=True).start()
# -------------------------------------------------


# ------------------- CONFIG -------------------
GUILD_ID = 948971532431015976
CONFIG_CHANNEL_ID = 1478282165618737266
VOUCHES_CHANNEL_ID = 1478334777533927456

ADMIN_ID = 458624557763526666

APPROVE_EMOJI = "✅"
DECLINE_EMOJI = "❌"
# ---------------------------------------------


intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.reactions = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

processed_messages = set()


# ---------------- BOT READY ----------------
@bot.event
async def on_ready():
    print(f"[V1x Vouch] Logged in as {bot.user} ✅")

    try:
        synced = await tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"Slash command sync failed: {e}")


# ---------------- VOUCH COMMAND ----------------
@tree.command(
    name="vouch",
    description="Submit a vouch",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    seller="Seller's name",
    product="Product/service bought",
    quantity="Quantity purchased",
    proof="Attach proof image"
)
async def vouch(
    interaction: discord.Interaction,
    seller: str,
    product: str,
    quantity: str,
    proof: discord.Attachment
):

    if not proof.filename.lower().endswith((".png", ".jpg", ".jpeg")):
        await interaction.response.send_message(
            "⚠ Please upload a valid image (png, jpg, jpeg).",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    config_channel = bot.get_channel(CONFIG_CHANNEL_ID)

    if not config_channel:
        await interaction.followup.send(
            "⚠ Config channel not found.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="New Vouch Submission",
        color=discord.Color.blue()
    )

    embed.add_field(name="Seller", value=seller, inline=True)
    embed.add_field(name="Product/Service", value=product, inline=True)
    embed.add_field(name="Quantity", value=quantity, inline=True)

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
        "✅ Your vouch has been submitted for approval!",
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

    original_embed = message.embeds[0]

    if emoji == APPROVE_EMOJI:

        processed_messages.add(message.id)

        date_now = datetime.now().strftime("%d-%m-%Y")

        approved_embed = discord.Embed(
            title=f"New Vouch ({date_now})",
            color=discord.Color.green()
        )

        approved_embed.description = message.content

        for field in original_embed.fields:
            approved_embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )

        if original_embed.image:
            approved_embed.set_image(url=original_embed.image.url)

        guild = bot.get_guild(GUILD_ID)
        user = guild.get_member(payload.user_id)

        approved_embed.set_footer(
            text=f"Approved by {user.display_name}"
        )

        await vouches_channel.send(embed=approved_embed)
        await message.delete()

    elif emoji == DECLINE_EMOJI:

        processed_messages.add(message.id)
        await message.delete()


# ---------------- TOKEN ----------------
BOT_TOKEN = os.getenv("TOKEN")

if not BOT_TOKEN:
    print("ERROR: TOKEN not found.")
    exit()

bot.run(BOT_TOKEN)
