# database.py
import aiosqlite
from typing import Optional, Tuple, List

class Database:
    """
    Работа с per-guild таблицами.
    Для каждой гильдии создаётся таблица guild_<id> со столбцами:
      - id BIGINT PRIMARY KEY
      - size INTEGER
      - datetime DATETIME
    """

    def __init__(self, db_path: str = "sizes.db"):
        self.db_path = db_path

    def _table_name(self, guild_id: int) -> str:
        """
        Формируем имя таблицы для guild_id.
        Приведение к int защищает от SQL-инъекций в имени таблицы.
        """
        gid = int(guild_id)
        return f"guild_{gid}"

    async def ensure_table(self, guild_id: int) -> None:
        """
        Создаёт таблицу guild_<id>, если она ещё не существует.
        Вызывать перед любой операцией с таблицей этой гильдии.
        """
        table_name = self._table_name(guild_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id BIGINT PRIMARY KEY,
                    size INTEGER,
                    datetime DATETIME
                )
            """)
            await db.commit()

    async def write_sql(self, user_id: int, size: int, datetime_str: str, guild_id: int) -> None:
        """
        Записывает/обновляет размер игрока в таблице guild_<guild_id>.
        Если записи нет — вставляет новую, иначе увеличивает поле size и обновляет datetime.
        """
        await self.ensure_table(guild_id)
        table_name = self._table_name(guild_id)

        async with aiosqlite.connect(self.db_path) as db:
            # Смотрим, есть ли уже запись для пользователя
            async with db.execute(f"SELECT size FROM {table_name} WHERE id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()

            if row is None:
                # Вставляем новую запись
                await db.execute(
                    f"INSERT INTO {table_name} (id, size, datetime) VALUES (?, ?, ?)",
                    (user_id, size, datetime_str)
                )
            else:
                # Обновляем существующую запись — накапливаем size
                await db.execute(
                    f"UPDATE {table_name} SET size = size + ?, datetime = ? WHERE id = ?",
                    (size, datetime_str, user_id)
                )

            await db.commit()

    async def get_sql(self, user_id: int, guild_id: int) -> Optional[Tuple[int, str]]:
        """
        Возвращает кортеж (size, datetime) для пользователя в конкретной гильдии,
        либо None, если записи нет.
        """
        await self.ensure_table(guild_id)
        table_name = self._table_name(guild_id)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT size, datetime FROM {table_name} WHERE id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return tuple(row) if row else None

    async def get_top(self, guild_id: int, limit: int = 10) -> List[Tuple[int, int]]:
        """
        Возвращает список (id, size) — топ `limit` пользователей по size для guild_id.
        Пустой список, если данных нет.
        """
        await self.ensure_table(guild_id)
        table_name = self._table_name(guild_id)

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                f"SELECT id, size FROM {table_name} ORDER BY size DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [(int(r[0]), int(r[1])) for r in rows] if rows else []


