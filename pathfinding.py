import heapq

def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def astar(map_data, start, goal):
    rows = len(map_data)
    cols = len(map_data[0])
    neighbors = [(0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    close_set = set()
    came_from = {}
    gscore = {start: 0}
    fscore = {start: heuristic(start, goal)}
    
    oheap = []
    heapq.heappush(oheap, (fscore[start], start))

    while oheap:
        current = heapq.heappop(oheap)[1]

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]

        close_set.add(current)

        for i, j in neighbors:
            neighbor = current[0] + i, current[1] + j
            
            # Перевірка виходу за межі карти
            if not (0 <= neighbor[1] < rows and 0 <= neighbor[0] < cols):
                continue
                
            # Перетворюємо значення клітинки в рядок. Тепер '1' і 1 працюють однаково.
            cell_val = str(map_data[neighbor[1]][neighbor[0]])
            if cell_val in ['1', 'X', '#']: 
                continue

            step_cost = 1.414 if i != 0 and j != 0 else 1
            tentative_g_score = gscore[current] + step_cost

            # ВИПРАВЛЕНО: Невідвідані клітинки тепер мають вартість нескінченності, а не 0
            if neighbor in close_set and tentative_g_score >= gscore.get(neighbor, float('inf')):
                continue

            if tentative_g_score < gscore.get(neighbor, float('inf')) or neighbor not in [item[1] for item in oheap]:
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g_score
                fscore[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(oheap, (fscore[neighbor], neighbor))

    return []