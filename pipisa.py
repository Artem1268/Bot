import random
import discord


ROLES_N = [
    "Пизда", "Пизденка", "Кастрированый", "Пиструнчик",
    "Пиструн", "Писюн", "Хуй",
    "Валына", "Хуище"
]


class Pipisa:
    async def pipisa_rulet(self, min_value: int, max_value: int) -> int:
        return random.randint(min_value, max_value)

    async def catchedDroch(self, first_size: int, second_size: int, max_diff: int = 30) -> bool:
        if first_size >= second_size:
            return False
        diff = second_size - first_size
        if diff >= max_diff:
            return True
        return random.random() < (diff / max_diff)

    async def preventedFuck(self, first_size: int, second_size: int, max_diff: int = 20) -> bool:
        if first_size > second_size:
            return False
        diff = second_size - first_size
        if diff >= max_diff:
            return True
        return random.random() < (diff / max_diff)


async def channel_check(interaction: discord.Interaction, setup_db) -> bool:
    """
    Проверяет:
      - Вызвана ли команда на сервере
      - Если для сервера задан настроенный канал — совпадает ли он с текущим
    """
    if interaction.guild is None:
        await interaction.response.send_message("❌ Не тот чат (только на сервере)", ephemeral=True)
        return False

    cfg = await setup_db.get_setup(interaction.guild.id)
    channel_id = None

    if cfg is None:
        channel_id = None
    elif isinstance(cfg, int):
        channel_id = cfg
    elif isinstance(cfg, (tuple, list)):
        channel_id = int(cfg[0]) if cfg else None
    else:
        try:
            channel_id = int(cfg)
        except Exception:
            try:
                channel_id = int(cfg[0])
            except Exception:
                channel_id = None

    if channel_id is None:
        return True

    if interaction.channel is None or interaction.channel.id != channel_id:
        await interaction.response.send_message("❌ Не тот чат. Используйте настроенный канал.", ephemeral=True)
        return False

    return True


async def update_role(member: discord.Member, cumulative_size: int, guild: discord.Guild) -> str:
    """Назначает роль участнику на основе cumulative_size."""
    roles_to_remove=[discord.utils.get(guild.roles, name=j) for j in ROLES_N]

    if len(roles_to_remove) <9 or None in roles_to_remove:
        print(roles_to_remove)
        return "Ошибка в ролях"

    if cumulative_size <= -5:
        role = roles_to_remove[0]
    elif -5 < cumulative_size < 0:
        role = roles_to_remove[1]
    elif cumulative_size == 0:
        role = roles_to_remove[2]
    elif cumulative_size <= 7:
        role = roles_to_remove[3]
    elif cumulative_size <= 15:
        role = roles_to_remove[4]
    elif cumulative_size <= 25:
        role = roles_to_remove[5]
    elif cumulative_size <= 35:
        role = roles_to_remove[6]
    elif cumulative_size < 45:
        role = roles_to_remove[7]
    else:
        role = roles_to_remove[8]

    to_remove = [r for r in member.roles if r in roles_to_remove]
    if to_remove:
        try:
            await member.remove_roles(*to_remove, reason="Обновление звания")
        except Exception as e:
            print(f"Ошибка при удалении ролей у {member}: {e}")

    if role:
        try:
            await member.add_roles(role, reason="Выдача звания")
            return role.name
        except Exception as e:
            print(f"Ошибка при добавлении роли {role.name} для {member}: {e}")
            return "Не удалось назначить роль"
    return "Роль не найдена"