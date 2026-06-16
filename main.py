import os
import asyncio
from dotenv import load_dotenv
import discord
from discord import app_commands
import datetime

from database import Database, setupDatabase
from pipisa import Pipisa, channel_check, update_role

# ──────────── Загрузка токена из .env ────────────
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("Переменная окружения DISCORD_TOKEN не установлена")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True


class MyClient(discord.Client):
    def __init__(self, *, intents: discord.Intents):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.db = Database()
        self.setup_db = setupDatabase()
        self.pipisa = Pipisa()
        self.active_votes: dict[int, dict] = {}

    async def setup_hook(self):
        try:
            synced = await self.tree.sync()
            print(f"✅ Слэш-команды синхронизированы ({len(synced)}).")
        except Exception as e:
            print(f"❌ Ошибка синхронизации: {e}")

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        vote = self.active_votes.get(payload.message_id)
        if not vote:
            return
        if payload.user_id != vote['target'].id:
            return
        if str(payload.emoji) not in ('👍', '👎'):
            return
        vote['event'].set()


client = MyClient(intents=intents)


# ──────────── Событие готовности ────────────
@client.event
async def on_ready():
    print(f"✅ вошли как {client.user}")


# ──────────── Команда /dick_play ────────────
@client.tree.command(name="dick_play", description="Получить размер и обновить звание (12ч)")
async def dick_play(interaction: discord.Interaction):
    if not await channel_check(interaction, client.setup_db):
        return

    guild = interaction.guild
    user = interaction.user
    gid, uid = guild.id, user.id
    now = datetime.datetime.now(datetime.timezone.utc)
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    data = await client.db.get_sql(uid, gid)
    member = guild.get_member(uid) or await guild.fetch_member(uid)

    if data:
        size_total, last = data
        last_dt = datetime.datetime.strptime(last, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc)
        diff = now - last_dt
        if diff < datetime.timedelta(hours=12):
            rem = datetime.timedelta(hours=12) - diff
            h, r = divmod(rem.seconds, 3600)
            m, s = divmod(r, 60)
            return await interaction.response.send_message(f"⏳ Осталось {h}h {m}m {s}s")

    new = await client.pipisa.pipisa_rulet(-6, 15)
    try:
        await client.db.write_sql(uid, new, now_str, gid)
    except Exception as e:
        print(f"DB Error: {e}")
        return await interaction.response.send_message("⚠️ Ошибка записи в базу: место закончилось", ephemeral=True)

    size_total, _ = await client.db.get_sql(uid, gid)
    role_name = await update_role(member, size_total, guild)
    await interaction.response.send_message(
        f"🎮 {user.display_name} получил {new} см (всего {size_total} см). Звание: {role_name}"
    )


# ──────────── Команда /dick_get ────────────
@client.tree.command(name="dick_get", description="Посмотреть свой размер")
async def dick_get(interaction: discord.Interaction):
    if not await channel_check(interaction, client.setup_db):
        return

    data = await client.db.get_sql(interaction.user.id, interaction.guild.id)
    size = data[0] if data else 0
    await interaction.response.send_message(f"📜 Твой размер: {size} см")


# ──────────── Команда /top_dick ────────────
@client.tree.command(name="top_dick", description="Топ-10 игроков по размеру")
async def top_dick(interaction: discord.Interaction):
    if not await channel_check(interaction, client.setup_db):
        return

    await interaction.response.defer(ephemeral=True)
    top = await client.db.get_top(interaction.guild.id)
    if not top:
        return await interaction.followup.send("Нет данных", ephemeral=True)

    lines = [
        f"{i+1}. {(await client.fetch_user(uid)).display_name} — {sz} см"
        for i, (uid, sz) in enumerate(top)
    ]
    await interaction.followup.send("💪 **Топ-10:**\n" + "\n".join(lines), ephemeral=True)


# ──────────── Команда /droch ────────────
@client.tree.command(name="droch", description="Подрочить на челика")
@app_commands.describe(user="Цель")
async def droch(interaction: discord.Interaction, user: discord.User):
    if not await channel_check(interaction, client.setup_db):
        return

    gid = interaction.guild.id
    author = interaction.user
    a_size = (await client.db.get_sql(author.id, gid) or (0,))[0]
    t_size = (await client.db.get_sql(user.id, gid) or (0,))[0]

    caught = await client.pipisa.catchedDroch(a_size, t_size)
    msg = (
        f"{author.display_name} хотел подрочить на {user.mention}, но был пойман 😔"
        if caught else
        f"**{author.display_name}** подрочил на {user.mention} 💦"
    )
    await interaction.response.send_message(msg)


# ──────────── Команда /fuck ────────────
@client.tree.command(name="fuck", description="Выебать кого-то")
@app_commands.describe(user="Цель")
async def fuck(interaction: discord.Interaction, user: discord.User):
    if not await channel_check(interaction, client.setup_db):
        return

    author = interaction.user
    if author.id == user.id:
        return await interaction.response.send_message("Нельзя себе!", ephemeral=True)

    gid = interaction.guild.id
    a_size = (await client.db.get_sql(author.id, gid) or (0,))[0]
    t_size = (await client.db.get_sql(user.id, gid) or (0,))[0]

    try:
        dm = await user.create_dm()
        dm_msg = await dm.send(f"Вас пытается выебать **{author.display_name}**. 👍 или 👎?")
    except discord.Forbidden:
        return await interaction.response.send_message(f"**{author.display_name}** выебал {user.mention}", ephemeral=True)

    await dm_msg.add_reaction('👍')
    await dm_msg.add_reaction('👎')

    event = asyncio.Event()
    client.active_votes[dm_msg.id] = {
        'channel': interaction.channel,
        'author': author,
        'target': user,
        'message': dm_msg,
        'author_size': a_size,
        'target_size': t_size,
        'event': event,
    }

    await interaction.response.send_message("Запрос отправлен", ephemeral=True)

    try:
        await asyncio.wait_for(event.wait(), timeout=120)
    except asyncio.TimeoutError:
        pass

    vote = client.active_votes.pop(dm_msg.id, None)
    if not vote:
        return

    msg_obj = await vote['message'].channel.fetch_message(vote['message'].id)
    up_votes   = next((r.count - 1 for r in msg_obj.reactions if str(r.emoji) == '👍'), 0)
    down_votes = next((r.count - 1 for r in msg_obj.reactions if str(r.emoji) == '👎'), 0)

    if down_votes > up_votes and await client.pipisa.preventedFuck(vote['author_size'], vote['target_size']):
        result = f"{vote['target'].display_name} дал отпор {vote['author'].display_name}."
    else:
        result = f"{vote['author'].display_name} выебал {vote['target'].display_name}."

    await vote['channel'].send(result)

# Запуск бота
client.run(TOKEN)