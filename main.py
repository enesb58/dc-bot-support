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
REFUND_LOG_CHANNEL_ID = 1415401929106002061  # Assume same as other logs
# ------------------- Bot -------------------
intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="/", intents=intents)
bot.role_embed_data = {}  # Storage 
for role embeds
# ------------------- Database Helpers -------------------

async def item_autocomplete(interaction: discord.Interaction, current: str):
    if pool is None:
        return []
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                query = "SELECT `name` FROM `ld_items` WHERE `name` LIKE %s LIMIT 25"
                await cur.execute(query, (f"%{current}%",))
                items = await cur.fetchall()
                return [
                    app_commands.Choice(name=item[0], value=item[0])
                    for item in items
                ]
    except Exception as e:
        print(f"Error during autocomplete: {e}")
        return []

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
        synced 
= await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
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
    titel = TextInput(label="Titel", style=discord.TextStyle.short, placeholder="Bijv.
Mededeling", required=True, max_length=100)
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
            await 
interaction.response.send_message("Kon guild niet vinden.", ephemeral=True)
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
    titel = 
TextInput(
        label="Titel", style=discord.TextStyle.short,
        placeholder="Bijv.
Kies je rol", required=True, max_length=100
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
                "Geen geldige mapping gevonden.
Gebruik format emoji:role_id of emoji:RoleName",
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
    emoji_map = 
getattr(bot, "role_embed_data", {}).get(payload.message_id)
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
# ------------------- Moderatie Modal -------------------
class ModeratieModal(Modal, title="Reden"):
    reden = TextInput(label="Reden", style=discord.TextStyle.paragraph, placeholder="Geef een reden", required=True)
 
   def __init__(self, view_ref):
        super().__init__()
        self.view_ref = view_ref
    async def on_submit(self, interaction: discord.Interaction):
        view = self.view_ref
        action = view.actie
        guild = interaction.guild
        moderator = interaction.user
        try:
            if action in {"ban", "kick", "warn"}:
    
            member: discord.Member = view.target_member
                if member is None:
                    await interaction.response.send_message("❌ Geen doelwit geselecteerd.", ephemeral=True)
                    return
                me = guild.me
   
             if action == "ban" and not me.guild_permissions.ban_members:
                    await interaction.response.send_message("❌ Bot mist 'Ban Members' permissie.", ephemeral=True)
                    return
                if action == "kick" and not me.guild_permissions.kick_members:
            
        await interaction.response.send_message("❌ Bot mist 'Kick Members' permissie.", ephemeral=True)
                    return
                if member == me:
                    await interaction.response.send_message("❌ Kan de bot niet modereren.", ephemeral=True)
                   
 return
                if member.top_role >= me.top_role:
                    await interaction.response.send_message("❌ Kan deze gebruiker niet modereren: hogere of gelijke rol dan de bot.", ephemeral=True)
                    return
                dm_text = make_action_dm(guild.name if guild else "de server", action.upper(), self.reden.value, 
moderator.mention)
                dm_ok = await try_send_dm(member, dm_text)
                if action == "ban":
                    await member.ban(reason=self.reden.value)
                elif action == "kick":
                    await 
member.kick(reason=self.reden.value)
                elif action == "warn":
                    pass  # Placeholder for persistent warn store
                log_id = LOG_CHANNELS.get(action)
                if log_id:
                   
 log_chan = guild.get_channel(log_id)
                    if log_chan:
                        emb = discord.Embed(
                            title=f"{action.capitalize()} uitgevoerd",
                     
       description=(
                                f"Gebruiker: {member} ({member.id})\n"
                                f"Reden: {self.reden.value}\n"
                          
      f"Door: {moderator.mention}\n"
                                f"DM verzonden: {'Ja' if dm_ok else 'Nee'}"
                            ),
                           
 color=discord.Color.red(),
                            timestamp=datetime.now(timezone.utc),
                        )
                        await log_chan.send(embed=emb)
                await interaction.response.send_message(f"✅ Actie {action} uitgevoerd op 
{member}.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Ongeldige actie.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot heeft onvoldoende permissies om deze actie uit te voeren.", ephemeral=True)
        except Exception as exc:
            await interaction.response.send_message(f"❌ Fout bij uitvoeren: {exc}", ephemeral=True)
# ------------------- Unban Modal -------------------
class 
UnbanModal(Modal, title="Unban gebruiker (ID)"):
    user_id = TextInput(label="User ID", style=discord.TextStyle.short, placeholder="Bijv.
123456789012345678", required=True)
    reden = TextInput(label="Reden (optioneel)", style=discord.TextStyle.paragraph, placeholder="Reden (optioneel)", required=False)
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        moderator = interaction.user
        if guild is None:
            await interaction.response.send_message("❌ Guild niet gevonden.", ephemeral=True)
            return
        if not guild.me.guild_permissions.ban_members:
          
  await interaction.response.send_message("❌ Bot mist 'Ban Members' permissie (nodig voor unban).", ephemeral=True)
            return
        try:
            uid = int(self.user_id.value.strip())
        except Exception:
            await interaction.response.send_message("❌ Ongeldige User ID.", ephemeral=True)
            return
        reason_text = self.reden.value or "Geen reden opgegeven"
  
      try:
            bans = await guild.bans()
        except TypeError:
            bans = [b async for b in guild.bans()]
        ban_entry = next((b for b in bans if b.user.id == uid), None)
        if ban_entry is None:
            await interaction.response.send_message("❌ Deze user ID is niet geband (of 
niet gevonden).", ephemeral=True)
            return
        try:
            await guild.unban(ban_entry.user, reason=reason_text)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Bot heeft geen permissie om te unbannen.", ephemeral=True)
            return
        except Exception as e:
           
 await interaction.response.send_message(f"❌ Unban faalde: {e}", ephemeral=True)
            return
        dm_text = make_action_dm(guild.name, "UNBAN", reason_text, moderator.mention)
        try_send = await try_send_dm(ban_entry.user, dm_text)
        log_id = LOG_CHANNELS.get("unban")
        if log_id:
            log_channel = guild.get_channel(log_id)
            if log_channel:
           
     emb = discord.Embed(
                    title="Unban uitgevoerd",
                    description=(
                        f"Gebruiker: {ban_entry.user} ({ban_entry.user.id})\n"
                        f"Reden: {reason_text}\n"
 
                       f"Door: {moderator.mention}\n"
                        f"DM verzonden: {'Ja' if try_send else 'Nee'}"
                    ),
                    color=discord.Color.green(),
      
              timestamp=datetime.now(timezone.utc),
                )
                await log_channel.send(embed=emb)
        await interaction.response.send_message(f"✅ Unbanned: {ban_entry.user} ({ban_entry.user.id})", ephemeral=True)
# ------------------- Moderatie View -------------------
class ModeratieView(View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=900.0)
        self.author = author
        self.target_member: discord.Member 
| None = None
        self.actie: str |
None = None
        self.reden: str |
None = None
        user_select = UserSelect(placeholder="Kies een gebruiker", min_values=1, max_values=1)
        user_select.callback = self._user_selected
        self.add_item(user_select)
        for label, style, attr in [
            ("Ban", discord.ButtonStyle.danger, "ban"),
            ("Kick", discord.ButtonStyle.primary, "kick"),
            ("Warn", discord.ButtonStyle.secondary, "warn"),
           
 ("Unban", discord.ButtonStyle.success, "unban"),
        ]:
            btn = Button(label=label, style=style)
            btn.callback = self.make_callback(attr)
            self.add_item(btn)
    async def _user_selected(self, interaction: discord.Interaction):
        try:
            sel_vals = interaction.data.get("values", [])
            if sel_vals:
    
            selected_id = int(sel_vals[0])
                selected = interaction.guild.get_member(selected_id) or await interaction.guild.fetch_member(selected_id)
            else:
                selected = None
        except Exception:
            selected = None
        if selected is None:
 
           await interaction.response.send_message("❌ Kon gebruiker niet vinden.", ephemeral=True)
            return
        self.target_member = selected
        await interaction.response.send_message(f"✅ Gebruiker gekozen: {self.target_member.mention}", ephemeral=True)
    def make_callback(self, actie: str):
        async def callback(interaction: discord.Interaction):
            permitted = UNBAN_ROLES if actie == "unban" else ALLOWED_ROLES
          
  if not any(r.id in permitted for r in interaction.user.roles):
                await interaction.response.send_message("❌ Je hebt hier geen toestemming voor.", ephemeral=True)
                return
            if actie == "unban":
                await interaction.response.send_modal(UnbanModal())
                return
  
          if self.target_member is None:
                await interaction.response.send_message("❌ Kies eerst een gebruiker.", ephemeral=True)
                return
            self.actie = actie
            await interaction.response.send_modal(ModeratieModal(self))
        return callback
@bot.tree.command(name="moderatie", description="Open het moderatie UI menu", guild=discord.Object(id=GUILD_ID))
async def moderatie(interaction: discord.Interaction):
    
if not any(r.id in (ALLOWED_ROLES | UNBAN_ROLES) for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toegang tot dit menu.", ephemeral=True)
        return
    await interaction.response.send_message("Moderatie menu:", view=ModeratieView(interaction.user), ephemeral=True)
# ------------------- Role Check -------------------
def has_allowed_role(interaction: discord.Interaction) -> bool:
    return any(r.id in ALLOWED_ROLES for r in interaction.user.roles)
def has_refund_role(interaction: discord.Interaction) -> bool:
    return any(r.id == REFUND_ROLE_ID for r in interaction.user.roles)
# ------------------- Debug Commands -------------------
@bot.tree.command(name="checkban", description="Check of een user ID geband is in deze server", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user_id="Discord user ID (alleen cijfers)")
async def checkban(interaction: discord.Interaction, 
user_id: str):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    try:
        uid = int(user_id.strip())
    except:
        await interaction.response.send_message("❌ Ongeldige ID — gebruik alleen cijfers.", ephemeral=True)
        return
    try:
        bans = await interaction.guild.bans()
    except TypeError:
    
    bans = [b async for b in interaction.guild.bans()]
    ban_entry = next((b for b in bans if b.user.id == uid), None)
    if ban_entry:
        reason = ban_entry.reason or "Geen reden opgegeven"
        emb = discord.Embed(
            title="User is geband",
            description=f"Gebruiker: {ban_entry.user} ({ban_entry.user.id})\nReden: {reason}",
            color=discord.Color.red()
    
    )
        await interaction.response.send_message(embed=emb, ephemeral=True)
    else:
        await interaction.response.send_message("❌ Deze user ID is niet geband in deze server.", ephemeral=True)
@bot.tree.command(name="listbans", description="Laat de laatste N bans zien (debug)", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(limit="Hoeveel bans tonen (max 25)")
async def listbans(interaction: discord.Interaction, limit: int = 10):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    if limit < 1 or limit > 
25:
        await interaction.response.send_message("❌ Limit tussen 1 en 25.", ephemeral=True)
        return
    try:
        bans = await interaction.guild.bans()
    except TypeError:
        bans = [b async for b in interaction.guild.bans()]
    if not bans:
        await interaction.response.send_message("🔎 Geen bans gevonden in deze server.", ephemeral=True)
        return
    lines = []
    for i, 
b in enumerate(bans[:limit], start=1):
        reason = b.reason or "Geen reden"
        lines.append(f"{i}.
{b.user} — {b.user.id} — {reason}")
    emb = discord.Embed(
        title=f"Laatst {min(limit,len(bans))} bans",
        description="\n".join(lines),
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=emb, ephemeral=True)
# ------------------- Clear Command -------------------
@bot.tree.command(name="clear", description="Verwijder berichten uit een kanaal", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="Aantal berichten om te verwijderen (of 'all')")
async def clear(interaction: discord.Interaction, amount: str):
    CLEAR_ALLOWED_ROLES = {1409557291329392745}
    if not any(r.id in CLEAR_ALLOWED_ROLES for r in interaction.user.roles):
        await interaction.response.send_message("❌ Je hebt geen toestemming om 
dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    channel = interaction.channel
    deleted = 0
    try:
        if amount.lower() == "all":
            await channel.purge(limit=None)
            await interaction.followup.send("🧹 Alle berichten in dit kanaal zijn verwijderd!", ephemeral=True)
            return
        else:
  
          num = int(amount)
            if num < 1 or num > 1000:
                await interaction.followup.send("❌ Je kan alleen tussen 1 en 1000 berichten verwijderen.", ephemeral=True)
                return
            deleted_msgs = await channel.purge(limit=num)
           
 deleted = len(deleted_msgs)
            await interaction.followup.send(f"🧹 {deleted} berichten verwijderd.", ephemeral=True)
    except ValueError:
        await interaction.followup.send("❌ Ongeldig aantal, gebruik een getal of 'all'.", ephemeral=True)
# ------------------- Refund Notification Embed -------------------
def build_refund_embed(refund_id, user, refund_type, item, amount, weapon, ammo):
    embed = discord.Embed(title="Refund Bevestigd", description=f"De refund voor {user.mention} is succesvol bevestigd.", color=discord.Color.green())
    embed.add_field(name="Refund Details", value=f"Is dit de refund die je aan {user.mention} wilt geven?")
    embed.add_field(name="Refund ID", value=str(refund_id))
    type_map = {'item': 'Item', 'weapon': 'Wapen', 
'money': 'Geld', 'black_money': 'Zwart Geld'}
    embed.add_field(name="Type", value=type_map.get(refund_type, refund_type))
    if item:
        embed.add_field(name="Item", value=item)
    if weapon:
        embed.add_field(name="Wapen", value=weapon)
    if amount:
        embed.add_field(name="Aantal", value=str(amount))
    if ammo:
        embed.add_field(name="Aantal", value=str(ammo))  # or "Ammo"
    embed.add_field(name="Hoe claim je je refund", value="1.
Ga in-game\n2. Open het refund menu met /refunds\n3. Claim je refund")
    return embed
# ------------------- Add Refund Command -------------------
@bot.tree.command(name="addrefund", description="Voeg een refund toe voor een gebruiker", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(
    user="De gebruiker",
    refund_type="Type refund (item, weapon, money, black_money)",
    item="Item naam (voor type item)",
    amount="Aantal (voor item, money, black_money)",
    weapon="Weapon naam (voor type weapon)",
    ammo="Ammo (voor weapon, optioneel)"
)
@app_commands.choices(refund_type=[
    Choice(name="Item", value="item"),
    Choice(name="Weapon", value="weapon"),
    Choice(name="Money", value="money"),
    Choice(name="Black Money", value="black_money"),
])
@app_commands.autocomplete(item=item_autocomplete, weapon=item_autocomplete)
async def addrefund(interaction: discord.Interaction, user: discord.User, 
refund_type: str, item: str = None, amount: int = None, weapon: str = None, ammo: int = None):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    if pool is None:
        await interaction.followup.send("❌ Geen verbinding met de database.", ephemeral=True)
        return
    # Validate input based on type
    if refund_type 
not in ['item', 'weapon', 'money', 'black_money']:
        await interaction.followup.send("❌ Ongeldig refund type.", ephemeral=True)
        return
    insert_item = None
    insert_amount = None
    insert_weapon = None
    insert_ammo = None
    if refund_type == 'item':
        if not item or not amount:
            await interaction.followup.send("❌ Item en amount vereist voor type 'item'.", ephemeral=True)
         
   return
        insert_item = item
        insert_amount = amount
    elif refund_type == 'weapon':
        if not weapon:
            await interaction.followup.send("❌ Weapon vereist voor type 'weapon'.", ephemeral=True)
            return
        insert_weapon = weapon
        insert_ammo = ammo or 0
    elif refund_type in 
['money', 'black_money']:
        if not amount:
            await interaction.followup.send("❌ Amount vereist voor type 'money' of 'black_money'.", ephemeral=True)
            return
        insert_amount = amount
        insert_ammo = 0
    description = f"{refund_type}"
    if item:
        description += f" {item}"
    if weapon:
        description 
+= f" {weapon}"
    if amount:
        description += f" x{amount}"
    if ammo:
        description += f" (ammo: {ammo})"
    class ConfirmationView(View):
        @discord.ui.select(placeholder="Bevestig de refund", options=[SelectOption(label="Bevestigen", value="confirm"), SelectOption(label="Annuleren", value="cancel")])
        async def select_callback(self, select_interaction: discord.Interaction, select: Select):
            if select.values[0] == "confirm":
                try:
 
                   async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
                    
            """
                                INSERT INTO ld_refunds (discord_id, refund_type, item, amount, weapon, ammo, status)
                                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
        
                        """,
                                (user.id, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                            )
           
                 refund_id = cur.lastrowid
                    # Send notification embed to the channel
                    embed = build_refund_embed(refund_id, user, refund_type, item, amount, weapon, ammo)
                    await interaction.channel.send(embed=embed)
      
              # Log
                    log_chan = interaction.guild.get_channel(REFUND_LOG_CHANNEL_ID)
                    if log_chan:
                        log_embed = discord.Embed(title="Refund Aangemaakt", description=f"Door {interaction.user.mention} voor {user.mention}: {description}\nID: {refund_id}", color=discord.Color.blue())
        
                await log_chan.send(embed=log_embed)
                    await select_interaction.response.edit_message(content=f"✅ Refund bevestigd.", view=None)
                except Exception as e:
                    await select_interaction.response.edit_message(content=f"❌ Fout bij bevestigen: {str(e)}", view=None)
            else:
  
              await select_interaction.response.edit_message(content="❌ Refund geannuleerd", view=None)
    await interaction.followup.send(f"Is dit de refund die je aan {user.mention} wilt geven?
{description}", view=ConfirmationView(), ephemeral=True)
# ------------------- Refund Annuleer Command -------------------
@bot.tree.command(name="refund_annuleer", description="Annuleer een refund via ID", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(refund_id="Refund ID")
async def refund_annuleer(interaction: discord.Interaction, refund_id: int):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    if pool is None:
        await interaction.followup.send("❌ Geen verbinding met de database.", ephemeral=True)
        return
    try:
        async 
with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE ld_refunds SET status = 'canceled', canceled_at = %s WHERE id = %s AND status = 'pending'", (datetime.now(timezone.utc), refund_id))
                if cur.rowcount == 0:
                    await interaction.followup.send("❌ Refund niet gevonden of al 
geclaimd/geannuleerd.", ephemeral=True)
                    return
        # Log
        log_chan = interaction.guild.get_channel(REFUND_LOG_CHANNEL_ID)
        if log_chan:
            log_embed = discord.Embed(title="Refund Geannuleerd", description=f"Door {interaction.user.mention}: Refund ID {refund_id}", color=discord.Color.red())
            await log_chan.send(embed=log_embed)
        await interaction.followup.send(f"✅ Refund ID {refund_id} geannuleerd.", ephemeral=True)
   
 except Exception as e:
        await interaction.followup.send(f"❌ Fout bij annuleren: {str(e)}", ephemeral=True)
# ------------------- Refund Informatie Gebruiker Command -------------------
@bot.tree.command(name="refund_informatie_gebruiker", description="Krijg informatie over refunds van een gebruiker", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="De gebruiker")
async def refund_informatie_gebruiker(interaction: discord.Interaction, user: discord.User):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    refunds = await get_refunds(user.id)
    if not refunds:
        await interaction.followup.send(f"Geen refunds 
voor {user.mention}.", ephemeral=True)
        return
    embed = discord.Embed(title=f"Refunds voor {user.name}", color=discord.Color.blue())
    for refund in refunds:
        desc = f"ID: {refund['id']}\nType: {refund['refund_type']}\nStatus: {refund['status']}"
        if refund['item']:
            desc += f"\nItem: {refund['item']} x{refund['amount']}"
        if refund['weapon']:
            desc += f"\nWapen: {refund['weapon']} (ammo: {refund['ammo']})"
        if refund['amount'] 
and not refund['item']:
            desc += f"\nAantal: {refund['amount']}"
        embed.add_field(name=f"Refund {refund['id']}", value=desc, inline=False)
    await interaction.followup.send(embed=embed, ephemeral=True)
# ------------------- Refund Informatie ID Command -------------------
@bot.tree.command(name="refund_informatie_id", description="Krijg informatie over een refund via ID", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(refund_id="Refund ID")
async def refund_informatie_id(interaction: discord.Interaction, refund_id: int):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    refund = await get_refund(refund_id)
 
   if not refund:
        await interaction.followup.send("Geen refund gevonden met dat ID.", ephemeral=True)
        return
    embed = discord.Embed(title=f"Refund {refund['id']}", color=discord.Color.blue())
    desc = f"Type: {refund['refund_type']}\nStatus: {refund['status']}\nDiscord ID: {refund['discord_id']}\nCreated: {refund['created_at']}"
    if refund['claimed_at']:
        desc += f"\nClaimed: {refund['claimed_at']}"
    if refund['canceled_at']:
        desc += f"\nCanceled: {refund['canceled_at']}"
    if refund['item']:
        desc += f"\nItem: {refund['item']} x{refund['amount']}"
    
if refund['weapon']:
        desc += f"\nWapen: {refund['weapon']} (ammo: {refund['ammo']})"
    if refund['amount'] and not refund['item']:
        desc += f"\nAantal: {refund['amount']}"
    embed.description = desc
    await interaction.followup.send(embed=embed, ephemeral=True)
# ------------------- Refund Geef Geld Command -------------------
@bot.tree.command(name="refund_geef_geld", description="Geef een refund in geld", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="De gebruiker", amount="Bedrag")
async def refund_geef_geld(interaction: discord.Interaction, user: discord.User, amount: int):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
 
   await interaction.response.defer(ephemeral=True)
    refund_type = 'money'
    insert_amount = amount
    insert_item = None
    insert_weapon = None
    insert_ammo = 0
    description = f"Geld x{amount}"
    class ConfirmationView(View):
        @discord.ui.select(placeholder="Bevestig de refund", options=[SelectOption(label="Bevestigen", value="confirm"), SelectOption(label="Annuleren", value="cancel")])
        async def select_callback(self, select_interaction: discord.Interaction, select: Select):
            if select.values[0] == "confirm":
           
     try:
                    async with pool.acquire() as conn:
                        async with conn.cursor() as cur:
                            await cur.execute(
              
                  """
                                INSERT INTO ld_refunds (discord_id, refund_type, item, amount, weapon, ammo, status)
                                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
  
                              """,
                                (user.id, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                            )
     
                       refund_id = cur.lastrowid
                    # Send notification embed to the channel
                    embed = build_refund_embed(refund_id, user, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                    await 
interaction.channel.send(embed=embed)
                    # Log
                    log_chan = interaction.guild.get_channel(REFUND_LOG_CHANNEL_ID)
                    if log_chan:
                        log_embed = discord.Embed(title="Refund Aangemaakt", description=f"Door {interaction.user.mention} voor {user.mention}: {description}\nID: {refund_id}", color=discord.Color.blue())
  
                      await log_chan.send(embed=log_embed)
                    await select_interaction.response.edit_message(content=f"✅ Refund bevestigd.", view=None)
                except Exception as e:
                    await select_interaction.response.edit_message(content=f"❌ Fout bij bevestigen: {str(e)}", view=None)
        
    else:
                await select_interaction.response.edit_message(content="❌ Refund geannuleerd", view=None)
    await interaction.followup.send(f"Is dit de refund die je aan {user.mention} wilt geven?
{description}", view=ConfirmationView(), ephemeral=True)
# ------------------- Refund Geef Item Command -------------------
@bot.tree.command(name="refund_geef_item", description="Geef een refund voor een item", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="De gebruiker", item="Item naam", amount="Aantal")
@app_commands.autocomplete(item=item_autocomplete)
async def refund_geef_item(interaction: discord.Interaction, user: discord.User, item: str, amount: int):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    refund_type = 'item'
    insert_item = item
    insert_amount = amount
    insert_weapon = None
    insert_ammo = 0
    
description = f"Item {item} x{amount}"
    class ConfirmationView(View):
        @discord.ui.select(placeholder="Bevestig de refund", options=[SelectOption(label="Bevestigen", value="confirm"), SelectOption(label="Annuleren", value="cancel")])
        async def select_callback(self, select_interaction: discord.Interaction, select: Select):
            if select.values[0] == "confirm":
                try:
                    async with pool.acquire() as conn:
        
                async with conn.cursor() as cur:
                            await cur.execute(
                                """
                   
             INSERT INTO ld_refunds (discord_id, refund_type, item, amount, weapon, ammo, status)
                                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
                                """,
       
                         (user.id, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                            )
                            refund_id = cur.lastrowid
            
        # Send notification embed to the channel
                    embed = build_refund_embed(refund_id, user, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                    await interaction.channel.send(embed=embed)
                    # Log
                
    log_chan = interaction.guild.get_channel(REFUND_LOG_CHANNEL_ID)
                    if log_chan:
                        log_embed = discord.Embed(title="Refund Aangemaakt", description=f"Door {interaction.user.mention} voor {user.mention}: {description}\nID: {refund_id}", color=discord.Color.blue())
                        await log_chan.send(embed=log_embed)
              
      await select_interaction.response.edit_message(content=f"✅ Refund bevestigd.", view=None)
                except Exception as e:
                    await select_interaction.response.edit_message(content=f"❌ Fout bij bevestigen: {str(e)}", view=None)
            else:
                await select_interaction.response.edit_message(content="❌ Refund geannuleerd", view=None)
    await interaction.followup.send(f"Is dit de refund die je aan {user.mention} 
wilt geven? {description}", view=ConfirmationView(), ephemeral=True)
# ------------------- Refund Geef Wapen Command -------------------
@bot.tree.command(name="refund_geef_wapen", description="Geef een refund voor een wapen", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="De gebruiker", weapon="Weapon naam", ammo="Ammo (optioneel)")
@app_commands.autocomplete(weapon=item_autocomplete)
async def refund_geef_wapen(interaction: discord.Interaction, user: discord.User, weapon: str, ammo: int = 0):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    refund_type = 'weapon'
    insert_weapon = weapon
    insert_ammo = ammo
    insert_item = None
    insert_amount 
= None
    description = f"Wapen {weapon} (ammo: {ammo})"
    class ConfirmationView(View):
        @discord.ui.select(placeholder="Bevestig de refund", options=[SelectOption(label="Bevestigen", value="confirm"), SelectOption(label="Annuleren", value="cancel")])
        async def select_callback(self, select_interaction: discord.Interaction, select: Select):
            if select.values[0] == "confirm":
                try:
                    async with pool.acquire() as conn:
  
                      async with conn.cursor() as cur:
                            await cur.execute(
                                """
             
                   INSERT INTO ld_refunds (discord_id, refund_type, item, amount, weapon, ammo, status)
                                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
                                """,
 
                               (user.id, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                            )
                            refund_id = cur.lastrowid
      
              # Send notification embed to the channel
                    embed = build_refund_embed(refund_id, user, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                    await interaction.channel.send(embed=embed)
                    # Log
          
          log_chan = interaction.guild.get_channel(REFUND_LOG_CHANNEL_ID)
                    if log_chan:
                        log_embed = discord.Embed(title="Refund Aangemaakt", description=f"Door {interaction.user.mention} voor {user.mention}: {description}\nID: {refund_id}", color=discord.Color.blue())
                        await log_chan.send(embed=log_embed)
        
            await select_interaction.response.edit_message(content=f"✅ Refund bevestigd.", view=None)
                except Exception as e:
                    await select_interaction.response.edit_message(content=f"❌ Fout bij bevestigen: {str(e)}", view=None)
            else:
                await select_interaction.response.edit_message(content="❌ Refund geannuleerd", view=None)
    await interaction.followup.send(f"Is dit 
de refund die je aan {user.mention} wilt geven? {description}", view=ConfirmationView(), ephemeral=True)
# ------------------- Refund Geef Zwartgeld Command -------------------
@bot.tree.command(name="refund_geef_zwartgeld", description="Geef een refund in zwart geld", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(user="De gebruiker", amount="Bedrag")
async def refund_geef_zwartgeld(interaction: discord.Interaction, user: discord.User, amount: int):
    if not has_refund_role(interaction):
        await interaction.response.send_message("❌ Je hebt geen permissie om dit commando te gebruiken.", ephemeral=True)
        return
    await interaction.response.defer(ephemeral=True)
    refund_type = 'black_money'
    insert_amount = amount
    insert_item = None
    insert_weapon = None
    insert_ammo = 
0
    description = f"Zwart Geld x{amount}"
    class ConfirmationView(View):
        @discord.ui.select(placeholder="Bevestig de refund", options=[SelectOption(label="Bevestigen", value="confirm"), SelectOption(label="Annuleren", value="cancel")])
        async def select_callback(self, select_interaction: discord.Interaction, select: Select):
            if select.values[0] == "confirm":
                try:
                    async with pool.acquire() as conn:
    
                    async with conn.cursor() as cur:
                            await cur.execute(
                                """
               
                 INSERT INTO ld_refunds (discord_id, refund_type, item, amount, weapon, ammo, status)
                                VALUES (%s, %s, %s, %s, %s, %s, 'pending')
                                """,
   
                             (user.id, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                            )
                            refund_id = cur.lastrowid
        
            # Send notification embed to the channel
                    embed = build_refund_embed(refund_id, user, refund_type, insert_item, insert_amount, insert_weapon, insert_ammo)
                    await interaction.channel.send(embed=embed)
                    # Log
            
        log_chan = interaction.guild.get_channel(REFUND_LOG_CHANNEL_ID)
                    if log_chan:
                        log_embed = discord.Embed(title="Refund Aangemaakt", description=f"Door {interaction.user.mention} voor {user.mention}: {description}\nID: {refund_id}", color=discord.Color.blue())
                        await log_chan.send(embed=log_embed)
          
          await select_interaction.response.edit_message(content=f"✅ Refund bevestigd.", view=None)
                except Exception as e:
                    await select_interaction.response.edit_message(content=f"❌ Fout bij bevestigen: {str(e)}", view=None)
            else:
                await select_interaction.response.edit_message(content="❌ Refund geannuleerd", view=None)
    await interaction.followup.send(f"Is dit de refund 
die je aan {user.mention} wilt geven? {description}", view=ConfirmationView(), ephemeral=True)
# ------------------- Ticket Modal -------------------
class TicketReasonModal(discord.ui.Modal, title="Ticket Reden en Info"):
    def __init__(self, ticket_type: str):
        super().__init__(timeout=None)
        self.ticket_type = ticket_type
        self.reason = discord.ui.TextInput(
            label="Reden van je ticket",
            placeholder="Beschrijf kort waarom je dit ticket opent...",
            style=discord.TextStyle.short,
   
         required=True,
            max_length=200
        )
        self.add_item(self.reason)
        self.info = discord.ui.TextInput(
            label="Extra informatie",
            placeholder="Voeg extra details toe zodat staff je sneller kan helpen.",
            style=discord.TextStyle.paragraph,
       
     required=False,
            max_length=1000
        )
        self.add_item(self.info)
    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)
        if not category or not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("❌ Ticket categorie niet gevonden!", ephemeral=True)
       
     return
        for ch in category.channels:
            if ch.name == f"ticket-{interaction.user.id}":
                await interaction.response.send_message(f"❌ Je hebt al een ticket: {ch.mention}", ephemeral=True)
                return
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
      
      interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
        }
        for rid in TICKET_STAFF_ROLES:
            role = guild.get_role(rid)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
        channel_name = f"{self.ticket_type.lower().replace(' ', '-')}-{interaction.user.id}"
        ticket_channel = await category.create_text_channel(
  
          name=channel_name,
            overwrites=overwrites
        )
        emb = discord.Embed(
            title=f"🎫 Ticket geopend - {self.ticket_type}",
            description=f"Door: {interaction.user.mention}\n\nReden: {self.reason.value}\n\nExtra info: {self.info.value if self.info.value else 'Geen extra info'}",
            color=discord.Color.blurple()
        )
  
      await ticket_channel.send(content=f"{interaction.user.mention} Ticket aangemaakt!", embed=emb, view=CloseTicketView())
        await interaction.response.send_message(f"✅ Ticket aangemaakt: {ticket_channel.mention}", ephemeral=True)
# ------------------- Dropdown Menu -------------------
class TicketDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Algemene Vragen", emoji="❓"),
            discord.SelectOption(label="Klachten (Spelers)", emoji="👤"),
            discord.SelectOption(label="Klachten (Staff)", emoji="🛑"),
            discord.SelectOption(label="Ingame Refund", 
emoji="💰"),
            discord.SelectOption(label="Unban Aanvraag (Discord)", emoji="💬"),
            discord.SelectOption(label="Unban Aanvraag (TX-Admin)", emoji="🖥️"),
            discord.SelectOption(label="Unban Aanvraag (Anticheat)", emoji="⚠️"),
            discord.SelectOption(label="Staff Sollicitatie", emoji="📝"),
            discord.SelectOption(label="Donaties", emoji="💎"),
        ]
        super().__init__(placeholder="📌 Kies een ticket type...", min_values=1, max_values=1, options=options)
    async 
def callback(self, interaction: discord.Interaction):
        ticket_type = self.values[0]
        await interaction.response.send_modal(TicketReasonModal(ticket_type))
# ------------------- Dropdown View -------------------
class TicketDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketDropdown())
# ------------------- Sluit-knop -------------------
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @discord.ui.button(label="❌ Sluit ticket", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not any(r.id in TICKET_STAFF_ROLES for r in interaction.user.roles):
 
           await interaction.response.send_message("❌ Alleen staff kan tickets sluiten.", ephemeral=True)
            return
        await interaction.channel.delete()
# ------------------- Ticket Setup Command -------------------
@bot.tree.command(name="ticketsetup", description="Plaats ticket systeem in dit kanaal", guild=discord.Object(id=GUILD_ID))
async def ticketsetup(interaction: discord.Interaction):
    if not has_allowed_role(interaction):
        await interaction.response.send_message("❌ Geen permissie.", ephemeral=True)
        return
    emb = discord.Embed(
        title="🎫 Tickets",
     
   description="Selecteer hieronder het type ticket dat je wilt openen.",
        color=discord.Color.blurple()
    )
    await interaction.channel.send(embed=emb, view=TicketDropdownView())
    await interaction.response.send_message("✅ Ticket systeem geplaatst!", ephemeral=True)
# ------------------- Error Handlers -------------------
@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    try:
        if interaction.response.is_done():
            await interaction.followup.send(f"❌ Er ging iets mis: {error}", ephemeral=True)
        else:
            await 
interaction.response.send_message(f"❌ Er ging iets mis: {error}", ephemeral=True)
    except:
        pass
    import traceback
    traceback.print_exception(type(error), error, error.traceback)
class SafeView(discord.ui.View):
    async def on_error(self, error: Exception, item: discord.ui.Item, interaction: discord.Interaction):
        try:
            if interaction.response.is_done():
                await interaction.followup.send("❌ Fout bij uitvoeren van deze knop/select.", ephemeral=True)
            else:
 
               await interaction.response.send_message("❌ Fout bij uitvoeren van deze knop/select.", ephemeral=True)
        except:
            pass
        import traceback
        traceback.print_exception(type(error), error, error.traceback)
# ------------------- Start Bot -------------------
print("Booting up...")
keep_alive()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ Geen Discord TOKEN gevonden in environment variables!")
else:
    bot.run(TOKEN)
