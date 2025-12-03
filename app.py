from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from database.db import init_db, get_user_by_username, create_user, verify_user, get_user_balance, update_user_balance, \
    add_skin_to_inventory, get_user_inventory, remove_skin_from_inventory, get_db_connection
from utils.game_logic import get_case_skins, spin_roulette, SKINS_DATABASE, get_rarity_name

from datetime import datetime, timedelta
import random

import os

# Проверяем и создаем папки
for folder in ['database', 'static', 'templates']:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📁 Created folder: {folder}")

# Проверяем и создаем папки
for folder in ['database', 'static', 'templates']:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"📁 Created folder: {folder}")

app = Flask(__name__)
# Генерируем случайный ключ, если нет в настройках
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24).hex())

# Инициализация БД при запуске
with app.app_context():
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization error: {str(e)}")
        # Создаем папку database если нет
        import os
        if not os.path.exists('database'):
            os.makedirs('database')
        init_db()  # Пробуем еще раз


# Проверка авторизации для всех страниц
@app.before_request
def require_login():
    if request.endpoint and not request.endpoint.startswith('static') and not request.endpoint.startswith('auth_'):
        if 'user_id' not in session:
            return redirect(url_for('auth_login'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/cases')
def cases():
    return render_template('cases.html')


@app.route('/inventory')
def inventory():
    return render_template('inventory.html')


@app.route('/plane')
def plane():
    return render_template('plane.html')


@app.route('/upgrade')
def upgrade():
    return render_template('upgrade.html')


@app.route('/craft')
def craft():
    return render_template('craft.html')


@app.route('/withdraw')
def withdraw():
    return render_template('withdraw.html')


@app.route('/mines')
def mines():
    return render_template('mines.html')


@app.route('/calendar')
def calendar():
    if 'user_id' not in session:
        return redirect(url_for('auth_login'))

    user_id = session['user_id']

    conn = get_db_connection()

    # Используем текущую дату вместо даты регистрации
    today = datetime.now().date()
    start_date = today.replace(day=1)  # Начало месяца
    current_day = today.day

    # Проверяем, забрал ли сегодня награду
    claimed_today = conn.execute(
        'SELECT 1 FROM daily_rewards WHERE user_id = ? AND DATE(claimed_at) = ?',
        (user_id, today.strftime('%Y-%m-%d'))
    ).fetchone() is not None

    # Общая статистика за текущий месяц
    total_claimed = conn.execute(
        'SELECT SUM(reward_amount) as total FROM daily_rewards WHERE user_id = ? AND strftime("%Y-%m", claimed_at) = ?',
        (user_id, today.strftime('%Y-%m'))
    ).fetchone()['total'] or 0

    # Пропущенные дни в текущем месяце
    total_days_claimed = conn.execute(
        'SELECT COUNT(*) as count FROM daily_rewards WHERE user_id = ? AND strftime("%Y-%m", claimed_at) = ?',
        (user_id, today.strftime('%Y-%m'))
    ).fetchone()['count']
    missed_days = max(0, current_day - total_days_claimed)

    # Время до следующей награды (до полуночи)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    time_until_next = tomorrow - now
    hours = int(time_until_next.seconds // 3600)
    minutes = int((time_until_next.seconds % 3600) // 60)
    seconds = int(time_until_next.seconds % 60)
    next_reward_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    conn.close()

    return render_template('calendar.html',
                           current_day=current_day,
                           claimed_today=claimed_today,
                           total_claimed=total_claimed,
                           missed_days=missed_days,
                           next_reward_time=next_reward_time)


@app.route('/quests')
def quests():
    if 'user_id' not in session:
        return redirect(url_for('auth_login'))

    user_id = session['user_id']

    conn = get_db_connection()

    # Получаем квесты правильно, без дублирования
    quests_data = conn.execute('''
        SELECT 
            q.id,
            q.title,
            q.description,
            q.quest_type,
            q.target_value,
            q.reward_amount,
            COALESCE(qp.current_value, 0) as current_value,
            CASE WHEN COALESCE(qp.current_value, 0) >= q.target_value THEN 1 ELSE 0 END as is_completed,
            COALESCE(qp.completed_at, '') as completed_at
        FROM quests q
        LEFT JOIN quest_progress qp ON q.id = qp.quest_id AND qp.user_id = ?
        WHERE q.is_active = 1
        ORDER BY q.id
    ''', (user_id,)).fetchall()

    # Статистика пользователя
    stats_row = conn.execute(
        'SELECT * FROM user_stats WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    if not stats_row:
        # Создаем запись статистики если её нет
        conn.execute(
            'INSERT INTO user_stats (user_id, last_login) VALUES (?, ?)',
            (user_id, datetime.now().strftime('%Y-%m-%d'))
        )
        conn.commit()
        stats = {
            'total_cases_opened': 0,
            'total_plane_games': 0,
            'total_mines_games': 0,
            'total_safe_cells': 0,
            'total_crafts': 0,
            'total_upgrades': 0,
            'consecutive_logins': 0
        }
    else:
        # Конвертируем Row в словарь
        stats = dict(stats_row)

    # Обновляем статистику входа
    update_login_statistics(user_id)

    # Обновляем прогресс квеста последовательных входов
    update_consecutive_logins_quest(user_id, stats.get('consecutive_logins', 0))

    # Получаем текущую дату для шаблона
    current_date = datetime.now().strftime('%Y-%m-%d')

    conn.close()

    return render_template('quests.html', quests=quests_data, stats=stats, current_date=current_date)

def update_consecutive_logins_quest(user_id, consecutive_days):
    """Обновляет прогресс квеста последовательных входов"""
    conn = get_db_connection()

    # Находим квест последовательных входов
    quest = conn.execute(
        'SELECT * FROM quests WHERE quest_type = ? AND is_active = 1',
        ('consecutive_logins',)
    ).fetchone()

    if quest:
        progress = conn.execute(
            'SELECT * FROM quest_progress WHERE user_id = ? AND quest_id = ?',
            (user_id, quest['id'])
        ).fetchone()

        new_value = min(consecutive_days, quest['target_value'])

        if progress:
            conn.execute(
                'UPDATE quest_progress SET current_value = ?, is_completed = ? WHERE user_id = ? AND quest_id = ?',
                (new_value, 1 if new_value >= quest['target_value'] else 0, user_id, quest['id'])
            )
        else:
            conn.execute(
                'INSERT INTO quest_progress (user_id, quest_id, current_value, is_completed) VALUES (?, ?, ?, ?)',
                (user_id, quest['id'], new_value, 1 if new_value >= quest['target_value'] else 0)
            )

    conn.commit()
    conn.close()

@app.route('/case/<int:case_id>')
def case_detail_page(case_id):
    case_types = {1: 'basic', 2: 'premium', 3: 'legendary'}
    case_type = case_types.get(case_id, 'basic')
    skins = get_case_skins(case_type)
    return render_template('case_detail.html', case_id=case_id, case_type=case_type, skins=skins)


# Авторизация
@app.route('/login', methods=['GET', 'POST'])
def auth_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = verify_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Неверный логин или пароль')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def auth_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if create_user(username, password):
            return redirect(url_for('auth_login'))
        else:
            return render_template('register.html', error='Пользователь уже существует')
    return render_template('register.html')


@app.route('/logout')
def auth_logout():
    session.clear()
    return redirect(url_for('auth_login'))

# Добавь этот маршрут где-то после @app.route('/')

@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy', 'service': 'sticker-auction'}), 200

# Основные API методы
# В app.py обновляем функцию open_case
# Обновляем функцию open_case для работы со всеми типами кейсов
@app.route('/api/open_case/<int:case_id>')
def open_case(case_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    user_id = session['user_id']

    # Расширенная система цен кейсов
    case_prices = {
        # Бесплатные кейсы
        1: 0, 2: 0, 3: 0,
        # Для новичков
        4: 50, 5: 100, 6: 200,
        # Премиум
        7: 500, 8: 1000, 9: 2000,
        # Легендарные
        10: 5000, 11: 10000, 12: 25000,
        # Секретные
        13: 1500, 14: 3000, 15: 7500,
        # VIP
        16: 15000, 17: 50000, 18: 100000,
        # Хеллоуинские
        19: 750, 20: 1500, 21: 3000,
        # Зимние
        22: 1000, 23: 2500, 24: 5000
    }

    case_price = case_prices.get(case_id, 100)

    # Для бесплатных кейсов проверяем лимиты
    if case_price == 0:
        if not check_free_case_availability(user_id, case_id):
            return jsonify({'error': 'Бесплатный кейс уже использован сегодня'}), 400

    current_balance = get_user_balance(user_id)

    if current_balance < case_price:
        return jsonify({'error': 'Недостаточно UC'}), 400

    # Система типов кейсов для game_logic
    case_types = {
        # Бесплатные
        1: 'free', 2: 'free', 3: 'free',
        # Для новичков
        4: 'starter_50', 5: 'starter_100', 6: 'starter_200',
        # Премиум
        7: 'premium_500', 8: 'premium_1000', 9: 'premium_2000',
        # Легендарные
        10: 'legendary_5000', 11: 'legendary_10000', 12: 'legendary_25000',
        # Секретные
        13: 'secret_1500', 14: 'secret_3000', 15: 'secret_7500',
        # VIP
        16: 'vip_15000', 17: 'vip_50000', 18: 'vip_100000',
        # Хеллоуинские
        19: 'halloween_750', 20: 'halloween_1500', 21: 'halloween_3000',
        # Зимние
        22: 'winter_1000', 23: 'winter_2500', 24: 'winter_5000'
    }

    case_type = case_types.get(case_id, 'basic')

    # СПЕРВА получаем выигранный скин
    won_skin = spin_roulette(case_type)

    # ПОТОМ списываем баланс (кроме бесплатных)
    if case_price > 0:
        update_user_balance(user_id, current_balance - case_price)

    # Для бесплатных кейсов отмечаем использование
    if case_price == 0:
        mark_free_case_used(user_id, case_id)

    # Обновляем статистику и квесты
    update_user_stats(user_id, 'total_cases_opened')
    update_quest_progress(user_id, 'open_cases')

    return jsonify(won_skin)

# В app.py добавляем новый маршрут
@app.route('/api/get_case_skins/<case_type>')
def get_case_skins(case_type):
    """Возвращает скины для определенного типа кейса"""
    try:
        skins = get_case_skins(case_type)
        return jsonify({'skins': skins})
    except Exception as e:
        print(f"Error getting case skins: {e}")
        return jsonify({'error': 'Failed to load case skins'}), 500

# Добавляем в app.py вспомогательные функции для бесплатных кейсов
def check_free_case_availability(user_id, case_id):
    """Проверяет, доступен ли бесплатный кейс сегодня"""
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')

    # Проверяем, использовал ли пользователь этот кейс сегодня
    used_today = conn.execute(
        'SELECT 1 FROM free_case_usage WHERE user_id = ? AND case_id = ? AND used_date = ?',
        (user_id, case_id, today)
    ).fetchone()

    conn.close()
    return used_today is None


# В app.py добавляем новый маршрут
@app.route('/api/check_free_case/<int:case_id>')
def check_free_case(case_id):
    """Проверяет доступность бесплатного кейса"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    user_id = session['user_id']

    # Проверяем, является ли кейс бесплатным
    free_case_ids = [1, 2, 3]  # ID бесплатных кейсов
    if case_id not in free_case_ids:
        return jsonify({'available': False, 'error': 'Это не бесплатный кейс'})

    # Проверяем доступность
    is_available = check_free_case_availability(user_id, case_id)

    response_data = {
        'available': is_available,
        'case_id': case_id
    }

    # Добавляем подсказку в зависимости от типа кейса
    if case_id == 1:
        response_data['hint'] = 'Бесплатный кейс доступен 1 раз в день'
    elif case_id == 2:
        response_data['hint'] = 'Приветственный кейс для новых игроков'
    elif case_id == 3:
        response_data['hint'] = 'Ежедневный бонус за вход в игру'

    return jsonify(response_data)

def mark_free_case_used(user_id, case_id):
    """Отмечает использование бесплатного кейса"""
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')

    conn.execute(
        'INSERT OR REPLACE INTO free_case_usage (user_id, case_id, used_date) VALUES (?, ?, ?)',
        (user_id, case_id, today)
    )
    conn.commit()
    conn.close()

@app.route('/api/save_skin', methods=['POST'])
def save_skin():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    skin_id = data['skin_id']
    user_id = session['user_id']

    skin = None
    for rarity in SKINS_DATABASE.values():
        for s in rarity:
            if s['id'] == skin_id:
                skin = s.copy()
                break
        if skin:
            break

    if skin:
        add_skin_to_inventory(user_id, skin)
        return jsonify({'success': True})

    return jsonify({'success': False})


@app.route('/api/sell_skin', methods=['POST'])
def sell_skin():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    skin_id = data['skin_id']
    user_id = session['user_id']

    price = remove_skin_from_inventory(user_id, skin_id)
    if price > 0:
        current_balance = get_user_balance(user_id)
        update_user_balance(user_id, current_balance + price)
        return jsonify({'success': True, 'price': price})

    return jsonify({'success': False})


@app.route('/api/get_inventory')
def get_inventory():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    user_id = session['user_id']
    inventory_items = get_user_inventory(user_id)
    balance = get_user_balance(user_id)

    skins = []
    for item in inventory_items:
        skins.append({
            'id': item['id'],
            'name': item['skin_name'],
            'image': item['skin_image'],
            'price': item['skin_price']
        })

    return jsonify({
        'balance': balance,
        'skins': skins
    })


@app.route('/api/get_user_info')
def get_user_info():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    user_id = session['user_id']
    balance = get_user_balance(user_id)
    username = session.get('username', '')

    return jsonify({
        'username': username,
        'balance': balance
    })


# Игры
@app.route('/api/plane_bet', methods=['POST'])
def plane_bet():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    bet_amount = data.get('amount', 0)
    user_id = session['user_id']

    if bet_amount > 10000000:
        return jsonify({'error': 'Максимальная ставка - 10,000,000 UC'}), 400

    current_balance = get_user_balance(user_id)

    if current_balance < bet_amount:
        return jsonify({'error': 'Недостаточно UC'}), 400

    update_user_balance(user_id, current_balance - bet_amount)

    # Обновляем статистику игры
    update_user_stats(user_id, 'total_plane_games')

    # Обновляем квест только если игра началась (ставка сделана)
    update_quest_progress(user_id, 'play_plane')

    return jsonify({'success': True, 'new_balance': current_balance - bet_amount})


@app.route('/api/plane_win', methods=['POST'])
def plane_win():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    win_amount = data.get('amount', 0)
    user_id = session['user_id']

    current_balance = get_user_balance(user_id)
    update_user_balance(user_id, current_balance + win_amount)

    return jsonify({'success': True, 'new_balance': current_balance + win_amount})


@app.route('/api/mines_bet', methods=['POST'])
def mines_bet():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    bet_amount = data.get('amount', 0)
    user_id = session['user_id']

    if bet_amount > 10000000:
        return jsonify({'error': 'Максимальная ставка - 10,000,000 UC'}), 400

    current_balance = get_user_balance(user_id)

    if current_balance < bet_amount:
        return jsonify({'error': 'Недостаточно UC'}), 400

    update_user_balance(user_id, current_balance - bet_amount)

    update_user_stats(user_id, 'total_mines_games')

    return jsonify({'success': True, 'new_balance': current_balance - bet_amount})


@app.route('/api/mines_win', methods=['POST'])
def mines_win():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    win_amount = data.get('amount', 0)
    user_id = session['user_id']

    current_balance = get_user_balance(user_id)
    update_user_balance(user_id, current_balance + win_amount)

    return jsonify({'success': True, 'new_balance': current_balance + win_amount})


@app.route('/api/update_safe_cells', methods=['POST'])
def update_safe_cells():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    user_id = session['user_id']
    cells_count = data.get('cells_count', 1)

    update_user_stats(user_id, 'total_safe_cells', cells_count)
    update_quest_progress(user_id, 'open_safe_cells', cells_count)

    return jsonify({'success': True})


# Крафт и улучшение
@app.route('/api/upgrade_success', methods=['POST'])
def upgrade_success():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    user_id = session['user_id']
    skin_id = data['skin_id']
    target_id = data['target_id']
    cost = data['cost']

    current_balance = get_user_balance(user_id)
    update_user_balance(user_id, current_balance - cost)
    remove_skin_from_inventory(user_id, skin_id)

    target_skin = {
        'id': target_id,
        'name': f'Улучшенный скин {target_id}',
        'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=UPGRADED',
        'price': cost * 3
    }
    add_skin_to_inventory(user_id, target_skin)

    update_user_stats(user_id, 'total_upgrades')
    update_quest_progress(user_id, 'upgrade_skin')

    return jsonify({'success': True})


@app.route('/api/upgrade_fail', methods=['POST'])
def upgrade_fail():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    user_id = session['user_id']
    skin_id = data['skin_id']
    cost = data['cost']

    current_balance = get_user_balance(user_id)
    update_user_balance(user_id, current_balance - cost)
    remove_skin_from_inventory(user_id, skin_id)

    return jsonify({'success': True})


@app.route('/api/craft_skins', methods=['POST'])
def craft_skins():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    user_id = session['user_id']
    skin1_id = data['skin1_id']
    skin2_id = data['skin2_id']
    result_skin = data['result_skin']

    remove_skin_from_inventory(user_id, skin1_id)
    remove_skin_from_inventory(user_id, skin2_id)
    add_skin_to_inventory(user_id, result_skin)

    update_user_stats(user_id, 'total_crafts')
    update_quest_progress(user_id, 'craft_skins')

    return jsonify({'success': True})


@app.route('/api/process_withdraw', methods=['POST'])
def process_withdraw():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    user_id = session['user_id']
    skins = data['skins']
    email = data['email']
    pubg_id = data['pubg_id']

    for skin in skins:
        remove_skin_from_inventory(user_id, skin['id'])

    return jsonify({
        'success': True,
        'message': 'Заявка на вывод принята в обработку'
    })


# Календарь и квесты API
@app.route('/api/claim_daily_reward', methods=['POST'])
def claim_daily_reward():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    user_id = session['user_id']
    today = datetime.now().strftime('%Y-%m-%d')

    conn = get_db_connection()

    # Проверяем, не забрал ли уже сегодня
    already_claimed = conn.execute(
        'SELECT 1 FROM daily_rewards WHERE user_id = ? AND DATE(claimed_at) = ?',
        (user_id, today)
    ).fetchone()

    if already_claimed:
        conn.close()
        return jsonify({'success': False, 'error': 'Вы уже забрали сегодняшнюю награду'})

    # Определяем день месяца и награду
    current_day = datetime.now().day

    # Рассчитываем награду по дням месяца
    if current_day % 7 == 0:
        reward_amount = 5000  # Каждые 7 дней
    elif current_day % 3 == 0:
        reward_amount = 1000  # Каждые 3 дня
    else:
        reward_amount = 500  # Обычный день

    # Выдаем награду
    current_balance = get_user_balance(user_id)
    update_user_balance(user_id, current_balance + reward_amount)

    # Записываем в историю
    conn.execute(
        'INSERT INTO daily_rewards (user_id, reward_day, reward_amount) VALUES (?, ?, ?)',
        (user_id, current_day, reward_amount)
    )

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'reward': reward_amount})


@app.route('/api/claim_quest_reward', methods=['POST'])
def claim_quest_reward():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    quest_id = data.get('quest_id')
    user_id = session['user_id']

    conn = get_db_connection()

    progress = conn.execute('''
        SELECT qp.*, q.reward_amount, q.target_value
        FROM quest_progress qp
        JOIN quests q ON qp.quest_id = q.id
        WHERE qp.user_id = ? AND qp.quest_id = ?
    ''', (user_id, quest_id)).fetchone()

    if not progress or not progress['is_completed']:
        conn.close()
        return jsonify({'success': False, 'error': 'Квест не выполнен'})

    if progress['completed_at']:
        conn.close()
        return jsonify({'success': False, 'error': 'Награда уже получена'})

    reward_amount = progress['reward_amount']
    current_balance = get_user_balance(user_id)
    update_user_balance(user_id, current_balance + reward_amount)

    conn.execute(
        'UPDATE quest_progress SET completed_at = CURRENT_TIMESTAMP WHERE user_id = ? AND quest_id = ?',
        (user_id, quest_id)
    )

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'reward': reward_amount})


# Вспомогательные функции
def update_login_statistics(user_id):
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')

    stats_row = conn.execute(
        'SELECT * FROM user_stats WHERE user_id = ?',
        (user_id,)
    ).fetchone()

    if not stats_row:
        conn.execute('INSERT INTO user_stats (user_id, last_login) VALUES (?, ?)', (user_id, today))
        conn.commit()
        conn.close()
        return

    # Конвертируем Row в словарь для работы
    stats = dict(stats_row)
    last_login = stats['last_login']

    if last_login != today:
        if last_login and (datetime.strptime(today, '%Y-%m-%d') - datetime.strptime(last_login, '%Y-%m-%d')).days == 1:
            new_consecutive = stats['consecutive_logins'] + 1
        else:
            new_consecutive = 1

        conn.execute(
            'UPDATE user_stats SET last_login = ?, consecutive_logins = ? WHERE user_id = ?',
            (today, new_consecutive, user_id)
        )
        conn.commit()

    conn.close()

def update_quest_progress(user_id, quest_type, increment=1):
    """Обновляет прогресс квестов"""
    conn = get_db_connection()

    # ИСПРАВЛЕНИЕ: Получаем квесты по типу
    quests = conn.execute(
        'SELECT * FROM quests WHERE quest_type = ? AND is_active = 1',
        (quest_type,)
    ).fetchall()

    for quest in quests:
        progress = conn.execute(
            'SELECT * FROM quest_progress WHERE user_id = ? AND quest_id = ?',
            (user_id, quest['id'])
        ).fetchone()

        # Пропускаем если квест уже завершен и награда получена
        if progress and progress['is_completed'] and progress['completed_at']:
            continue

        new_value = (progress['current_value'] if progress else 0) + increment
        is_completed = new_value >= quest['target_value']

        if progress:
            # Обновляем только если еще не завершен или не получена награда
            if not progress['completed_at']:
                conn.execute(
                    'UPDATE quest_progress SET current_value = ?, is_completed = ? WHERE user_id = ? AND quest_id = ?',
                    (new_value, 1 if is_completed else 0, user_id, quest['id'])
                )
        else:
            # Создаем новую запись только если её нет
            conn.execute(
                'INSERT INTO quest_progress (user_id, quest_id, current_value, is_completed) VALUES (?, ?, ?, ?)',
                (user_id, quest['id'], new_value, 1 if is_completed else 0)
            )

    conn.commit()
    conn.close()

def update_user_stats(user_id, stat_field, increment=1):
    conn = get_db_connection()

    conn.execute(
        f'UPDATE user_stats SET {stat_field} = {stat_field} + ? WHERE user_id = ?',
        (increment, user_id)
    )

    conn.commit()
    conn.close()


# Админ панель
@app.route('/admin')
def admin_panel():
    if session.get('username') != 'Developer':
        return redirect(url_for('index'))
    return render_template('admin.html')


@app.route('/api/admin/get_users')
def admin_get_users():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    try:
        conn = get_db_connection()
        users = conn.execute('''
            SELECT u.id, u.username, u.balance, u.created_at, u.is_banned,
                   (SELECT COUNT(*) FROM inventory i WHERE i.user_id = u.id) as skin_count
            FROM users u 
            ORDER BY u.created_at DESC
        ''').fetchall()
        conn.close()

        users_list = []
        for user in users:
            users_list.append({
                'id': user['id'],
                'username': user['username'],
                'balance': user['balance'],
                'created_at': user['created_at'],
                'is_banned': bool(user['is_banned']),
                'skin_count': user['skin_count']
            })

        return jsonify({'users': users_list})

    except Exception as e:
        print(f"Error in admin_get_users: {str(e)}")
        return jsonify({'error': 'Database error'}), 500


@app.route('/api/admin/get_all_skins')
def admin_get_all_skins():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    all_skins = []
    for rarity, skins_list in SKINS_DATABASE.items():
        for skin in skins_list:
            skin_with_rarity = skin.copy()
            skin_with_rarity['rarity'] = rarity
            skin_with_rarity['rarity_name'] = get_rarity_name(rarity)
            all_skins.append(skin_with_rarity)

    return jsonify({
        'skins': all_skins
    })


@app.route('/api/admin/system_stats')
def admin_system_stats():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    conn = get_db_connection()

    total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
    total_skins = conn.execute('SELECT COUNT(*) as count FROM inventory').fetchone()['count']
    total_balance = conn.execute('SELECT SUM(balance) as total FROM users').fetchone()['total'] or 0

    conn.close()

    return jsonify({
        'total_users': total_users,
        'total_skins': total_skins,
        'total_balance': total_balance
    })


@app.route('/api/admin/set_balance', methods=['POST'])
def admin_set_balance():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')

    if not user_id or amount is None:
        return jsonify({'success': False, 'error': 'Missing user_id or amount'})

    try:
        update_user_balance(user_id, amount)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/add_balance', methods=['POST'])
def admin_add_balance():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    user_id = data.get('user_id')
    amount = data.get('amount')

    if not user_id or amount is None:
        return jsonify({'success': False, 'error': 'Missing user_id or amount'})

    try:
        current_balance = get_user_balance(user_id)
        update_user_balance(user_id, current_balance + amount)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/give_skin', methods=['POST'])
def admin_give_skin():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    user_id = data.get('user_id')
    skin_id = data.get('skin_id')

    if not user_id or not skin_id:
        return jsonify({'success': False, 'error': 'Missing user_id or skin_id'})

    skin = None
    for rarity in SKINS_DATABASE.values():
        for s in rarity:
            if s['id'] == skin_id:
                skin = s.copy()
                break
        if skin:
            break

    if skin:
        try:
            add_skin_to_inventory(user_id, skin)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    return jsonify({'success': False, 'error': 'Skin not found'})


@app.route('/api/admin/ban_user', methods=['POST'])
def admin_ban_user():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Missing user_id'})

    try:
        conn = get_db_connection()
        conn.execute('UPDATE users SET is_banned = 1 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/unban_user', methods=['POST'])
def admin_unban_user():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Missing user_id'})

    try:
        conn = get_db_connection()
        conn.execute('UPDATE users SET is_banned = 0 WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/give_all_bonus', methods=['POST'])
def admin_give_all_bonus():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    amount = data.get('amount', 100)

    try:
        conn = get_db_connection()
        users = conn.execute('SELECT id, balance FROM users WHERE username != "Developer"').fetchall()

        for user in users:
            new_balance = user['balance'] + amount
            conn.execute('UPDATE users SET balance = ? WHERE id = ?', (new_balance, user['id']))

        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/reset_all_inventories', methods=['POST'])
def admin_reset_all_inventories():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM inventory')
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/generate_daily_rewards', methods=['POST'])
def admin_generate_daily_rewards():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    try:
        conn = get_db_connection()
        users = conn.execute('SELECT id FROM users WHERE username != "Developer"').fetchall()

        for user in users:
            bonus = random.randint(50, 200)
            current_balance = get_user_balance(user['id'])
            update_user_balance(user['id'], current_balance + bonus)

        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/create_test_users', methods=['POST'])
def admin_create_test_users():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    test_users = [
        {'username': 'test_user1', 'password': '123'},
        {'username': 'test_user2', 'password': '123'},
        {'username': 'test_user3', 'password': '123'},
        {'username': 'pro_player', 'password': '123'},
        {'username': 'casino_king', 'password': '123'}
    ]

    created_count = 0
    for user_data in test_users:
        if create_user(user_data['username'], user_data['password']):
            created_count += 1

    return jsonify({
        'success': True,
        'created_count': created_count,
        'message': f'Создано {created_count} тестовых пользователей'
    })


@app.route('/api/admin/delete_user', methods=['POST'])
def admin_delete_user():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    data = request.json
    user_id = data.get('user_id')

    if not user_id:
        return jsonify({'success': False, 'error': 'Missing user_id'})

    try:
        conn = get_db_connection()

        if user_id == session.get('user_id'):
            return jsonify({'success': False, 'error': 'Нельзя удалить себя'})

        conn.execute('DELETE FROM inventory WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))

        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/admin/modify_case_chances', methods=['POST'])
def admin_modify_case_chances():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({'success': True, 'message': 'Шансы кейсов обновлены'})


@app.route('/api/admin/export_users')
def admin_export_users():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    conn = get_db_connection()
    users = conn.execute('''
        SELECT u.id, u.username, u.balance, u.created_at,
               COUNT(i.id) as skin_count
        FROM users u 
        LEFT JOIN inventory i ON u.id = i.user_id
        GROUP BY u.id
    ''').fetchall()
    conn.close()

    return jsonify({
        'success': True,
        'data': [dict(user) for user in users],
        'message': 'Данные готовы для экспорта'
    })


@app.route('/api/admin/export_transactions')
def admin_export_transactions():
    if session.get('username') != 'Developer':
        return jsonify({'error': 'Access denied'}), 403

    return jsonify({
        'success': True,
        'message': 'Транзакции готовы для экспорта'
    })


@app.route('/api/complete_quest', methods=['POST'])
def complete_quest():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    quest_type = data.get('quest_type')
    user_id = session['user_id']

    if quest_type:
        update_quest_progress(user_id, quest_type, 1)
        return jsonify({'success': True})

    return jsonify({'success': False, 'error': 'No quest type provided'})


# Добавить в app.py новые маршруты

# Добавить эти маршруты в app.py

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('auth_login'))

    user_id = session['user_id']
    conn = get_db_connection()

    # Получаем аватар пользователя из БД
    user_data = conn.execute(
        'SELECT avatar, created_at FROM users WHERE id = ?', (user_id,)
    ).fetchone()

    # Получаем статистику пользователя
    stats = conn.execute(
        'SELECT * FROM user_stats WHERE user_id = ?', (user_id,)
    ).fetchone()

    # Получаем количество скинов
    skin_count = conn.execute(
        'SELECT COUNT(*) as count FROM inventory WHERE user_id = ?', (user_id,)
    ).fetchone()['count']

    conn.close()

    # Форматируем дату регистрации
    reg_date = user_data['created_at'].split()[0] if user_data else 'Неизвестно'

    # Общая статистика игр
    total_games = (stats['total_cases_opened'] if stats else 0) + \
                  (stats['total_plane_games'] if stats else 0) + \
                  (stats['total_mines_games'] if stats else 0)

    # Текущая аватарка
    current_avatar = user_data['avatar'] if user_data and user_data['avatar'] else 'avatar1.png'

    return render_template('settings.html',
                           registration_date=reg_date,
                           total_games=total_games,
                           cases_opened=stats['total_cases_opened'] if stats else 0,
                           total_skins=skin_count,
                           current_avatar=current_avatar)


@app.route('/api/change_username', methods=['POST'])
def change_username():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    new_username = data.get('new_username', '').strip()
    user_id = session['user_id']

    if not new_username:
        return jsonify({'success': False, 'error': 'Введите никнейм'})

    if len(new_username) < 3 or len(new_username) > 20:
        return jsonify({'success': False, 'error': 'Никнейм должен быть от 3 до 20 символов'})

    conn = get_db_connection()

    # Проверяем, не занят ли ник
    existing_user = conn.execute(
        'SELECT id FROM users WHERE username = ? AND id != ?',
        (new_username, user_id)
    ).fetchone()

    if existing_user:
        conn.close()
        return jsonify({'success': False, 'error': 'Этот никнейм уже занят'})

    # Обновляем никнейм
    conn.execute(
        'UPDATE users SET username = ? WHERE id = ?',
        (new_username, user_id)
    )
    conn.commit()
    conn.close()

    # Обновляем сессию
    session['username'] = new_username

    return jsonify({'success': True})


@app.route('/api/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    user_id = session['user_id']

    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Заполните все поля'})

    if len(new_password) < 4:
        return jsonify({'success': False, 'error': 'Пароль должен быть не менее 4 символов'})

    import hashlib

    conn = get_db_connection()

    # Проверяем текущий пароль
    current_password_hash = hashlib.sha256(current_password.encode()).hexdigest()
    user = conn.execute(
        'SELECT id FROM users WHERE id = ? AND password = ?',
        (user_id, current_password_hash)
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({'success': False, 'error': 'Неверный текущий пароль'})

    # Обновляем пароль
    new_password_hash = hashlib.sha256(new_password.encode()).hexdigest()
    conn.execute(
        'UPDATE users SET password = ? WHERE id = ?',
        (new_password_hash, user_id)
    )
    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/change_avatar', methods=['POST'])
def change_avatar():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authorized'}), 401

    data = request.json
    avatar = data.get('avatar', 'avatar1.png')
    user_id = session['user_id']

    # Сохраняем в БД
    conn = get_db_connection()
    conn.execute(
        'UPDATE users SET avatar = ? WHERE id = ?',
        (avatar, user_id)
    )
    conn.commit()
    conn.close()

    # Обновляем сессию
    session['avatar'] = avatar

    return jsonify({'success': True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)