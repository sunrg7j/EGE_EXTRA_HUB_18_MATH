import aiosqlite
import os

DB_PATH = "math18.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Пользователи
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                username   TEXT,
                full_name  TEXT,
                has_access INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        # Задачи
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                description TEXT NOT NULL,
                image_path  TEXT,          -- путь к картинке (фото задачи)
                solution    TEXT NOT NULL,
                solution_image TEXT,       -- путь к картинке разбора
                is_demo     INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now'))
            )
        """)
        # Платежи
        await db.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER,
                payment_id    TEXT UNIQUE,
                amount        INTEGER,
                status        TEXT DEFAULT 'pending',
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()

    await seed_demo_tasks()


async def seed_demo_tasks():
    """Добавляет демо-задачи если их нет"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM tasks WHERE is_demo=1")
        count = (await cur.fetchone())[0]
        if count == 0:
            demos = [
                (
                    "Демо №1 — Куб",
                    "В кубе ABCDA₁B₁C₁D₁ найдите угол между прямой AB₁ и плоскостью основания.",
                    None,
                    "Угол между AB₁ и основанием = arctan(a/a) = 45°.\n\n📐 Шаги:\n1. AB₁ — диагональ грани\n2. Проекция на основание = AB = a\n3. Высота = AA₁ = a\n4. tan(φ) = a/a = 1 → φ = 45°",
                    None,
                    1
                ),
                (
                    "Демо №2 — Пирамида",
                    "Правильная четырёхугольная пирамида, сторона основания 6, высота 4. Найдите угол между боковой гранью и основанием.",
                    None,
                    "Апофема = √(3²+4²) = 5\ntan(φ) = 4/3 → φ = arctan(4/3) ≈ 53.1°\n\n📐 Шаги:\n1. Апофема = расстояние от центра до середины ребра\n2. Центр основания до середины стороны = 6/2 = 3\n3. tan(φ) = высота / апофема = 4/3",
                    None,
                    1
                ),
            ]
            await db.executemany(
                "INSERT INTO tasks (title, description, image_path, solution, solution_image, is_demo) VALUES (?,?,?,?,?,?)",
                demos
            )
            await db.commit()


# ---- USER ----

async def get_or_create_user(user_id: int, username: str, full_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?,?,?)",
            (user_id, username, full_name)
        )
        await db.commit()


async def has_access(user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT has_access FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return bool(row and row[0])


async def grant_access(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE users SET has_access=1 WHERE user_id=?", (user_id,))
        await db.commit()


# ---- TASKS ----

async def get_demo_tasks():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, title FROM tasks WHERE is_demo=1 ORDER BY id")
        return await cur.fetchall()


async def get_all_tasks():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT id, title FROM tasks ORDER BY id")
        return await cur.fetchall()


async def get_task(task_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
        return await cur.fetchone()


async def add_task(title, description, image_path, solution, solution_image, is_demo=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tasks (title, description, image_path, solution, solution_image, is_demo) VALUES (?,?,?,?,?,?)",
            (title, description, image_path, solution, solution_image, is_demo)
        )
        await db.commit()


# ---- PAYMENTS ----

async def create_payment(user_id: int, payment_id: str, amount: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO payments (user_id, payment_id, amount) VALUES (?,?,?)",
            (user_id, payment_id, amount)
        )
        await db.commit()


async def confirm_payment(payment_id: str) -> int | None:
    """Подтверждает платёж, возвращает user_id"""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM payments WHERE payment_id=?", (payment_id,))
        row = await cur.fetchone()
        if row:
            await db.execute("UPDATE payments SET status='paid' WHERE payment_id=?", (payment_id,))
            await db.commit()
            return row[0]
    return None


# ---- STATS (для админа) ----

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        paid = (await (await db.execute("SELECT COUNT(*) FROM users WHERE has_access=1")).fetchone())[0]
        revenue = (await (await db.execute("SELECT COALESCE(SUM(amount),0) FROM payments WHERE status='paid'")).fetchone())[0]
        tasks = (await (await db.execute("SELECT COUNT(*) FROM tasks")).fetchone())[0]
        return users, paid, revenue, tasks
