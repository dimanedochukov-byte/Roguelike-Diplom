# Налаштування вікна
WIDTH = 800
HEIGHT = 600
FPS = 60
TITLE = "Roguelike Diplom: Alpha Build"

# Кольори (формат RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREY = (40, 40, 40)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GREY = (100, 100, 100)

# Налаштування гравця
PLAYER_SIZE = 40
PLAYER_SPEED = 300
PLAYER_HEALTH = 100
PLAYER_COLOR = (0, 255, 0)

# Налаштування сітки (Світу)
TILESIZE = 40

# Налаштування зброї та куль
BULLET_SPEED = 600
BULLET_LIFETIME = 1000
BULLET_SIZE = 10
BULLET_COLOR = (255, 255, 0)

# Характеристики зброї: rate, count, spread, damage, mag, reload
WEAPONS = {
    'pistol': {'rate': 300, 'count': 1, 'spread': 2, 'damage': 35, 'mag': 12, 'reload': 1000},
    'shotgun': {'rate': 800, 'count': 6, 'spread': 15, 'damage': 15, 'mag': 6, 'reload': 2000},
    'machine_gun': {'rate': 100, 'count': 1, 'spread': 6, 'damage': 15, 'mag': 30, 'reload': 1500}
}


MOB_DAMAGE = 20
MOB_KNOCKBACK = 15
MOB_COLOR_HIT = (255, 255, 255)
SPAWN_RADIUS = 280
EMERGE_TIME = 1000


# Інші об'єкти
COIN_SIZE = 15
COIN_COLOR = (255, 255, 0)

PORTAL_SIZE = 90
PORTAL_COLOR = (128, 0, 128)
DOOR_COLOR = (200, 150, 50)

MOB_PROJECTILE_SPEED = 300
MOB_PROJECTILE_LIFETIME = 2000
MOB_PROJECTILE_COLOR = (255, 0, 0) 


MOB_TYPES = {
    'zombie': {'speed': 80, 'health': 100, 'color': (34, 139, 34), 'type': 'melee'},
    'skeleton': {'speed': 160, 'health': 50, 'color': (220, 220, 220), 'type': 'melee'},
    'archer': {'speed': 100, 'health': 60, 'color': (200, 180, 50), 'type': 'ranged', 'shoot_rate': 2000}
}



