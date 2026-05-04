import pygame      # Головна бібліотека для малювання графіки
import sys         # Системна бібліотека (потрібна для закриття гри без помилок)
import random      # Бібліотека для випадкових чисел (для спавну мобів і кімнат)
import os          # Бібліотека для роботи з файлами (для пошуку папки з картинками)
from settings import *  # Завантаження констант (кольори, швидкість, розміри)
from map_gen import DungeonGenerator # Завантаження генератора кімнат і коридорів
from sprites import Player, Wall, Bullet, Floor, Mob, Coin, Portal, Crosshair # Завантаження всіх ігрових об'єктів

# Створення скороченої назви для векторів. Вектор - це математична "стрілочка", 
# яка має напрямок і довжину. Використовується для руху і камери.
vec = pygame.math.Vector2

class Camera:
    # Клас камери. Камера сама нічого не малює, просто вираховує зміщення картинки, 
    # щоб гравець завжди залишався по центру екрану.
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height) # Невидима рамка камери
        self.width = width
        self.height = height
        # Збереження точних координат з крапкою (float) для плавного руху
        self.x = 0.0
        self.y = 0.0

    def apply(self, entity):
        # Зміщення картинки об'єкта відповідно до того, на скільки посунулась камера
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        # Обчислення позиції камери (центрування рівно на гравці)
        target_x = -target.pos.x + int(WIDTH / 2)
        target_y = -target.pos.y + int(HEIGHT / 2)
        
        # Плавне слідування камери за гравцем (на 10% ближче кожен кадр) замість жорсткого прилипання
        self.x += (target_x - self.x) * 0.1
        self.y += (target_y - self.y) * 0.1
        
        # Передача округлених цілих чисел в рамку (пікселі не можуть бути дробовими)
        self.camera.x = int(self.x)
        self.camera.y = int(self.y)

class Game:
    # Головна програма. Створює вікно, запускає меню і керує всім ігровим процесом.
    def __init__(self):
        pygame.init() # Запуск рушія
        self.font = pygame.font.SysFont("Arial", 28) # Завантаження звичайного шрифту Arial
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT)) # Створення вікна гри
        pygame.display.set_caption(TITLE) # Задання назви вікна
        self.clock = pygame.time.Clock() # Таймер для контролю кадрів за секунду (FPS)
        self.running = True # Прапорець роботи гри (False - гра закривається)
        self.score = 0 # Кількість зібраних монет
        self.damage_timer = 0 # Таймер для запобігання миттєвій втраті всього ХП від зомбі
        self.crosshair = Crosshair() # Створення зеленого прицілу
        pygame.font.init()
        self.ui_font = pygame.font.SysFont(None, 30) # Додатковий шрифт
        
        self.current_level = 1 # Поточний поверх підземелля
        
        self.load_data() # Завантаження всіх картинок в пам'ять
    
    def load_data(self):
        # Завантаження картинок один раз на старті для уникнення лагів під час гри
        assets_folder = os.path.join(os.path.dirname(__file__), 'assets')
        sprite_sheet = pygame.image.load(os.path.join(assets_folder, 'tileset.png')).convert_alpha()

        def get_tile(x, y):
            # Функція для вирізання квадратика 32х32 з великої картинки (спрайтшита)
            tile = sprite_sheet.subsurface((x * 32, y * 32, 32, 32))
            # Масштабування квадратика до ігрового розміру TILESIZE
            return pygame.transform.scale(tile, (TILESIZE, TILESIZE))

        # Вирізання підлоги
        self.floor_img = get_tile(4, 2)

        # Вирізання фрагментів стін для системи автоматичного підбору кутів
        self.b_top = get_tile(1, 2)      # Рамка знизу (для стіни НАД підлогою)
        self.b_bot = get_tile(1, 0)      # Рамка зверху (для стіни ПІД підлогою)
        self.b_left = get_tile(2, 1)     # Рамка справа
        self.b_right = get_tile(0, 1)    # Рамка зліва
        self.c_tl = get_tile(2, 2)       # Кут знизу-справа
        self.c_tr = get_tile(0, 2)       # Кут знизу-зліва
        self.c_bl = get_tile(2, 0)       # Кут зверху-справа
        self.c_br = get_tile(0, 0)       # Кут зверху-зліва

        # Отримання кольору з куточка стіни для зафарбовування пустого фону за картою (замість чорного екрану)
        self.bg_color = self.b_top.get_at((0, 0))
        self.void_img = pygame.Surface((TILESIZE, TILESIZE))
        self.void_img.fill(self.bg_color) 
        
        def load_anim(filename):
            # Функція для розрізання довгої картинки анімації на 4 окремі кадри
            sheet = pygame.image.load(os.path.join(assets_folder, filename)).convert_alpha()
            frame_w = sheet.get_width() // 4
            frame_h = sheet.get_height()
            anim_list = []
            
            for i in range(4):
                frame = sheet.subsurface((i * frame_w, 0, frame_w, frame_h))
                temp = pygame.Surface((frame_w, frame_h), pygame.SRCALPHA)
                for x in range(frame_w):
                    for y in range(frame_h):
                        if frame.get_at((x, y))[3] > 200: 
                            temp.set_at((x, y), frame.get_at((x, y)))
                # Обрізання пустих прозорих країв для ідеального облягання картинки рамкою
                r = temp.get_bounding_rect()
                anim_list.append(frame.subsurface(r) if r.width > 0 else frame)
            return anim_list

        # Завантаження анімацій всіх ворогів
        self.zombie_anim = load_anim('zombie_walk.png')
        self.skeleton_anim = load_anim('skeleton_walk.png')
        self.archer_anim = load_anim('archer_walk.png')

        # Завантаження предметів: Аптечка
        potions_sheet = pygame.image.load(os.path.join(assets_folder, 'potions.png')).convert_alpha()
        pot_w = potions_sheet.get_width() // 6 
        pot_h = potions_sheet.get_height() // 6
        self.medkit_img = potions_sheet.subsurface((1 * pot_w, 1 * pot_h, pot_w, pot_h))
        self.medkit_img = pygame.transform.scale(self.medkit_img, (36, 36)) 

        # Завантаження предметів: Монетка
        coins_sheet = pygame.image.load(os.path.join(assets_folder, 'coin.png')).convert_alpha()
        coin_w = coins_sheet.get_width() // 6
        coin_h = coins_sheet.get_height()
        self.coin_img = coins_sheet.subsurface((2 * coin_w, 0, coin_w, coin_h))
        self.coin_img = pygame.transform.scale(self.coin_img, (32, 32))

        # Завантаження та масштабування стріли
        self.arrow_img = pygame.image.load(os.path.join(assets_folder, 'arrow.png')).convert_alpha()
        self.arrow_img = pygame.transform.scale(self.arrow_img, (20, 20))
        
        # Вирізання порталу (використовується тільки перший кадр)
        portal_sheet = pygame.image.load(os.path.join(assets_folder, 'portal.png')).convert_alpha()
        portal_w = portal_sheet.get_width() // 8
        portal_h = portal_sheet.get_height()
        self.portal_img = portal_sheet.subsurface((0, 0, portal_w, portal_h))
        self.portal_img = pygame.transform.scale(self.portal_img, (PORTAL_SIZE, PORTAL_SIZE))
        
        # Нарізання зброї
        weapons_sheet = pygame.image.load(os.path.join(assets_folder, 'weapons.png')).convert_alpha()
        w_w = weapons_sheet.get_width() // 3
        w_h = weapons_sheet.get_height() // 4
        
        # Відсікання нижньої частини картинки для уникнення артефактів
        safe_h = int(w_h * 0.7) 
        
        # Автомат
        self.machine_gun_img = weapons_sheet.subsurface((0, w_h, w_w, safe_h))
        self.machine_gun_img = pygame.transform.scale(self.machine_gun_img, (90, 45))
        
        # Дробовик
        self.shotgun_img = weapons_sheet.subsurface((w_w, w_h, w_w, safe_h))
        self.shotgun_img = pygame.transform.scale(self.shotgun_img, (90, 36))
        
        # Пістолет
        self.pistol_img = weapons_sheet.subsurface((w_w, w_h * 2, w_w, safe_h))
        self.pistol_img = pygame.transform.scale(self.pistol_img, (60, 40))
        
        # Куля (жовта)
        bul_w = weapons_sheet.get_width() // 6
        raw_bullet = weapons_sheet.subsurface((bul_w * 1, w_h * 3, bul_w, w_h))
        
        # Автоматичне обрізання пустих пікселів навколо кулі для точності влучання
        bullet_bounds = raw_bullet.get_bounding_rect() 
        self.bullet_img = raw_bullet.subsurface(bullet_bounds)
        self.bullet_img = pygame.transform.scale(self.bullet_img, (20, 8)) # Витягування в довжину
        
        # Нарізання кадрів головного героя
        player_sheet = pygame.image.load(os.path.join(assets_folder, 'player_sheet.png')).convert_alpha()
        p_w = player_sheet.get_width() // 6
        p_h = player_sheet.get_height() // 9 

        # Словник для зберігання кадрів кожного напрямку
        self.player_anim = {
            'walk_down': [], 'walk_right': [], 'walk_up': [], 'walk_left': [],
            'idle_down': [], 'idle_right': [], 'idle_up': [], 'idle_left': []
        }

        crop_x = int(p_w * 0.3)
        crop_y = int(p_h * 0.25)
        crop_w = int(p_w * 0.4)
        crop_h = int(p_h * 0.5)
        target_h = 90

        def get_frame(col, row):
            # Вирізання кадру гравця
            img = player_sheet.subsurface((col * p_w + crop_x, row * p_h + crop_y, crop_w, crop_h))
            # Обчислення оригінальних пропорцій для уникнення розтягування
            ratio = img.get_width() / img.get_height()
            target_w = int(target_h * ratio)
            return pygame.transform.scale(img, (target_w, target_h))

        for i in range(6):
            # Рух у 4 сторони
            wd = get_frame(i, 0)
            wl = get_frame(i, 1) # Базовий напрямок вліво
            wu = get_frame(i, 2)
            wr = pygame.transform.flip(wl, True, False) # Віддзеркалення лівих кадрів для руху вправо
            
            self.player_anim['walk_down'].append(wd)
            self.player_anim['walk_left'].append(wl)
            self.player_anim['walk_up'].append(wu)
            self.player_anim['walk_right'].append(wr)
            
            # Стан спокою в 4 сторони
            id_d = get_frame(i, 3)
            id_l = get_frame(i, 4) 
            id_u = get_frame(i, 5)
            id_r = pygame.transform.flip(id_l, True, False) 
            
            self.player_anim['idle_down'].append(id_d)
            self.player_anim['idle_left'].append(id_l)
            self.player_anim['idle_up'].append(id_u)
            self.player_anim['idle_right'].append(id_r)

    def draw_hud(self):
        # Відображення інтерфейсу на екрані
        health_bar_width = 200
        health_bar_height = 20
        
        # Відображення червоного фону для шкали здоров'я
        pygame.draw.rect(self.screen, RED, (10, 10, health_bar_width, health_bar_height))
        hp = max(self.player.health, 0) # Блокування візуального падіння ХП нижче нуля
        
        # Обчислення довжини зеленої смужки залежно від поточного ХП
        current_health_width = (hp / PLAYER_HEALTH) * health_bar_width
        
        # Відображення зеленої смужки
        if current_health_width > 0:
            pygame.draw.rect(self.screen, GREEN, (10, 10, current_health_width, health_bar_height))
            
        # Відображення білої рамки навколо ХП
        pygame.draw.rect(self.screen, WHITE, (10, 10, health_bar_width, health_bar_height), 2)
        
        # Вивід тексту рівня
        level_text = self.font.render(f"Рівень: {self.current_level}", True, WHITE)
        self.screen.blit(level_text, (health_bar_width + 30, 8))

        # Вивід тексту монет
        score_text = self.font.render(f"Монети: {self.score}", True, (255, 215, 0)) 
        self.screen.blit(score_text, (health_bar_width + 160, 8))

        wpn = WEAPONS[self.player.weapon]
        
        # Словник для локалізації назв зброї на екрані
        weapon_names_ua = {
            'pistol': 'ПІСТОЛЕТ',
            'shotgun': 'ДРОБОВИК',
            'machine_gun': 'АВТОМАТ'
        }
        weapon_display = weapon_names_ua.get(self.player.weapon, self.player.weapon.upper())

        # Перевірка стану перезарядки для зміни кольору тексту
        if self.player.reloading:
            ammo_text = "ПЕРЕЗАРЯДЖАННЯ..."
            text_color = RED
        else:
            # Відображення залишку патронів
            ammo_text = f"{self.player.ammo} / {wpn['mag']}"
            text_color = WHITE
            
        weapon_text = self.font.render(f"Зброя: {weapon_display} | Набої: {ammo_text}", True, text_color)
        self.screen.blit(weapon_text, (10, 40))
        
        # Спливаючі підказки (при знаходженні поруч із предметами)
        portal_hits = pygame.sprite.spritecollide(self.player, self.portals, False)
        if portal_hits: # Контакт із порталом
            prompt = self.font.render("Натисни 'E', щоб увійти в портал", True, WHITE)
            self.screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 50))
            return # Вихід з функції для запобігання накладання текстів
            
        kit_hits = pygame.sprite.spritecollide(self.player, self.health_kits, False)
        if kit_hits: # Контакт з аптечкою
            kit = kit_hits[0]
            if self.player.health >= PLAYER_HEALTH:
                prompt = self.font.render("Здоров'я повне!", True, GREY)
            elif self.score < kit.cost:
                prompt = self.font.render(f"Не вистачає монет (потрібно {kit.cost})", True, RED)
            else:
                prompt = self.font.render(f"Натисни 'E' - Купити аптечку (-{kit.cost} монет)", True, GREEN)
            self.screen.blit(prompt, (WIDTH//2 - prompt.get_width()//2, HEIGHT//2 + 50))

    def new(self, next_level=False): 
        # Запуск рівня (при старті гри або проходженні порталу)
        # Очищення всіх груп для видалення старих об'єктів з пам'яті
        self.all_sprites = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.mobs = pygame.sprite.Group()
        self.mob_projectiles = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.portals = pygame.sprite.Group()
        self.health_kits = pygame.sprite.Group()

        self.last_mob_pos = (0, 0)
        
        # Генерація нової карти 80х80 тайлів
        generator = DungeonGenerator(80, 80)
        generated_map, start_x, start_y = generator.generate()
        self.map_data = generated_map
        
        # Перевірка згенерованої карти: розстановка стін на місцях з '1'
        for row, tiles in enumerate(generated_map):
            for col, tile in enumerate(tiles):
                if tile == '1':
                    wall = Wall(self, col, row)
                    self.all_sprites.add(wall)
                    self.walls.add(wall)

        # Скидання прогресу при новій грі або його збереження при переході в портал
        if not next_level:
            self.player = Player(self)
            self.current_level = 1  
            self.score = 0          
        else: 
            self.current_level += 1 
        
        # Встановлення гравця у стартову кімнату
        self.player.rect.center = (start_x * TILESIZE, start_y * TILESIZE)
        self.player.pos = vec(self.player.rect.center)
        
        self.all_sprites.add(self.player)
        self.all_sprites.add(self.player.weapon_sprite)
        
        # Розстановка мобів у всіх кімнатах, крім стартової
        for room in generator.rooms[1:]:
            mobs_in_room = random.randint(4, 8) # Від 4 до 8 мобів на кімнату
            for _ in range(mobs_in_room):
                x = room[0] * TILESIZE + random.randint(-60, 60)
                y = room[1] * TILESIZE + random.randint(-60, 60)
                mob = Mob(self, x, y)
                self.all_sprites.add(mob)
                self.mobs.add(mob)

            # Ймовірність спавну торговця (аптечки) в кімнаті - 20%
            if random.random() > 0.8: 
                kit_grid_x = room[0]
                kit_grid_y = room[1]
                
                # Зсув аптечки при випадковому потраплянні в стіну
                if self.map_data[kit_grid_y][kit_grid_x] == '1':
                    kit_grid_x += 1
                    
                HealthKit(self, kit_grid_x * TILESIZE, kit_grid_y * TILESIZE)

        # Створення камери
        self.camera = Camera(80 * TILESIZE, 80 * TILESIZE)
        pygame.mouse.set_visible(False) # Приховування системного курсора миші
            
    def events(self):
        # Зчитування натискань кнопок гравцем
        for event in pygame.event.get():
            # Обробка натискання на хрестик вікна
            if event.type == pygame.QUIT:
                self.playing = False
                self.running = False
                import sys
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                # Обробка натискання Escape
                if event.key == pygame.K_ESCAPE:
                    self.playing = False
                    self.running = False
                    import sys
                    pygame.quit()
                    sys.exit()
                    
                # Зміна зброї кнопками 1, 2, 3
                if event.key == pygame.K_1 and self.player.weapon != 'pistol':
                    self.player.weapon = 'pistol'
                    self.player.ammo = WEAPONS['pistol']['mag']
                    self.player.reloading = False
                if event.key == pygame.K_2 and self.player.weapon != 'shotgun':
                    self.player.weapon = 'shotgun'
                    self.player.ammo = WEAPONS['shotgun']['mag']
                    self.player.reloading = False
                if event.key == pygame.K_3 and self.player.weapon != 'machine_gun':
                    self.player.weapon = 'machine_gun'
                    self.player.ammo = WEAPONS['machine_gun']['mag']
                    self.player.reloading = False
                
                # Запуск перезарядки клавішею R
                if event.key == pygame.K_r and not self.player.reloading:
                    if self.player.ammo < WEAPONS[self.player.weapon]['mag']:
                        self.player.reloading = True
                        self.player.reload_start_time = pygame.time.get_ticks()
                        
                # Клавіша взаємодії (E)
                if event.key == pygame.K_e:
                    # Купівля аптечки
                    kit_hits = pygame.sprite.spritecollide(self.player, self.health_kits, False)
                    for kit in kit_hits:
                        if self.score >= kit.cost and self.player.health < PLAYER_HEALTH:
                            self.score -= kit.cost
                            self.player.health = min(self.player.health + kit.heal_amount, PLAYER_HEALTH)
                            kit.kill() # Видалення аптечки з карти
                            break 
                            
                    # Вхід у портал
                    portal_hits = pygame.sprite.spritecollide(self.player, self.portals, False)
                    if portal_hits:
                        self.score += 25 # Бонусні бали за проходження рівня
                        self.new(next_level=True) # Перехід на наступний рівень

    def update(self):
        # Оновлення позицій усіх об'єктів (гравець, моби, кулі)
        self.all_sprites.update()
        self.camera.update(self.player) # Рух камери за гравцем
        self.crosshair.update() # Рух прицілу за мишкою
        
        # Щоб не шукати останніх мобів по всій карті - вони самі біжать до гравця
        if 0 < len(self.mobs) <= 3:
            for mob in self.mobs:
                if mob.state == 'IDLE':
                    mob.state = 'ACTIVE'
        
        # Перевірка всіх зіткнень
        self.check_collisions()

    def check_collisions(self):
        # 1. Влучання куль гравця у ворогів
        # Перевірка колізій між групами об'єктів (True - видалення кулі при влучанні)
        hits = pygame.sprite.groupcollide(self.mobs, self.bullets, False, True)
        for mob, bullets_hit in hits.items():
            if mob.state == 'ACTIVE':
                # Сумування урону від всіх влучених куль (важливо для дробовика)
                total_damage = sum([b.damage for b in bullets_hit])
                mob.health -= total_damage
                mob.is_hit = True # Зміна кольору моба на червоний
                mob.hit_timer = pygame.time.get_ticks()
                
                # Відкидання моба при влучанні
                b = bullets_hit[0] 
                if b.vel.length() > 0:
                    knockback_dir = b.vel.normalize() # Визначення напрямку кулі
                    
                    # Горизонтальне відкидання та перевірка стін
                    mob.pos.x += knockback_dir.x * 15
                    mob.hitbox.centerx = mob.pos.x
                    for wall in self.walls:
                        if mob.hitbox.colliderect(wall.rect):
                            if knockback_dir.x > 0: mob.hitbox.right = wall.rect.left
                            if knockback_dir.x < 0: mob.hitbox.left = wall.rect.right
                            mob.pos.x = mob.hitbox.centerx
                            
                    # Вертикальне відкидання та перевірка стін
                    mob.pos.y += knockback_dir.y * 15
                    mob.hitbox.centery = mob.pos.y
                    for wall in self.walls:
                        if mob.hitbox.colliderect(wall.rect):
                            if knockback_dir.y > 0: mob.hitbox.bottom = wall.rect.top
                            if knockback_dir.y < 0: mob.hitbox.top = wall.rect.bottom
                            mob.pos.y = mob.hitbox.centery
                            
                    mob.rect.center = mob.hitbox.center
                
                # Смерть моба
                if mob.health <= 0:
                    self.last_mob_pos = (mob.rect.centerx, mob.rect.centery) # Збереження місця смерті
                    mob.kill() # Видалення об'єкта
                    
                    # Спавн монетки з імовірністю 15%
                    if random.random() < 0.15:
                        coin = Coin(self, mob.rect.centerx, mob.rect.centery)
                        self.all_sprites.add(coin)
                        self.coins.add(coin)
                        
                    # Спавн порталу на місці останнього вбитого моба
                    if len(self.mobs) == 0 and len(self.portals) == 0:
                        portal = Portal(self, self.last_mob_pos[0], self.last_mob_pos[1])
                        self.all_sprites.add(portal)
                        self.portals.add(portal)

        # 2. Влучання ворожих куль у гравця
        proj_hits = pygame.sprite.spritecollide(self.player, self.mob_projectiles, True)
        for hit in proj_hits:
            self.player.health -= 10 # Втрата ХП
            if self.player.health <= 0:
                self.show_go_screen() # Перехід на екран поразки

        # 3. Ближній бій (контакт моба з гравцем)
        player_hits = pygame.sprite.spritecollide(self.player, self.mobs, False)
        if player_hits:
            active_hits = [m for m in player_hits if m.state == 'ACTIVE']
            if active_hits:
                current_time = pygame.time.get_ticks()
                # Таймер невразливості (для запобігання миттєвій смерті від одного контакту)
                if current_time - self.damage_timer > 1000:
                    self.damage_timer = current_time
                    self.player.health -= MOB_DAMAGE * active_hits[0].damage_mult
                    
                    # Відкидання гравця від удару моба
                    dir_to_mob = vec(self.player.rect.center) - vec(active_hits[0].rect.center)
                    if dir_to_mob.length() > 0:
                        dir_vector = dir_to_mob.normalize()
                        
                        move_x = dir_vector.x * MOB_KNOCKBACK
                        self.player.rect.x += move_x
                        hits_x = pygame.sprite.spritecollide(self.player, self.walls, False)
                        if hits_x:
                            if move_x > 0: self.player.rect.right = hits_x[0].rect.left
                            if move_x < 0: self.player.rect.left = hits_x[0].rect.right

                        move_y = dir_vector.y * MOB_KNOCKBACK
                        self.player.rect.y += move_y
                        hits_y = pygame.sprite.spritecollide(self.player, self.walls, False)
                        if hits_y:
                            if move_y > 0: self.player.rect.bottom = hits_y[0].rect.top
                            if move_y < 0: self.player.rect.top = hits_y[0].rect.bottom
                            
                    if self.player.health <= 0:
                        self.show_go_screen()

        # 4. Збір монет (контакт гравця з монетою)
        coin_hits = pygame.sprite.spritecollide(self.player, self.coins, True)
        for hit in coin_hits:
            self.score += 10 # Збільшення рахунку

    def draw(self):
        self.screen.fill(self.bg_color) # Очищення фону
        
        # Відображення підлоги зі зміщенням камери
        class CameraTarget:
            def __init__(self, rect):
                self.rect = rect

        for row, tiles in enumerate(self.map_data):
            for col, tile in enumerate(tiles):
                if tile == '0': # Якщо це підлога
                    tile_rect = pygame.Rect(col * TILESIZE, row * TILESIZE, TILESIZE, TILESIZE)
                    target = CameraTarget(tile_rect)
                    # Малювання плитки підлоги
                    self.screen.blit(self.floor_img, self.camera.apply(target))

        # Малювання всіх об'єктів (моби, гравець, кулі)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite))
            
            # Відображення шкали здоров'я над мобами
            if hasattr(sprite, 'state') and getattr(sprite, 'state') == 'ACTIVE':
                max_hp = MOB_TYPES[sprite.mob_type]['health']
                hp_ratio = max(0, sprite.health / max_hp)

                mob_screen_rect = self.camera.apply(sprite)
                bar_width = mob_screen_rect.width
                bar_height = 5

                pygame.draw.rect(self.screen, RED, (mob_screen_rect.left, mob_screen_rect.top - 10, bar_width, bar_height))
                pygame.draw.rect(self.screen, GREEN, (mob_screen_rect.left, mob_screen_rect.top - 10, bar_width * hp_ratio, bar_height))

        self.draw_hud() # Відображення інтерфейсу
        self.screen.blit(self.crosshair.image, self.crosshair.rect) # Відображення прицілу
        pygame.display.flip() # Вивід кадру на екран

    def show_start_screen(self):
        # Головне меню
        self.screen.fill((20, 20, 25))
        
        title_font = pygame.font.SysFont("Arial", 64, bold=True)
        title_text = title_font.render("ROGUELIKE DIPLOM", True, (255, 215, 0))
        prompt_text = self.font.render("Натисни ПРОБІЛ, щоб почати", True, WHITE)
        ctrl_text = self.ui_font.render("WASD - Рух | Миша - Приціл | 1, 2, 3 - Зміна зброї | E - Дія", True, (150, 150, 150))
        
        self.screen.blit(title_text, (WIDTH//2 - title_text.get_width()//2, HEIGHT//2 - 100))
        self.screen.blit(prompt_text, (WIDTH//2 - prompt_text.get_width()//2, HEIGHT//2 + 20))
        self.screen.blit(ctrl_text, (WIDTH//2 - ctrl_text.get_width()//2, HEIGHT - 50))
        
        pygame.display.flip()
        self.wait_for_key() # Очікування натискання клавіші

    def show_go_screen(self):
        # Екран завершення гри (ВИТРАЧЕНО)
        pygame.mouse.set_visible(True) 
        self.screen.fill((20, 20, 25)) 
        
        title_font = pygame.font.SysFont("Arial", 64, bold=True)
        text1 = title_font.render("ВИТРАЧЕНО", True, RED)
        
        # Відображення результатів (монети і рівень)
        score_text = self.font.render(f"Досягнуто рівень: {self.current_level}  |  Зібрано монет: {self.score}", True, (255, 215, 0))
        text2 = self.font.render("Натисни ПРОБІЛ для рестарту", True, WHITE)
        
        self.screen.blit(text1, (WIDTH//2 - text1.get_width()//2, HEIGHT//2 - 100))
        self.screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, HEIGHT//2))
        self.screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2 + 80))
        
        pygame.display.flip()
        self.wait_for_key()

    def wait_for_key(self):
        # Пауза до натискання Пробілу
        waiting = True
        while waiting:
            self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.running = False
                    self.playing = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        waiting = False
                        self.playing = False

    def run(self):
        # Ігровий цикл
        self.playing = True
        while self.playing:
            # Обчислення дельта-тайм для однакової швидкості гри на різних ПК
            self.dt = self.clock.tick(FPS) / 1000.0 
            
            # Обмеження dt при сильних лагах
            if self.dt > 0.05:
                self.dt = 0.05
                
            self.events()    # Обробка натискань кнопок
            self.update()    # Оновлення позицій
            self.draw()      # Відображення кадру

class HealthKit(pygame.sprite.Sprite):
    # Клас аптечки
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.health_kits
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.medkit_img 
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.cost = 50          # Ціна відновлення
        self.heal_amount = 30   # Кількість відновленого ХП

# Точка входу в програму. Звідси починається виконання.
if __name__ == "__main__":
    game = Game()               # Створення об'єкта гри
    game.show_start_screen()    # Відображення меню
    while game.running:         # Головний цикл роботи програми
        game.new()              # Генерація рівня
        game.run()              # Запуск ігрового процесу
    pygame.quit()               # Закриття Pygame
    sys.exit()                  # Закриття вікна