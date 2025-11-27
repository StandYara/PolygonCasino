import sqlite3
import hashlib
import os


def get_db_connection():
    conn = sqlite3.connect('database/casino.db')
    conn.row_factory = sqlite3.Row
    return conn


# В db.py в функцию init_db() добавляем новую таблицу
def init_db():
    if not os.path.exists('database'):
        os.makedirs('database')

    conn = get_db_connection()

    # Таблица пользователей (ОБНОВЛЕНА - добавлено поле avatar)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            avatar TEXT DEFAULT 'avatar1.png',
            balance INTEGER DEFAULT 1000,
            is_banned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Проверяем существование поля avatar и добавляем если его нет
    try:
        conn.execute('SELECT avatar FROM users LIMIT 1')
    except sqlite3.OperationalError:
        # Поле avatar не существует, добавляем его
        conn.execute('ALTER TABLE users ADD COLUMN avatar TEXT DEFAULT "avatar1.png"')
        print("Добавлено поле avatar в таблицу users")

    # Таблица инвентаря
    conn.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            skin_id INTEGER NOT NULL,
            skin_name TEXT NOT NULL,
            skin_image TEXT NOT NULL,
            skin_price INTEGER NOT NULL,
            acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Таблица ежедневных наград
    conn.execute('''
        CREATE TABLE IF NOT EXISTS daily_rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reward_day INTEGER NOT NULL,
            reward_amount INTEGER NOT NULL,
            claimed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, reward_day)
        )
    ''')

    # Таблица квестов
    conn.execute('''
        CREATE TABLE IF NOT EXISTS quests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            quest_type TEXT NOT NULL,
            target_value INTEGER NOT NULL,
            reward_amount INTEGER NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Таблица прогресса квестов
    conn.execute('''
        CREATE TABLE IF NOT EXISTS quest_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            quest_id INTEGER NOT NULL,
            current_value INTEGER DEFAULT 0,
            is_completed INTEGER DEFAULT 0,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (quest_id) REFERENCES quests (id),
            UNIQUE(user_id, quest_id)
        )
    ''')

    # Таблица статистики пользователей
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            last_login DATE,
            consecutive_logins INTEGER DEFAULT 0,
            total_cases_opened INTEGER DEFAULT 0,
            total_plane_games INTEGER DEFAULT 0,
            total_mines_games INTEGER DEFAULT 0,
            total_safe_cells INTEGER DEFAULT 0,
            total_crafts INTEGER DEFAULT 0,
            total_upgrades INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id)
        )
    ''')

    # НОВАЯ ТАБЛИЦА: Использование бесплатных кейсов
    conn.execute('''
        CREATE TABLE IF NOT EXISTS free_case_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            case_id INTEGER NOT NULL,
            used_date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id),
            UNIQUE(user_id, case_id, used_date)
        )
    ''')

    # Создаем уникальный индекс для предотвращения дублирования прогресса квестов
    conn.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_quest_progress_user_quest 
        ON quest_progress (user_id, quest_id)
    ''')

    # Создаем индекс для бесплатных кейсов
    conn.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_free_case_usage_user_case_date 
        ON free_case_usage (user_id, case_id, used_date)
    ''')

    # Создаем тестового пользователя
    try:
        password_hash = hashlib.sha256('123'.encode()).hexdigest()
        conn.execute(
            'INSERT OR IGNORE INTO users (username, password, avatar) VALUES (?, ?, ?)',
            ('test', password_hash, 'avatar1.png')
        )

        # Создаем пользователя Developer для админ панели
        conn.execute(
            'INSERT OR IGNORE INTO users (username, password, avatar, balance) VALUES (?, ?, ?, ?)',
            ('Developer', hashlib.sha256('admin123'.encode()).hexdigest(), 'avatar1.png', 1000000)
        )
    except sqlite3.IntegrityError:
        pass

    # Создаем базовые квесты (ИСПРАВЛЕНИЕ: используем INSERT OR IGNORE)
    base_quests = [
        (1, 'Открыватель кейсов', 'Откройте 5 кейсов любого типа', 'open_cases', 5, 500),
        (2, 'Пилот-испытатель', 'Сыграйте 3 раза в игру "Самолет"', 'play_plane', 3, 300),
        (3, 'Сапер-новичок', 'Откройте 10 безопасных клеток в игре "Сапер"', 'open_safe_cells', 10, 400),
        (4, 'Мастер крафта', 'Скрафтите 2 скина', 'craft_skins', 2, 600),
        (5, 'Улучшатель', 'Улучшите 1 скин', 'upgrade_skin', 1, 800),
        (6, 'Ежедневный игрок', 'Зайдите в игру 3 дня подряд', 'consecutive_logins', 3, 1000)
    ]

    for quest in base_quests:
        conn.execute(
            'INSERT OR IGNORE INTO quests (id, title, description, quest_type, target_value, reward_amount) VALUES (?, ?, ?, ?, ?, ?)',
            quest
        )

    # Очищаем возможные дубликаты в quest_progress (ИСПРАВЛЕНИЕ)
    conn.execute('''
        DELETE FROM quest_progress 
        WHERE rowid NOT IN (
            SELECT MIN(rowid) 
            FROM quest_progress 
            GROUP BY user_id, quest_id
        )
    ''')

    # Таблица временных кейсов
    conn.execute('''
            CREATE TABLE IF NOT EXISTS timed_cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (case_id) REFERENCES quests (id)
            )
        ''')

    # Добавляем тестовые временные кейсы
    from datetime import datetime, timedelta

    # Хеллоуинские кейсы (активны 7 дней)
    halloween_end = datetime.now() + timedelta(days=7)
    # Зимние кейсы (активны 30 дней)
    winter_end = datetime.now() + timedelta(days=30)

    timed_cases = [
        (19, datetime.now().strftime('%Y-%m-%d'), halloween_end.strftime('%Y-%m-%d'), 1),
        (20, datetime.now().strftime('%Y-%m-%d'), halloween_end.strftime('%Y-%m-%d'), 1),
        (21, datetime.now().strftime('%Y-%m-%d'), halloween_end.strftime('%Y-%m-%d'), 1),
        (22, datetime.now().strftime('%Y-%m-%d'), winter_end.strftime('%Y-%m-%d'), 1),
        (23, datetime.now().strftime('%Y-%m-%d'), winter_end.strftime('%Y-%m-%d'), 1),
        (24, datetime.now().strftime('%Y-%m-%d'), winter_end.strftime('%Y-%m-%d'), 1)
    ]

    for case in timed_cases:
        conn.execute(
            'INSERT OR IGNORE INTO timed_cases (case_id, start_date, end_date, is_active) VALUES (?, ?, ?, ?)',
            case
        )

    conn.commit()
    conn.close()


def get_user_by_username(username):
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ?', (username,)
    ).fetchone()
    conn.close()
    return user


def create_user(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db_connection()
    try:
        conn.execute(
            'INSERT INTO users (username, password, avatar) VALUES (?, ?, ?)',
            (username, password_hash, 'avatar1.png')
        )
        conn.commit()
        result = True
    except sqlite3.IntegrityError:
        result = False
    conn.close()
    return result


def verify_user(username, password):
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?',
        (username, password_hash)
    ).fetchone()
    conn.close()
    return user


def get_user_balance(user_id):
    conn = get_db_connection()
    balance = conn.execute(
        'SELECT balance FROM users WHERE id = ?', (user_id,)
    ).fetchone()
    conn.close()
    return balance[0] if balance else 0


def update_user_balance(user_id, new_balance):
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET balance = ? WHERE id = ?',
        (new_balance, user_id)
    )
    conn.commit()
    conn.close()


def add_skin_to_inventory(user_id, skin_data):
    conn = get_db_connection()
    conn.execute(
        'INSERT INTO inventory (user_id, skin_id, skin_name, skin_image, skin_price) VALUES (?, ?, ?, ?, ?)',
        (user_id, skin_data['id'], skin_data['name'], skin_data['image'], skin_data['price'])
    )
    conn.commit()
    conn.close()


def get_user_inventory(user_id):
    conn = get_db_connection()
    inventory = conn.execute(
        'SELECT * FROM inventory WHERE user_id = ? ORDER BY acquired_at DESC', (user_id,)
    ).fetchall()
    conn.close()
    return inventory


def remove_skin_from_inventory(user_id, skin_id):
    conn = get_db_connection()
    # Получаем цену скина перед удалением
    skin = conn.execute(
        'SELECT skin_price FROM inventory WHERE user_id = ? AND id = ?', (user_id, skin_id)
    ).fetchone()

    if skin:
        conn.execute(
            'DELETE FROM inventory WHERE user_id = ? AND id = ?', (user_id, skin_id)
        )
        conn.commit()
        conn.close()
        return skin['skin_price']
    conn.close()
    return 0


def get_quest_progress(user_id, quest_id):
    """Получить прогресс квеста для пользователя"""
    conn = get_db_connection()
    progress = conn.execute(
        'SELECT * FROM quest_progress WHERE user_id = ? AND quest_id = ?',
        (user_id, quest_id)
    ).fetchone()
    conn.close()
    return progress


def update_quest_progress(user_id, quest_id, current_value, is_completed=False):
    """Обновить прогресс квеста (ИСПРАВЛЕННАЯ ВЕРСИЯ)"""
    conn = get_db_connection()

    # Используем INSERT OR REPLACE для предотвращения дублирования
    conn.execute('''
        INSERT OR REPLACE INTO quest_progress 
        (user_id, quest_id, current_value, is_completed, completed_at) 
        VALUES (?, ?, ?, ?, CASE WHEN ? = 1 THEN CURRENT_TIMESTAMP ELSE NULL END)
    ''', (user_id, quest_id, current_value, 1 if is_completed else 0, 1 if is_completed else 0))

    conn.commit()
    conn.close()