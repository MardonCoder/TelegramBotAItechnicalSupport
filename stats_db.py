import aiosqlite
from datetime import datetime, timedelta
import asyncio

class StatsDB:
    def __init__(self, db_path="data/stats.db"):
        """Инициализация базы данных."""
        self.db_path = db_path
        self._cleaning_task = None  # Хранение фоновой задачи

    async def _execute(self, query, params=()):
        """Выполнение SQL-запроса."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(query, params)
            await db.commit()

    async def _fetchone(self, query, params=()):
        """Получение одной строки."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                return await cursor.fetchone()

    async def _fetchall(self, query, params=()):
        """Получение всех строк."""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                return await cursor.fetchall()

    async def init_db(self):
        """Создание таблицы, если её нет."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")  # Включение WAL-режима
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost REAL NOT NULL,
                    timestamp TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now', 'localtime'))
                )
            ''')
            await db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON stats(timestamp)")
            await db.commit()

        # Очищаем старые данные, если в БД уже есть записи
        existing_data = await self._fetchone("SELECT COUNT(*) FROM stats")
        if existing_data and existing_data[0] > 0:
            await self.clean_old_entries()

    async def clean_old_entries(self):
        """Удаление записей старше 30 дней."""
        one_month_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
        await self._execute("DELETE FROM stats WHERE timestamp < ?", (one_month_ago,))

    async def _periodic_clean(self):
        """Фоновая очистка каждые 24 часа."""
        while True:
            await asyncio.sleep(86400)  # 24 часа (1 день)
            await self.clean_old_entries()

    def start_cleaning(self):
        """Запуск периодической очистки в фоне (если не запущена)."""
        if not self._cleaning_task or self._cleaning_task.done():
            self._cleaning_task = asyncio.create_task(self._periodic_clean())

    async def add_entry(self, input_tokens: int, output_tokens: int, cost: float):
        """Добавление новой записи."""
        await self._execute("INSERT INTO stats (input_tokens, output_tokens, cost) VALUES (?, ?, ?)",
                            (input_tokens, output_tokens, cost))

    async def get_stats(self):
        """Получение общей статистики."""
        result = await self._fetchone("SELECT COUNT(*), SUM(input_tokens), SUM(output_tokens), SUM(cost) FROM stats")
        messages_answered = result[0] or 0
        total_input_tokens = result[1] or 0
        total_output_tokens = result[2] or 0
        total_cost = result[3] or 0.0
        return messages_answered, total_input_tokens, total_output_tokens, total_cost
