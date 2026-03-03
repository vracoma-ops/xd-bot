import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import os

# ------------------- CONFIG -------------------
GUILD_ID = 948971532431015976
CONFIG_CHANNEL_ID = 1478282165618737266
VOUCHES_CHANNEL_ID = 1478334777533927456

ADMIN_ID = 458624557763526666  # Your Discord ID

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

@bot.event
async def on_ready():
    print(f"[V1x Vouch] Logged in as {bot.user} ✅")
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print("Slash commands synced!")

@tree.command(
    name="vouch",
    description="Submit a vouch",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    seller="Seller's name",
    product="Product/service bought",
    quantity="Quantity purchased",
    proof="Attach proof image (png, jpg, jpeg)"
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
        await interaction.followup.send("⚠ Config channel not found.", ephemeral=True)
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

@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return
    if reaction.message.channel.id != CONFIG_CHANNEL_ID:
        return
    if user.id != ADMIN_ID:
        return
    if reaction.message.id in processed_messages:
        return
    if not reaction.message.embeds:
        return

    vouches_channel = bot.get_channel(VOUCHES_CHANNEL_ID)
    if not vouches_channel:
        return

    original_embed = reaction.message.embeds[0]

    if str(reaction.emoji) == APPROVE_EMOJI:
        processed_messages.add(reaction.message.id)
        date_now = datetime.now().strftime("%d-%m-%Y")

        approved_embed = discord.Embed(
            title=f"New Vouch ({date_now})",
            color=discord.Color.green()
        )

        approved_embed.description = reaction.message.content

        for field in original_embed.fields:
            approved_embed.add_field(
                name=field.name,
                value=field.value,
                inline=field.inline
            )

        if original_embed.image.url:
            approved_embed.set_image(url=original_embed.image.url)

        approved_embed.set_footer(
            text=f"Approved by {user.display_name}"
        )

        await vouches_channel.send(embed=approved_embed)
        await reaction.message.delete()

    elif str(reaction.emoji) == DECLINE_EMOJI:
        processed_messages.add(reaction.message.id)
        await reaction.message.delete()

BOT_TOKEN = os.getenv("TOKEN")
bot.run(BOT_TOKEN)