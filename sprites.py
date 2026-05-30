import pygame      # Головна бібліотека для малювання графіки
import random      # Бібліотека для генерації випадкових чисел
from settings import *  # Завантаження констант (кольори, швидкість, розміри)
from pathfinding import astar  # Алгоритм пошуку шляху для об'єктів штучного інтелекту

# Створення короткої назви для векторів. Вектор використовується для 
# математичного розрахунку напрямку та довжини руху або стрільби.
vec = pygame.math.Vector2

class PlayerWeapon(pygame.sprite.Sprite):
    """Клас для відображення та керування зброєю в руках гравця"""
    def __init__(self, game, player):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.player = player
        self.image = self.game.pistol_img # Початкова зброя — пістолет
        self.rect = self.image.get_rect()
        
    def update(self):
        # 1. Оновлення зображення зброї залежно від вибору гравця
        if self.player.weapon == 'pistol': base_img = self.game.pistol_img
        elif self.player.weapon == 'shotgun': base_img = self.game.shotgun_img
        else: base_img = self.game.machine_gun_img
            
        # 2. Розрахунок прицілювання: обчислення вектора від гравця до курсора миші
        mouse_pos = pygame.mouse.get_pos()
        # Врахування координат камери для коректного прицілювання при переміщенні по карті
        target_pos = vec(mouse_pos[0] - self.game.camera.camera.x, mouse_pos[1] - self.game.camera.camera.y)
        player_pos = vec(self.player.rect.center)
        
        # Обчислення кута повороту між гравцем та мишею
        dir_vector = target_pos - player_pos
        angle = dir_vector.angle_to(vec(1, 0))
        
        # 3. Візуальна корекція: дзеркальне відображення зброї, якщо миша ліворуч від гравця
        if target_pos.x < player_pos.x:
            base_img = pygame.transform.flip(base_img, False, True)
            
        # Поворот зображення на розрахований кут
        self.image = pygame.transform.rotate(base_img, angle)
        
        # 4. Центрування зброї з невеликим відступом від центру спрайту гравця
        offset = dir_vector.normalize() * 20 if dir_vector.length() > 0 else vec(20, 0)
        self.rect = self.image.get_rect(center=player_pos + offset)

class Player(pygame.sprite.Sprite):
    """Головний клас персонажа. Керує рухом, колізіями, стрільбою та анімацією."""
    def __init__(self, game):
        super().__init__()
        self.game = game
        
        # --- СИСТЕМА АНІМАЦІЇ ---
        self.anim = self.game.player_anim  # Отримання кадрів анімації з головного файлу
        self.current_frame = 0             # Поточний індекс кадру
        self.last_update = pygame.time.get_ticks() # Час останнього оновлення зображення
        self.facing = 'down'               # Напрямок погляду персонажа
        self.state = 'idle'                # Поточний стан: спокій (idle) або рух (walk)
        
        self.image = self.anim['idle_down'][0] # Встановлення початкового кадру
        
        # --- ФІЗИЧНА ТА ВІЗУАЛЬНА МОДЕЛІ ---
        # self.rect — візуальна рамка для відображення картинки.
        self.rect = self.image.get_rect() 
        # self.hitbox — фізична рамка (40х40) для розрахунку зіткнень. 
        # Зменшений розмір дозволяє вільніше проходити через вузькі проходи.
        self.hitbox = pygame.Rect(0, 0, 40, 40) 

        self.health = PLAYER_HEALTH
        self.vx, self.vy = 0, 0 # Поточна швидкість по осях
        self.pos = vec(0, 0)    # Точні координати позиції
        
        # Параметри стрільби
        self.weapon = 'pistol'
        self.last_shot = 0
        self.ammo = WEAPONS[self.weapon]['mag']
        self.reloading = False
        self.reload_start_time = 0
        
        # Створення та прив'язка об'єкта зброї
        self.weapon_sprite = PlayerWeapon(game, self)

    def update(self):
        # Оновлення швидкості на основі натискання клавіш WASD
        self.vx, self.vy = 0, 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]: self.vx = -PLAYER_SPEED
        if keys[pygame.K_d]: self.vx = PLAYER_SPEED
        if keys[pygame.K_w]: self.vy = -PLAYER_SPEED
        if keys[pygame.K_s]: self.vy = PLAYER_SPEED
        
        # Корекція діагональної швидкості: множення на 0.7071 для збереження 
        # однакової швидкості руху по прямій та по діагоналі.
        if self.vx != 0 and self.vy != 0:
            self.vx *= 0.7071
            self.vy *= 0.7071
            
        # Визначення напрямку для вибору відповідної анімації
        if self.vx > 0: self.facing = 'right'
        elif self.vx < 0: self.facing = 'left'
        elif self.vy > 0: self.facing = 'down'
        elif self.vy < 0: self.facing = 'up'
        
        # Встановлення стану руху залежно від наявності швидкості
        self.state = 'walk' if (self.vx != 0 or self.vy != 0) else 'idle'
            
        # Оновлення кадрів анімації з інтервалом у 120 мілісекунд
        now = pygame.time.get_ticks()
        if now - self.last_update > 120: 
            self.last_update = now
            self.current_frame = (self.current_frame + 1) % 6
            self.image = self.anim[f'{self.state}_{self.facing}'][self.current_frame]

        # --- РОЗРАХУНОК РУХУ ТА ЗІТКНЕНЬ ---
        # Горизонтальне переміщення та перевірка зіткнень зі стінами
        self.pos.x += self.vx * self.game.dt
        self.hitbox.centerx = self.pos.x
        self.collide_with_walls('x') 
        
        # Вертикальне переміщення та перевірка зіткнень
        self.pos.y += self.vy * self.game.dt
        self.hitbox.centery = self.pos.y
        self.collide_with_walls('y') 
        
        # Синхронізація візуального спрайту з позицією фізичного хітбокса
        self.rect.center = self.hitbox.center
        
        self.shoot() # Виклик методу стрільби

    def collide_with_walls(self, dir):
        """Обробка зіткнень з об'єктами групи walls (алгоритм AABB)"""
        if dir == 'x':
            for wall in self.game.walls:
                if self.hitbox.colliderect(wall.rect):
                    if self.vx > 0: self.hitbox.right = wall.rect.left # Зупинка перед стіною справа
                    if self.vx < 0: self.hitbox.left = wall.rect.right # Зупинка перед стіною зліва
                    self.vx = 0
                    self.pos.x = self.hitbox.centerx
        if dir == 'y':
            for wall in self.game.walls:
                if self.hitbox.colliderect(wall.rect):
                    if self.vy > 0: self.hitbox.bottom = wall.rect.top    # Зупинка перед стіною знизу
                    if self.vy < 0: self.hitbox.top = wall.rect.bottom    # Зупинка перед стіною зверху
                    self.vy = 0
                    self.pos.y = self.hitbox.centery

    def shoot(self):
        """Керування стрільбою: перевірка боєзапасу, перезарядки та створення куль"""
        now = pygame.time.get_ticks()
        wpn = WEAPONS[self.weapon] 
        
        # Перевірка статусу та завершення часу перезарядки
        if self.reloading:
            if now - self.reload_start_time > wpn['reload']:
                self.reloading = False
                self.ammo = wpn['mag'] 
            return

        mouse_pressed = pygame.mouse.get_pressed()
        if mouse_pressed[0]: # Спроба пострілу при натисканні лівої кнопки миші
            if self.ammo > 0:
                if now - self.last_shot > wpn['rate']: # Перевірка темпу стрільби
                    self.last_shot = now
                    self.ammo -= 1 
                    
                    if self.ammo == 0: # Автоматичний початок перезарядки при порожньому магазині
                        self.reloading = True
                        self.reload_start_time = now
                        # Відтворення звуку при порожньому магазині
                        self.game.snd_reload.play()

                    # Розрахунок вектора напрямку кулі відносно камери
                    mouse_pos = pygame.mouse.get_pos()
                    mouse_world_x = mouse_pos[0] - self.game.camera.camera.x
                    mouse_world_y = mouse_pos[1] - self.game.camera.camera.y
                    
                    player_pos = vec(self.rect.center)
                    target_pos = vec(mouse_world_x, mouse_world_y)
                    dir_vector = target_pos - player_pos
                    
                    if dir_vector.length() > 0: 
                        # Відтворення звуку пострілу
                        self.game.snd_shoot.play()
                        dir_vector = dir_vector.normalize() 
                        # Генерація заданої кількості куль (використовується для дробовика)
                        for _ in range(wpn['count']):
                            # Застосування випадкового розкиду (spread)
                            spread = random.uniform(-wpn['spread'], wpn['spread'])
                            bullet_dir = dir_vector.rotate(spread)
                            
                            # Розрахунок точки появи кулі з урахуванням довжини зброї (barrel offset)
                            barrel_offset = 45 if self.weapon in ['shotgun', 'machine_gun'] else 30
                            spawn_pos = vec(self.weapon_sprite.rect.center) + bullet_dir * barrel_offset
                            
                            # Створення та додавання кулі в ігрові групи
                            bullet = Bullet(self.game, spawn_pos, bullet_dir, wpn['damage'])
                            self.game.all_sprites.add(bullet)
                            self.game.bullets.add(bullet)
            else: # Активація перезарядки при спробі стрільби без патронів
                self.reloading = True
                self.reload_start_time = now
                # Відтворення звуку при спробі вистрілити без набоїв
                self.game.snd_reload.play()

class Wall(pygame.sprite.Sprite):
    """Клас стіни з підтримкою автоматичного вибору текстури (автотайлінг)"""
    def __init__(self, game, x, y):
        self.groups = game.all_sprites, game.walls
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = game.void_img 

        max_y = len(game.map_data) - 1
        max_x = len(game.map_data[0]) - 1

        def is_floor(dx, dy):
            # Перевірка наявності підлоги за відносними координатами
            nx, ny = x + dx, y + dy
            if 0 <= ny <= max_y and 0 <= nx <= max_x:
                # ТЕПЕР СТІНА БАЧИТЬ І ПІДЛОГУ, І БОЧКУ
                return game.map_data[ny][nx] in ['0', 'X'] 
            return False

        # Аналіз сусідніх клітинок для визначення типу текстури стіни
        f_d = is_floor(0, 1)   # Знизу
        f_u = is_floor(0, -1)  # Зверху
        f_r = is_floor(1, 0)   # Праворуч
        f_l = is_floor(-1, 0)  # Ліворуч

        # Вибір відповідного зображення (кути або прямі ділянки)
        if f_d and f_r:
            self.image = game.c_tl
        elif f_d and f_l:
            self.image = game.c_tr
        elif f_u and f_r:
            self.image = game.c_bl
        elif f_u and f_l:
            self.image = game.c_br
        elif f_d:
            self.image = game.b_top
        elif f_u:
            self.image = game.b_bot
        elif f_r:
            self.image = game.b_left
        elif f_l:
            self.image = game.b_right

        self.rect = self.image.get_rect()
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Floor(pygame.sprite.Sprite):
    """Базовий клас плитки підлоги"""
    def __init__(self, game, x, y):
        self.groups = game.all_sprites
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = pygame.Surface((TILESIZE, TILESIZE))
        self.image.fill((40, 40, 45)) 
        pygame.draw.rect(self.image, (30, 30, 35), (0, 0, TILESIZE, TILESIZE), 1)
        self.rect = self.image.get_rect()
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Obstacle(pygame.sprite.Sprite):
    def __init__(self, game, x, y):
        # Добавляем в группу walls, чтобы об нее бились пули, мобы и игрок
        self.groups = game.all_sprites, game.walls
        pygame.sprite.Sprite.__init__(self, self.groups)
        self.game = game
        self.image = self.game.barrel_img
        self.rect = self.image.get_rect()
        
        # Координаты по ігровій сітці
        self.x = x
        self.y = y
        self.rect.x = x * TILESIZE
        self.rect.y = y * TILESIZE

class Bullet(pygame.sprite.Sprite):
    """Клас снаряда гравця"""
    def __init__(self, game, pos, dir, damage):
        super().__init__()
        self.game = game
        
        # Поворот зображення кулі відповідно до напрямку польоту
        angle = dir.angle_to(vec(1, 0))
        self.image = pygame.transform.rotate(self.game.bullet_img, angle)
        
        self.rect = self.image.get_rect(center=pos)
        self.pos = vec(pos)
        self.vel = dir * BULLET_SPEED # Встановлення вектора швидкості
        self.spawn_time = pygame.time.get_ticks()
        self.damage = damage

    def update(self):
        # Переміщення кулі з урахуванням дельта-тайму (dt)
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        
        # Знищення об'єкта при зіткненні зі стіною
        if pygame.sprite.spritecollideany(self, self.game.walls):
            self.kill()
            
        # Знищення об'єкта після закінчення встановленого часу життя
        if pygame.time.get_ticks() - self.spawn_time > BULLET_LIFETIME:
            self.kill()

class MobProjectile(pygame.sprite.Sprite):
    """Клас снаряда ворога (наприклад, стріла)"""
    def __init__(self, game, pos, dir):
        super().__init__()
        self.game = game
        self.pos = vec(pos)
        self.vel = dir * MOB_PROJECTILE_SPEED
        self.spawn_time = pygame.time.get_ticks()
        
        # Поворот зображення снаряда
        angle = self.vel.angle_to(vec(1, 0)) 
        self.image = pygame.transform.rotate(self.game.arrow_img, angle)
        
        self.rect = self.image.get_rect(center=pos)

    def update(self):
        self.pos += self.vel * self.game.dt
        self.rect.center = self.pos
        
        if pygame.sprite.spritecollideany(self, self.game.walls):
            self.kill()
        if pygame.time.get_ticks() - self.spawn_time > MOB_PROJECTILE_LIFETIME:
            self.kill()

class Mob(pygame.sprite.Sprite):
    """Клас ворога з логікою пошуку шляху та станами поведінки"""
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        # Випадковий вибір типу моба
        self.mob_type = random.choice(list(MOB_TYPES.keys()))
        stats = MOB_TYPES[self.mob_type] 
        
        self.base_type = stats['type'] 
        self.speed = stats['speed']
        # --- МАСШТАБУВАННЯ СКЛАДНОСТІ ---
        base_hp = stats['health']
        self.health = int(base_hp * self.game.difficulty) # Множення ХП на складність
        
        self.color = stats['color']
        
        self.size = 45 # Візуальний розмір
        self.damage_mult = self.game.difficulty # Множення шкоди від моба на складність
        self.last_shot = 0

        # --- СИСТЕМА АНІМАЦІЇ ВОРОГІВ ---
        self.has_animation = True
        self.frames = []
        
        if self.mob_type == 'zombie':
            raw_anim = game.zombie_anim
        elif self.mob_type == 'skeleton':
            raw_anim = game.skeleton_anim
        elif self.mob_type == 'archer':
            raw_anim = game.archer_anim

        # Масштабування кадрів анімації
        for img in raw_anim:
            scale = self.size / img.get_height()
            new_w = int(img.get_width() * scale)
            new_h = int(img.get_height() * scale)
            self.frames.append(pygame.transform.scale(img, (new_w, new_h)))
            
        self.current_frame = 0
        self.last_update = pygame.time.get_ticks()
        self.frame_rate = 150 

        self.image = self.frames[0].copy() 
        self.rect = self.image.get_rect(center=(x, y))
        
        # Фізичний хітбокс (менший за розмір тайлу)
        self.hitbox = pygame.Rect(0, 0, 40, 40)
        self.hitbox.center = self.rect.center
        
        self.pos = vec(x, y)
        self.state = 'IDLE' # Початковий стан спокою
        self.is_hit = False
        self.hit_timer = 0
        self.path = [] # Список точок маршруту (алгоритм A*)
        # Випадкове зміщення таймера для розподілу обчислювального навантаження
        self.last_path_time = pygame.time.get_ticks() + random.randint(0, 500) 

    def update(self):
        player_pos = vec(self.game.player.rect.center)
        dist_to_player = self.pos.distance_to(player_pos) 
        now = pygame.time.get_ticks()
        
        # Синхронізація позиції хітбокса та візуальної рамки
        self.hitbox.center = self.pos
        self.rect.center = self.hitbox.center
        
        # --- ЛОГІКА СТАНІВ ---
        if self.state == 'IDLE':
            self.image = self.frames[0].copy()
            # Активація моба при наближенні гравця або отриманні шкоди
            if dist_to_player < SPAWN_RADIUS or self.is_hit:
                self.state = 'ACTIVE' 
                # Віднімаємо 1000 мс. Тепер затримка буде лише ~0.5 секунди
                self.last_shot = now - 1000
                
        elif self.state == 'ACTIVE':
            # Оновлення кадрів анімації
            if now - self.last_update > self.frame_rate:
                self.last_update = now
                self.current_frame = (self.current_frame + 1) % len(self.frames)
            
            self.image = self.frames[self.current_frame].copy()
            
            # Візуальний ефект отримання шкоди
            if self.is_hit:
                self.image.fill((255, 0, 0, 100), special_flags=pygame.BLEND_RGBA_MULT)
                if now - self.hit_timer > 100:
                    self.is_hit = False

            # --- НАВІГАЦІЯ ---
            move_dir = vec(0, 0)
            # Оновлення маршруту кожні 500 мілісекунд
            if now - self.last_path_time > 500:
                self.last_path_time = now + random.randint(-100, 100) 
                if dist_to_player < 800: 
                    start_cell = (int(self.pos.x // TILESIZE), int(self.pos.y // TILESIZE))
                    goal_cell = (int(player_pos.x // TILESIZE), int(player_pos.y // TILESIZE))
                    if start_cell != goal_cell:
                        # Розрахунок шляху в обхід перешкод
                        new_path = astar(self.game.map_data, start_cell, goal_cell)
                        if new_path and len(new_path) > 1: self.path = new_path[1:] 
                        else: self.path = []
                else: self.path = []

            # Переміщення за списком точок маршруту
            if self.path:
                target_cell = self.path[0]
                target_pixel = vec(target_cell[0] * TILESIZE + TILESIZE // 2, 
                                   target_cell[1] * TILESIZE + TILESIZE // 2)
                dir_vector = target_pixel - self.pos
                if dir_vector.length() > 0: move_dir = dir_vector.normalize()
                
                # Видалення точки зі списку при досягненні її центру
                if self.pos.distance_to(target_pixel) < (self.speed * self.game.dt * 1.5):
                    self.path.pop(0)
            else:
                # Прямий рух до гравця у разі відсутності складного маршруту
                dir_vector = (player_pos - self.pos)
                if dir_vector.length() > 0: move_dir = dir_vector.normalize()

            # Спеціальна поведінка для ворогів далекого бою
            if self.base_type == 'ranged':
                # Підтримання дистанції від гравця (відступ)
                if dist_to_player < 200: move_dir = -move_dir 
                
                # Періодична стрільба
                if now - self.last_shot > MOB_TYPES['archer']['shoot_rate']:
                    # ВИПРАВЛЕНО: Перевірка прямої видимості перед пострілом
                    if self.has_line_of_sight(player_pos):
                        self.last_shot = now
                        shoot_dir = (player_pos - self.pos).normalize() if (player_pos - self.pos).length() > 0 else vec(1, 0)
                        proj = MobProjectile(self.game, self.rect.center, shoot_dir)
                        self.game.all_sprites.add(proj)
                        self.game.mob_projectiles.add(proj)

            # Виконання переміщення
            if move_dir.length() > 0:
                self.move(move_dir)
    
    def has_line_of_sight(self, target_pos):
        """Перевірка прямої видимості: пускає промінь до гравця і шукає стіни чи бочки"""
        start = self.pos
        target = vec(target_pos)
        direction = target - start
        dist = direction.length()
        
        if dist == 0: 
            return True
            
        direction = direction.normalize()
        step = 20  # Перевіряємо кожні 20 пікселів (половина тайлу)
        current_dist = 0
        
        while current_dist < dist:
            check_point = start + direction * current_dist
            map_x = int(check_point.x // TILESIZE)
            map_y = int(check_point.y // TILESIZE)
            
            # Перевірка, чи не потрапив промінь у стіну ('1') або бочку ('X')
            if 0 <= map_y < len(self.game.map_data) and 0 <= map_x < len(self.game.map_data[0]):
                if self.game.map_data[map_y][map_x] in ['1', 'X']:
                    return False  # Перешкода знайдена, видимості немає
            
            current_dist += step
            
        return True  # Шлях чистий

    def move(self, direction):
        """Метод переміщення моба з обробкою зіткнень"""
        step = direction * self.speed * self.game.dt
        
        self.pos.x += step.x
        self.hitbox.centerx = self.pos.x
        for wall in self.game.walls:
            if self.hitbox.colliderect(wall.rect):
                if step.x > 0: self.hitbox.right = wall.rect.left
                if step.x < 0: self.hitbox.left = wall.rect.right
                self.pos.x = self.hitbox.centerx
                
        self.pos.y += step.y
        self.hitbox.centery = self.pos.y
        for wall in self.game.walls:
            if self.hitbox.colliderect(wall.rect):
                if step.y > 0: self.hitbox.bottom = wall.rect.top
                if step.y < 0: self.hitbox.top = wall.rect.bottom
                self.pos.y = self.hitbox.centery
                
        self.rect.center = self.hitbox.center
class Coin(pygame.sprite.Sprite):
    """Спрайт ігрової валюти"""
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = self.game.coin_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

class Portal(pygame.sprite.Sprite):
    """Об'єкт переходу на наступний рівень"""
    def __init__(self, game, x, y):
        super().__init__()
        self.game = game
        self.image = self.game.portal_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

class Crosshair(pygame.sprite.Sprite):
    """Графічний приціл, що замінює системний курсор"""
    def __init__(self):
        super().__init__()
        # Створення прозорої поверхні
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        # Малювання перехрестя
        pygame.draw.line(self.image, (0, 255, 0), (10, 0), (10, 20), 2)
        pygame.draw.line(self.image, (0, 255, 0), (0, 10), (20, 10), 2)
        self.rect = self.image.get_rect()

    def update(self):
        # Оновлення позиції відповідно до координат миші
        self.rect.center = pygame.mouse.get_pos()