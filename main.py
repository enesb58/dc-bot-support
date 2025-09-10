import os
import aiohttp
import aiomysql
from datetime import datetime, timezone
import discord
from discord.ext import commands
from discord import app_commands
from discord.app_commands import Choice
from discord.ui import View, Button, Modal, TextInput, Select, UserSelect
from discord import SelectOption
from flask import Flask
from threading import Thread
pool = None
# ------------------- Keep Alive Webserver -------------------
app = Flask('')
@app.route('/')
def home():
    return "✅ Bot is alive!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(target=run)
    t.start()
# ------------------- Config -------------------
GUILD_ID = 1409557290918477826
FIVEM_API = os.getenv("FIVEM_API") or "http://94.130.130.24:3024/refund"
# Moderation roles allowed
ALLOWED_ROLES = {
    1409557291329392748,
}
UNBAN_ROLES = {
    1409557291329392748,
}
LOG_CHANNELS = {
    "ban": 1409557293283934247,
    "kick": 1409557293283934247,
    "warn": 1409557293283934247,
    "unban": 1409557293283934247,
}
TICKET_CATEGORY_ID = 1409228873438199989
TICKET_STAFF_ROLES = {1409557291329392744}
TICKET_LOG_CHANNEL_ID = 1409557293283934247
REFUND_ROLE_ID = 1414363765272477818
REFUND_LOG_CHANNEL_ID = 1409557293283934247  # Assume same as other logs
# ------------------- Bot -------------------
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)
bot.role_embed_data = {}  # Storage for role embeds
# ------------------- Database Helpers -------------------
async def get_refunds(discord_id):
    if pool is None:
        return []
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM ld_refunds WHERE discord_id = %s ORDER BY id DESC", (discord_id,))
            return await cur.fetchall()
async def get_refund(refund_id):
    if pool is None:
        return None
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute("SELECT * FROM ld_refunds WHERE id = %s", (refund_id,))
            results = await cur.fetchall()
            return results[0] if results else None
# ------------------- Events -------------------
@bot.event
async def on_ready():
    print(f"✅ Bot ingelogd als {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🌐 Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as e:
        print(f"❌ Fout bij sync: {e}")
    global pool
    try:
        pool = await aiomysql.create_pool(
            host=os.getenv('DB_HOST'),
            port=int(os.getenv('DB_PORT', '3306')),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            db=os.getenv('DB_NAME'),
            autocommit=True
        )
        print("✅ Connected to MySQL database")
    except Exception as e:
        print(f"❌ Failed to connect to MySQL: {e}")
# ------------------- Embed Modal -------------------
class EmbedModal(Modal, title="Maak een Embed"):
    titel = TextInput(label="Titel", style=discord.TextStyle.short, placeholder="Bijv. Mededeling", required=True, max_length=100)
    beschrijving = TextInput(label="Beschrijving", style=discord.TextStyle.paragraph, placeholder="Tekst die in de embed verschijnt", required=True, max_length=2000)
    kleur = TextInput(label="Kleur (hex of none)", style=discord.TextStyle.short, placeholder="#2ecc71", required=False, max_length=10)
    async def on_submit(self, interaction: discord.Interaction):
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()
        embed = discord.Embed(title=self.titel.value, description=self.beschrijving.value, color=color)
        embed.set_footer(text=f"Gemaakt door {interaction.user}")
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.", ephemeral=True)
            return
        options = [SelectOption(label=ch.name, value=str(ch.id)) for ch in guild.text_channels[:25]]
        class ChannelSelect(View):
            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(content="Kanaal niet gevonden.", view=None)
                    return
                await kanaal.send(embed=embed)
                await select_interaction.response.edit_message(content=f"✅ Embed gestuurd naar {kanaal.mention}", view=None)
        await interaction.response.send_message("Kies een kanaal voor je embed:", view=ChannelSelect(), ephemeral=True)
@bot.tree.command(name="embed", description="Maak een embed via formulier", guild=discord.Object(id=GUILD_ID))
async def embed_cmd(interaction: discord.Interaction):
    allowed_roles = {1358184251471822947}
    if not any(r.id in allowed_roles for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit commando.", ephemeral=True)
        return
    await interaction.response.send_modal(EmbedModal())
# ------------------- Role Embed Modal -------------------
class RoleEmbedModal(Modal, title="Maak een Role Embed"):
    titel = TextInput(
        label="Titel", style=discord.TextStyle.short,
        placeholder="Bijv. Kies je rol", required=True, max_length=100
    )
    beschrijving = TextInput(
        label="Beschrijving (embed tekst)", style=discord.TextStyle.paragraph,
        placeholder="Tekst die in de role-embed verschijnt", required=True, max_length=4000
    )
    mapping = TextInput(
        label="Mapping (emoji:role_id of emoji:RoleName)", style=discord.TextStyle.short,
        placeholder="Bijv: ✅:1402417593419305060, 🎮:Gamer", required=True, max_length=200
    )
    thumbnail = TextInput(
        label="Thumbnail (URL of 'serverlogo')", style=discord.TextStyle.short,
        placeholder="https://example.com/thumb.png of 'serverlogo'", required=False, max_length=200
    )
    kleur = TextInput(
        label="Kleur (hex of none)", style=discord.TextStyle.short,
        placeholder="#2ecc71", required=False, max_length=10
    )
    async def on_submit(self, interaction: discord.Interaction):
        kleur_input = self.kleur.value or "#2ecc71"
        if kleur_input.lower() == "none":
            color = discord.Color.default()
        else:
            try:
                color = discord.Color(int(kleur_input.strip("#"), 16))
            except:
                color = discord.Color.default()
        embed = discord.Embed(title=self.titel.value, description=self.beschrijving.value, color=color)
        if self.thumbnail.value:
            if self.thumbnail.value.lower() == "serverlogo" and interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            else:
                embed.set_thumbnail(url=self.thumbnail.value)
        elif interaction.guild.icon:
            embed.set_thumbnail(url=interaction.guild.icon.url)
        if interaction.guild.icon:
            embed.set_footer(text=f"Gemaakt door {interaction.guild.name}", icon_url=interaction.guild.icon.url)
        else:
            embed.set_footer(text=f"Gemaakt door {interaction.guild.name}")
        raw_map = {}
        for part in self.mapping.value.split(","):
            if ":" in part:
                emoji_text, role_part = part.split(":", 1)
                emoji_text = emoji_text.strip()
                role_part = role_part.strip()
                if emoji_text and role_part:
                    raw_map[emoji_text] = role_part
        if not raw_map:
            await interaction.response.send_message(
                "Geen geldige mapping gevonden. Gebruik format emoji:role_id of emoji:RoleName",
                ephemeral=True
            )
            return
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("Kon guild niet vinden.", ephemeral=True)
            return
        options = [SelectOption(label=ch.name, value=str(ch.id)) for ch in guild.text_channels[:25]]
        class ChannelSelect(View):
            @discord.ui.select(placeholder="Kies een kanaal", options=options)
            async def select_callback(self, select_interaction: discord.Interaction, select: Select):
                kanaal_id = int(select.values[0])
                kanaal = guild.get_channel(kanaal_id)
                if kanaal is None:
                    await select_interaction.response.edit_message(content="Kanaal niet gevonden.", view=None)
                    return
                message = await kanaal.send(embed=embed)
                normalized_map = {}
                for emoji_text, role_part in raw_map.items():
                    role_id = None
                    if role_part.isdigit():
                        try:
                            role_id = int(role_part)
                            role_obj = guild.get_role(role_id)
                            if role_obj is None:
                                try:
                                    role_obj = await guild.fetch_role(role_id)
                                except:
                                    role_obj = None
                            if role_obj is None:
                                role_id = None
                        except:
                            role_id = None
                    else:
                        role_obj = discord.utils.get(guild.roles, name=role_part)
                        if role_obj:
                            role_id = role_obj.id
                    try:
                        await message.add_reaction(emoji_text)
                        if role_id:
                            normalized_map[str(emoji_text)] = role_id
                    except Exception as e:
                        print(f"Kon emoji niet toevoegen ({emoji_text}): {e}")
                bot.role_embed_data = getattr(bot, "role_embed_data", {})
                bot.role_embed_data[message.id] = normalized_map
                await select_interaction.response.edit_message(
                    content=f"✅ Role embed gestuurd naar {kanaal.mention}\nOpgeslagen mappings: {len(normalized_map)}",
                    view=None
                )
        await interaction.response.send_message("Kies een kanaal voor je role embed:", view=ChannelSelect(), ephemeral=True)
@bot.tree.command(
    name="roleembed",
    description="Maak een role embed (alleen bepaalde rollen mogen dit)",
    guild=discord.Object(id=GUILD_ID)
)
async def roleembed(interaction: discord.Interaction):
    allowed_roles = {1409557291329392748}
    if not any(r.id in allowed_roles for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit commando.", ephemeral=True)
        return
    await interaction.response.send_modal(RoleEmbedModal())
# ------------------- Reaction -> Roles -------------------
async def handle_reaction(payload: discord.RawReactionActionEvent, add=True):
    emoji_map = getattr(bot, "role_embed_data", {}).get(payload.message_id)
    if not emoji_map:
        return
    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return
    member = guild.get_member(payload.user_id)
    if member is None:
        try:
            member = await guild.fetch_member(payload.user_id)
        except:
            return
    if member.bot:
        return
    role_id = emoji_map.get(str(payload.emoji))
    if role_id:
        role = guild.get_role(role_id)
        if role:
            try:
                if add:
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)
            except Exception as e:
                print(f"Kon rol niet {'toevoegen' if add else 'verwijderen'}: {e}")
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    await handle_reaction(payload, add=True)
@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    await handle_reaction(payload, add=False)
# ------------------- Helpers -------------------
async def try_send_dm(user: discord.abc.Messageable, content: str):
    try:
        await user.send(content)
        return True
    except Exception:
        return False
def make_action_dm(guild_name: str, actie: str, reden: str, moderator: str):
    return (
        f"Je bent {actie} in {guild_name}.\n"
        f"Reden: {reden}\n"
        f"Door: {moderator}\n"
        f"Tijd: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
def make_refund_dm(user: discord.User, refund_type: str, item: str = None, amount: int = None, weapon: str = None, ammo: int = None):
    message = f"🎉 Je hebt een nieuwe refund ontvangen op {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}!\n\n"
    type_map = {'item': 'Item', 'weapon': 'Wapen', 'money': 'Geld', 'black_money': 'Zwart Geld'}
    message += f"Type: {type_map.get(refund_type, refund_type)}\n"
    if item:
        message += f"Item: {item} x{amount}\n"
    if weapon
