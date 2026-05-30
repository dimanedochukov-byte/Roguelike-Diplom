import random # Бібліотека для генерації випадкових значень (розміри та координати)
import math   # Бібліотека для математичних розрахунків (дистанція між об'єктами)

class DungeonGenerator:
    """
    Клас для процедурної генерації карти підземелля. 
    Відповідає за створення кімнат та їх логічне поєднання коридорами.
    """
    def __init__(self, width, height):
        # Встановлення розмірів карти в тайлах (клітинках)
        self.width = width
        self.height = height
        
        # Створення двовимірної матриці. 
        # Початкове заповнення всіх клітинок символом '1' (суцільна стіна).
        self.map = [['1' for _ in range(width)] for _ in range(height)]
        
        self.rooms = [] # Список для збереження координат центрів кімнат
        self._rect_rooms = [] # Список для збереження меж кімнат (для запобігання накладанню)

    def generate(self):
        
        
        # Визначення кількості кімнат (випадково від 8 до 12)
        num_rooms = random.randint(8, 12) 
        min_size = 10  # Мінімальна довжина сторони кімнати
        max_size = 16  # Максимальна довжина сторони кімнати

        # Спроби розміщення кімнат. Використовується запас ітерацій, 
        # оскільки частина спроб буде відхилена через перетин.
        for _ in range(num_rooms * 5): 
            w = random.randint(min_size, max_size) # Випадкова ширина
            h = random.randint(min_size, max_size) # Випадкова висота
            
            # Випадковий вибір координат лівого верхнього кута (з відступом від країв карти)
            x = random.randint(2, self.width - w - 2)
            y = random.randint(2, self.height - h - 2)

            new_room = (x, y, w, h) # Тимчасовий об'єкт кімнати
            
            # Перевірка перетину з уже побудованими об'єктами
            failed = False
            for other_room in self._rect_rooms:
                if self._intersect(new_room, other_room): 
                    failed = True 
                    break
            
            # Додавання кімнати до карти, якщо перетинів не виявлено
            if not failed:
                self._create_room(new_room) # Заміна стін на підлогу ('0') в матриці
                self._rect_rooms.append(new_room) 
                
                # Розрахунок центру кімнати для подальшого прокладання коридорів
                center_x = x + w // 2
                center_y = y + h // 2
                self.rooms.append((center_x, center_y)) 

        #  (АЛГОРИТМ НАЙБЛИЖЧОГО СУСІДА) 
        
        if len(self.rooms) > 1:
            # Поділ кімнат на "підключені" та "непідключені"
            connected = [self.rooms[0]]
            unconnected = self.rooms[1:]
            
            # Побудова зв'язків, поки список непідключених кімнат не стане порожнім
            while unconnected:
                best_dist = float('inf') # Початкове значення відстані (нескінченність)
                best_pair = (None, None) # Пара координат для з'єднання
                
                # Пошук найкоротшої дистанції між підключеними та непідключеними об'єктами
                for c_room in connected:
                    for u_room in unconnected:
                        # Обчислення прямої відстані за теоремою Піфагора
                        dist = math.hypot(c_room[0] - u_room[0], c_room[1] - u_room[1])
                        if dist < best_dist:
                            best_dist = dist 
                            best_pair = (c_room, u_room) 
                            
                prev_center = best_pair[0] 
                curr_center = best_pair[1] 
                
                # Створення Г-подібного проходу (тунелю). Випадковий вибір порядку осей (X або Y).
                if random.randint(0, 1) == 1:
                    self._create_h_tunnel(prev_center[0], curr_center[0], prev_center[1])
                    self._create_v_tunnel(prev_center[1], curr_center[1], curr_center[0])
                else:
                    self._create_v_tunnel(prev_center[1], curr_center[1], prev_center[0])
                    self._create_h_tunnel(prev_center[0], curr_center[0], curr_center[1])
                    
                # Оновлення списків після успішного з'єднання
                connected.append(curr_center)
                unconnected.remove(curr_center)

        # --- ЕТАП 3: ОПТИМІЗАЦІЯ ГЕОМЕТРІЇ (ВИДАЛЕННЯ ТОНКИХ СТІН) ---
        # Видалення поодиноких перегородок товщиною в 1 тайл для покращення навігації мобів та гравця.
        for _ in range(2): 
            for y in range(1, self.height - 1):
                for x in range(1, self.width - 1):
                    if self.map[y][x] == '1': # Перевірка клітинки стіни
                        # Видалення стіни, якщо вона знаходиться між двома горизонтальними ділянками підлоги
                        if self.map[y-1][x] == '0' and self.map[y+1][x] == '0':
                            self.map[y][x] = '0'
                        # Видалення стіни, якщо вона знаходиться між двома вертикальними ділянками підлоги
                        elif self.map[y][x-1] == '0' and self.map[y][x+1] == '0':
                            self.map[y][x] = '0'
                        
        for room in self._rect_rooms:
            rx, ry, rw, rh = room
            
            # Защита от слишком маленьких комнат
            if rw < 5 or rh < 5: 
                continue 
            
            # От 5 до 8 бочек на каждую комнату
            num_barrels = random.randint(0, 6)
            attempts = 0
            placed = 0
            
            # Запас итераций, чтобы генератор не завис, если не найдет место
            while placed < num_barrels and attempts < 50:
                attempts += 1
                
                bx = random.randint(rx, rx + rw - 1)
                by = random.randint(ry, ry + rh - 1)
                
                # ОТСЕКАЕМ ЦЕНТР: бочка ставится только в пределах 2 тайлов от любой стены
                # Если координаты попадают в "середину" комнаты - пропускаем
                if rx + 2 <= bx <= rx + rw - 3 and ry + 2 <= by <= ry + rh - 3:
                    continue
                    
                # ЗАЩИТА ПРОХОДОВ: проверяем зону 3х3 вокруг будущей бочки
                is_near_door = False
                for check_y in range(by - 1, by + 2):
                    for check_x in range(bx - 1, bx + 2):
                        if 0 <= check_x < self.width and 0 <= check_y < self.height:
                            # Если рядом есть пол, который ВНЕ этой комнаты - это выход/коридор
                            if self.map[check_y][check_x] in ['0', 'X']:
                                if not (rx <= check_x < rx + rw and ry <= check_y < ry + rh):
                                    is_near_door = True
                
                if is_near_door:
                    continue # Слишком близко к двери, ищем другую точку
                    
                # Если все проверки пройдены и клетка пустая - ставим бочку
                if self.map[by][bx] == '0':
                    self.map[by][bx] = 'X'
                    placed += 1

        # Отримання стартових координат для гравця (центр першої кімнати)
        start_x, start_y = self.rooms[0]
        # Повернення фінальної матриці та координат точки спавну
        return self.map, start_x, start_y

    # =======================================================
    # --- СЛУЖБОВІ МЕТОДИ КЛАСУ ---
    # =======================================================

    def _intersect(self, r1, r2):
        """
        Перевірка перетину двох прямокутників (кімнат).
        Використовується буферна зона (+2 тайли) для збереження стіни між кімнатами.
        """
        return (r1[0] <= r2[0] + r2[2] + 2 and r1[0] + r1[2] + 2 >= r2[0] and
                r1[1] <= r2[1] + r2[3] + 2 and r1[1] + r1[3] + 2 >= r2[1])

    def _create_room(self, room):
        """
        Модифікація матриці: заміна стін ('1') на підлогу ('0') у межах заданої кімнати.
        """
        x, y, w, h = room
        for i in range(x, x + w):
            for j in range(y, y + h):
                self.map[j][i] = '0'

    def _create_h_tunnel(self, x1, x2, y):
        """
        Створення горизонтального коридору шириною у 2 тайли для зручності руху.
        """
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 < x < self.width - 1 and 0 < y < self.height - 2:
                self.map[y][x] = '0'     
                self.map[y+1][x] = '0'   

    def _create_v_tunnel(self, y1, y2, x):
        """
        Створення вертикального коридору шириною у 2 тайли для зручності руху.
        """
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 < y < self.height - 1 and 0 < x < self.width - 2:
                self.map[y][x] = '0'     
                self.map[y][x+1] = '0'