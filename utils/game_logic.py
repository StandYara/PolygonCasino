import random

# Улучшенная база данных скинов с правильной экономикой
SKINS_DATABASE = {
    'common': [
        # Оружие обычной редкости (цена: 10-50 UC)
        {'id': 1, 'name': 'M416 - Серый', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=M416',
         'price': 20, 'type': 'assault_rifle'},
        {'id': 2, 'name': 'AKM - Стандарт', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=AKM',
         'price': 25, 'type': 'assault_rifle'},
        {'id': 3, 'name': 'UMP9 - Базовый', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=UMP9',
         'price': 15, 'type': 'smg'},
        {'id': 4, 'name': 'SKS - Обычный', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=SKS',
         'price': 30, 'type': 'marksman'},
        {'id': 5, 'name': 'Kar98k - Стандарт', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=KAR98',
         'price': 35, 'type': 'sniper'},
        {'id': 6, 'name': 'SCAR-L - Зеленый', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=SCAR',
         'price': 22, 'type': 'assault_rifle'},
        {'id': 7, 'name': 'M24 - Обычный', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=M24',
         'price': 40, 'type': 'sniper'},
        {'id': 8, 'name': 'UZI - Базовый', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=UZI',
         'price': 12, 'type': 'smg'},
        {'id': 9, 'name': 'Vector - Стандарт', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=VECTOR',
         'price': 18, 'type': 'smg'},
        {'id': 10, 'name': 'Mini14 - Обычный', 'image': 'https://via.placeholder.com/100/6c757d/ffffff?text=MINI14',
         'price': 28, 'type': 'marksman'},
    ],

    'rare': [
        # Оружие редкой редкости (цена: 100-300 UC)
        {'id': 201, 'name': 'M416 - Голубой Лед', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=M416',
         'price': 150, 'type': 'assault_rifle'},
        {'id': 202, 'name': 'AKM - Кровавый', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=AKM',
         'price': 180, 'type': 'assault_rifle'},
        {'id': 203, 'name': 'AWM - Арктический', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=AWM',
         'price': 300, 'type': 'sniper'},
        {'id': 204, 'name': 'Groza - Пустынный', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=GROZA',
         'price': 220, 'type': 'assault_rifle'},
        {'id': 205, 'name': 'M249 - Песочный', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=M249',
         'price': 280, 'type': 'lmg'},
        {'id': 206, 'name': 'SCAR-L - Лесной', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=SCAR',
         'price': 160, 'type': 'assault_rifle'},
        {'id': 207, 'name': 'Kar98k - Охотник', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=KAR98',
         'price': 200, 'type': 'sniper'},
        {'id': 208, 'name': 'UMP9 - Городской', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=UMP9',
         'price': 120, 'type': 'smg'},
        {'id': 209, 'name': 'Vector - Неоновый', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=VECTOR',
         'price': 140, 'type': 'smg'},
        {'id': 210, 'name': 'SKS - Тактический', 'image': 'https://via.placeholder.com/100/007bff/ffffff?text=SKS',
         'price': 190, 'type': 'marksman'},
    ],

    'epic': [
        # Оружие эпической редкости (цена: 500-1500 UC)
        {'id': 401, 'name': 'M416 - Драконий Огонь', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=M416',
         'price': 800, 'type': 'assault_rifle'},
        {'id': 402, 'name': 'AKM - Вампир', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=AKM',
         'price': 900, 'type': 'assault_rifle'},
        {'id': 403, 'name': 'AWM - Ледяной Дракон', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=AWM',
         'price': 1500, 'type': 'sniper'},
        {'id': 404, 'name': 'Groza - Гром', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=GROZA',
         'price': 1000, 'type': 'assault_rifle'},
        {'id': 405, 'name': 'M249 - Адская Пулемет', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=M249',
         'price': 1200, 'type': 'lmg'},
        {'id': 406, 'name': 'Kar98k - Призрачный', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=KAR98',
         'price': 700, 'type': 'sniper'},
        {'id': 407, 'name': 'SCAR-L - Золотой', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=SCAR',
         'price': 850, 'type': 'assault_rifle'},
        {'id': 408, 'name': 'Vector - Киберпанк', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=VECTOR',
         'price': 750, 'type': 'smg'},
        {'id': 409, 'name': 'SKS - Демонический', 'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=SKS',
         'price': 950, 'type': 'marksman'},
        {'id': 410, 'name': 'M24 - Призрачный Снайпер',
         'image': 'https://via.placeholder.com/100/8a2be2/ffffff?text=M24', 'price': 1100, 'type': 'sniper'},
    ],

    'legendary': [
        # Оружие легендарной редкости (цена: 2000-5000 UC)
        {'id': 601, 'name': 'M249 - GODLIKE', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=M249',
         'price': 3000, 'type': 'lmg'},
        {'id': 602, 'name': 'AWM - DRAGON KING', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=AWM',
         'price': 5000, 'type': 'sniper'},
        {'id': 603, 'name': 'M416 - IMMORTAL', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=M416',
         'price': 2500, 'type': 'assault_rifle'},
        {'id': 604, 'name': 'AKM - BLOOD GOD', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=AKM',
         'price': 2800, 'type': 'assault_rifle'},
        {'id': 605, 'name': 'Groza - THUNDER LORD', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=GROZA',
         'price': 3200, 'type': 'assault_rifle'},
        {'id': 606, 'name': 'Kar98k - PHOENIX', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=KAR98',
         'price': 2200, 'type': 'sniper'},
        {'id': 607, 'name': 'Mk14 - DIVINE', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=MK14',
         'price': 3800, 'type': 'marksman'},
        {'id': 608, 'name': 'AUG A3 - COSMIC', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=AUG',
         'price': 2700, 'type': 'assault_rifle'},
        {'id': 609, 'name': 'Beryl M762 - INFERNO', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=BERYL',
         'price': 2600, 'type': 'assault_rifle'},
        {'id': 610, 'name': 'Vector - NEO TOKYO', 'image': 'https://via.placeholder.com/100/ff6b6b/ffffff?text=VECTOR',
         'price': 2300, 'type': 'smg'},
    ],

    'mythical': [
        # Оружие мифической редкости (цена: 10000-50000 UC)
        {'id': 801, 'name': 'M416 - UNIVERSE', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=M416',
         'price': 15000, 'type': 'assault_rifle'},
        {'id': 802, 'name': 'AWM - GALAXY', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=AWM',
         'price': 30000, 'type': 'sniper'},
        {'id': 803, 'name': 'AKM - INFINITY', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=AKM',
         'price': 20000, 'type': 'assault_rifle'},
        {'id': 804, 'name': 'M249 - OBLIVION', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=M249',
         'price': 25000, 'type': 'lmg'},
        {'id': 805, 'name': 'Groza - ETERNITY', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=GROZA',
         'price': 18000, 'type': 'assault_rifle'},
        {'id': 806, 'name': 'Kar98k - CELESTIAL', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=KAR98',
         'price': 22000, 'type': 'sniper'},
        {'id': 807, 'name': 'Vector - QUANTUM', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=VECTOR',
         'price': 12000, 'type': 'smg'},
        {'id': 808, 'name': 'SCAR-L - NEBULA', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=SCAR',
         'price': 16000, 'type': 'assault_rifle'},
        {'id': 809, 'name': 'Mk14 - DIVINITY', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=MK14',
         'price': 35000, 'type': 'marksman'},
        {'id': 810, 'name': 'AUG A3 - COSMOS', 'image': 'https://via.placeholder.com/100/ff00ff/ffffff?text=AUG',
         'price': 28000, 'type': 'assault_rifle'},
    ],

    'ancient': [
        # Оружие древней редкости (цена: 100000+ UC)
        {'id': 901, 'name': 'M416 - GOD SLAYER', 'image': 'https://via.placeholder.com/100/00ffff/ffffff?text=M416',
         'price': 150000, 'type': 'assault_rifle'},
        {'id': 902, 'name': 'AWM - UNIVERSE DESTROYER',
         'image': 'https://via.placeholder.com/100/00ffff/ffffff?text=AWM', 'price': 300000, 'type': 'sniper'},
        {'id': 903, 'name': 'AKM - INFINITY BLADE', 'image': 'https://via.placeholder.com/100/00ffff/ffffff?text=AKM',
         'price': 200000, 'type': 'assault_rifle'},
        {'id': 904, 'name': 'M249 - OBLIVION CANNON',
         'image': 'https://via.placeholder.com/100/00ffff/ffffff?text=M249', 'price': 250000, 'type': 'lmg'},
        {'id': 905, 'name': 'Groza - ETERNAL THUNDER',
         'image': 'https://via.placeholder.com/100/00ffff/ffffff?text=GROZA', 'price': 180000, 'type': 'assault_rifle'},
        {'id': 906, 'name': 'Kar98k - CELESTIAL BOLT',
         'image': 'https://via.placeholder.com/100/00ffff/ffffff?text=KAR98', 'price': 220000, 'type': 'sniper'},
    ]
}


# В game_logic.py добавить новые типы кейсов в функцию get_case_skins:

# В game_logic.py обновляем функцию get_case_skins
def get_case_skins(case_type='basic'):
    """Возвращает скины для определенного типа кейса с правильным распределением"""
    chances = {
        # Бесплатные кейсы (очень низкие шансы на хорошее)
        'free': {'common': 95, 'rare': 5, 'epic': 0, 'legendary': 0, 'mythical': 0, 'ancient': 0},

        # Для новичков (постепенно улучшаются шансы)
        'starter_50': {'common': 80, 'rare': 18, 'epic': 2, 'legendary': 0, 'mythical': 0, 'ancient': 0},
        'starter_100': {'common': 70, 'rare': 25, 'epic': 5, 'legendary': 0, 'mythical': 0, 'ancient': 0},
        'starter_200': {'common': 60, 'rare': 30, 'epic': 9, 'legendary': 1, 'mythical': 0, 'ancient': 0},

        # Премиум (сбалансированные шансы)
        'premium_500': {'common': 40, 'rare': 45, 'epic': 12, 'legendary': 3, 'mythical': 0, 'ancient': 0},
        'premium_1000': {'common': 30, 'rare': 40, 'epic': 20, 'legendary': 9, 'mythical': 1, 'ancient': 0},
        'premium_2000': {'common': 20, 'rare': 35, 'epic': 30, 'legendary': 13, 'mythical': 2, 'ancient': 0},

        # Легендарные (высокие шансы на легендарные)
        'legendary_5000': {'common': 10, 'rare': 25, 'epic': 40, 'legendary': 20, 'mythical': 4, 'ancient': 1},
        'legendary_10000': {'common': 5, 'rare': 15, 'epic': 35, 'legendary': 30, 'mythical': 12, 'ancient': 3},
        'legendary_25000': {'common': 2, 'rare': 8, 'epic': 25, 'legendary': 40, 'mythical': 20, 'ancient': 5},

        # Секретные (высокий риск/высокая награда)
        'secret_1500': {'common': 50, 'rare': 30, 'epic': 15, 'legendary': 4, 'mythical': 1, 'ancient': 0},
        'secret_3000': {'common': 40, 'rare': 25, 'epic': 20, 'legendary': 10, 'mythical': 4, 'ancient': 1},
        'secret_7500': {'common': 30, 'rare': 20, 'epic': 25, 'legendary': 15, 'mythical': 8, 'ancient': 2},

        # VIP (гарантированные высокие редкости)
        'vip_15000': {'common': 0, 'rare': 20, 'epic': 40, 'legendary': 30, 'mythical': 8, 'ancient': 2},
        'vip_50000': {'common': 0, 'rare': 10, 'epic': 30, 'legendary': 40, 'mythical': 15, 'ancient': 5},
        'vip_100000': {'common': 0, 'rare': 5, 'epic': 20, 'legendary': 45, 'mythical': 20, 'ancient': 10},

        # Хеллоуинские (специальные скины)
        'halloween_750': {'common': 35, 'rare': 40, 'epic': 20, 'legendary': 4, 'mythical': 1, 'ancient': 0},
        'halloween_1500': {'common': 25, 'rare': 35, 'epic': 30, 'legendary': 8, 'mythical': 2, 'ancient': 0},
        'halloween_3000': {'common': 15, 'rare': 30, 'epic': 35, 'legendary': 15, 'mythical': 4, 'ancient': 1},

        # Зимние (специальные скины)
        'winter_1000': {'common': 30, 'rare': 45, 'epic': 20, 'legendary': 4, 'mythical': 1, 'ancient': 0},
        'winter_2500': {'common': 20, 'rare': 40, 'epic': 30, 'legendary': 8, 'mythical': 2, 'ancient': 0},
        'winter_5000': {'common': 10, 'rare': 35, 'epic': 35, 'legendary': 15, 'mythical': 4, 'ancient': 1},

        # Базовые (старые - для обратной совместимости)
        'basic': {'common': 85, 'rare': 14, 'epic': 1, 'legendary': 0, 'mythical': 0, 'ancient': 0},
        'premium': {'common': 40, 'rare': 45, 'epic': 12, 'legendary': 3, 'mythical': 0, 'ancient': 0},
        'legendary': {'common': 10, 'rare': 25, 'epic': 40, 'legendary': 20, 'mythical': 4, 'ancient': 1}
    }

    case_chances = chances.get(case_type, chances['basic'])
    all_skins = []

    for rarity, percent in case_chances.items():
        if percent > 0 and rarity in SKINS_DATABASE:
            skins = SKINS_DATABASE[rarity]

            # Берем только часть скинов в зависимости от процента
            num_skins = max(1, len(skins) * percent // 100)
            selected_skins = random.sample(skins, min(num_skins, len(skins)))

            # Добавляем каждый скин по одному разу
            all_skins.extend(selected_skins)

    # Перемешиваем все скины для разнообразия в рулетке
    random.shuffle(all_skins)

    # Ограничиваем общее количество скинов для производительности
    return all_skins[:100]  # Максимум 100 скинов для рулетки


def spin_roulette(case_type='basic'):
    """Крутит рулетку и возвращает выигранный скин"""
    skins_pool = get_case_skins(case_type)

    # Генерируем случайное число для определения выигрыша
    # Вместо random.choice используем взвешенную вероятность
    total_weight = len(skins_pool)
    random_index = random.randint(0, total_weight - 1)

    won_skin = skins_pool[random_index]

    # Создаем копию скина чтобы не менять оригинал
    result_skin = won_skin.copy()

    return result_skin


def get_skin_rarity(skin_price):
    """Определяет редкость скина по цене"""
    if skin_price <= 50:
        return 'common'
    elif skin_price <= 300:
        return 'rare'
    elif skin_price <= 1500:
        return 'epic'
    elif skin_price <= 5000:
        return 'legendary'
    elif skin_price <= 50000:
        return 'mythical'
    else:
        return 'ancient'


def get_rarity_color(rarity):
    """Возвращает цвет для редкости"""
    colors = {
        'common': '#6c757d',
        'rare': '#007bff',
        'epic': '#8a2be2',
        'legendary': '#ff6b6b',
        'mythical': '#ff00ff',
        'ancient': '#00ffff'
    }
    return colors.get(rarity, '#6c757d')


def get_rarity_name(rarity):
    """Возвращает название редкости на русском"""
    names = {
        'common': 'Обычный',
        'rare': 'Редкий',
        'epic': 'Эпический',
        'legendary': 'Легендарный',
        'mythical': 'Мифический',
        'ancient': 'Древний'
    }
    return names.get(rarity, 'Обычный')


def get_upgrade_targets(current_skin_price, current_rarity):
    """Возвращает возможные цели для улучшения с разными шансами"""
    rarity_order = ['common', 'rare', 'epic', 'legendary', 'mythical', 'ancient']
    current_index = rarity_order.index(current_rarity)

    targets = []

    # Цели с высоким шансом (70%) - следующая редкость
    if current_index + 1 < len(rarity_order):
        next_rarity = rarity_order[current_index + 1]
        high_chance_skins = SKINS_DATABASE.get(next_rarity, [])
        for skin in high_chance_skins[:3]:  # Берем первые 3 скина
            targets.append({
                **skin,
                'success_chance': 70,
                'upgrade_cost': int(skin['price'] * 0.3)  # 30% от цены целевого скина
            })

    # Цели со средним шансом (50%) - через одну редкость
    if current_index + 2 < len(rarity_order):
        medium_rarity = rarity_order[current_index + 2]
        medium_chance_skins = SKINS_DATABASE.get(medium_rarity, [])
        for skin in medium_chance_skins[:2]:  # Берем первые 2 скина
            targets.append({
                **skin,
                'success_chance': 50,
                'upgrade_cost': int(skin['price'] * 0.5)  # 50% от цены целевого скина
            })

    # Цели с низким шансом (30%) - через две редкости
    if current_index + 3 < len(rarity_order):
        low_rarity = rarity_order[current_index + 3]
        low_chance_skins = SKINS_DATABASE.get(low_rarity, [])
        for skin in low_chance_skins[:1]:  # Берем первый скин
            targets.append({
                **skin,
                'success_chance': 30,
                'upgrade_cost': int(skin['price'] * 0.7)  # 70% от цены целевого скина
            })

    # Цели с очень низким шансом (15%) - через три редкости
    if current_index + 4 < len(rarity_order):
        very_low_rarity = rarity_order[current_index + 4]
        very_low_chance_skins = SKINS_DATABASE.get(very_low_rarity, [])
        for skin in very_low_chance_skins[:1]:  # Берем первый скин
            targets.append({
                **skin,
                'success_chance': 15,
                'upgrade_cost': int(skin['price'] * 0.9)  # 90% от цены целевого скина
            })

    return targets