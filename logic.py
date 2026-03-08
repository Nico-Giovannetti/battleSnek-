import random
import heapq
from typing import List, Dict, Tuple

def get_neighbors(node: Tuple[int, int], board_width: int, board_height: int) -> List[Tuple[int, int]]:
    x, y = node
    neighbors = []
    if x > 0: neighbors.append((x - 1, y))
    if x < board_width - 1: neighbors.append((x + 1, y))
    if y > 0: neighbors.append((x, y - 1))
    if y < board_height - 1: neighbors.append((x, y + 1))
    return neighbors

def get_safe_cells(data: dict) -> set:
    safe = set()
    width = data["board"]["width"]
    height = data["board"]["height"]
    for x in range(width):
        for y in range(height):
            safe.add((x, y))
    
    # Remove hazards/snakes
    for snake in data["board"]["snakes"]:
        # We don't consider the tail as an obstacle if it will move, unless they just ate.
        # To be safe and simple, let's treat the entire body as an obstacle for now except the very last tail segment if we want to be aggressive.
        # For a beginner snake, treating all body parts as solid is safer.
        for index, body_part in enumerate(snake["body"]):
            if index == len(snake["body"]) - 1: continue # Ignore absolute tip of tail
            pos = (body_part["x"], body_part["y"])
            if pos in safe:
                safe.remove(pos)
                
        # Head-to-head collision avoidance
        # If the snake is an opponent and is >= our size, its next possible moves are deadly.
        if snake["id"] != data["you"]["id"] and snake["length"] >= data["you"]["length"]:
            head = (snake["head"]["x"], snake["head"]["y"])
            for risky_next_move in get_neighbors(head, width, height):
                if risky_next_move in safe:
                    safe.remove(risky_next_move)

    # Could also remove hazard zones if playing in a hazard mode
    if "hazards" in data["board"]:
        for hazard in data["board"]["hazards"]:
            pos = (hazard["x"], hazard["y"])
            if pos in safe:
                safe.remove(pos)
                
    return safe

def flood_fill(start: Tuple[int, int], safe_cells: set, board_width: int, board_height: int) -> int:
    # return the number of accessible cells
    visited = set()
    queue = [start]
    count = 0
    
    while queue:
        curr = queue.pop(0)
        if curr in visited: continue
        visited.add(curr)
        count += 1
        
        for n in get_neighbors(curr, board_width, board_height):
            if n in safe_cells and n not in visited:
                queue.append(n)
                
    return count

def get_voronoi_control(my_next_head: Tuple[int, int], data: dict, safe_cells: set, board_width: int, board_height: int) -> int:
    my_id = data["you"]["id"]
    my_length = data["you"]["length"]
    
    distances = {s["id"]: {} for s in data["board"]["snakes"]}
    
    for snake in data["board"]["snakes"]:
        s_id = snake["id"]
        start = my_next_head if s_id == my_id else (snake["head"]["x"], snake["head"]["y"])
        
        queue = [(start, 0)]
        dists = {start: 0}
        
        while queue:
            curr, d = queue.pop(0)
            for n in get_neighbors(curr, board_width, board_height):
                if n in safe_cells and n not in dists:
                    dists[n] = d + 1
                    queue.append((n, d + 1))
                    
        distances[s_id] = dists
        
    my_territory = 0
    for cell in safe_cells:
        if cell not in distances[my_id]:
            continue
            
        my_d = distances[my_id][cell]
        is_mine = True
        
        for snake in data["board"]["snakes"]:
            s_id = snake["id"]
            if s_id == my_id: continue
                
            if cell in distances[s_id]:
                their_d = distances[s_id][cell]
                if their_d < my_d:
                    is_mine = False
                    break
                elif their_d == my_d:
                    if snake["length"] >= my_length:
                        is_mine = False
                        break
                        
        if is_mine:
            my_territory += 1
            
    return my_territory

def find_bridges(safe_cells: set, board_width: int, board_height: int) -> set:
    """Tarjan's Bridge-Finding Algorithm to find articulation edges (choke points)."""
    visited = set()
    tin = {}
    low = {}
    timer = 0
    bridges = set()
    
    def dfs(node, p=-1):
        nonlocal timer
        visited.add(node)
        tin[node] = low[node] = timer
        timer += 1
        
        for neighbor in get_neighbors(node, board_width, board_height):
            if neighbor not in safe_cells: continue
                
            if neighbor == p: continue
                
            if neighbor in visited:
                low[node] = min(low[node], tin[neighbor])
            else:
                dfs(neighbor, node)
                low[node] = min(low[node], low[neighbor])
                if low[neighbor] > tin[node]:
                    # This edge is a bridge!
                    bridges.add((node, neighbor))
                    bridges.add((neighbor, node))
                    
    # The graph of safe cells might be disconnected, so run DFS for all unvisited
    for cell in safe_cells:
        if cell not in visited:
            dfs(cell)
            
    return bridges

def a_star(start: Tuple[int, int], target: Tuple[int, int], safe_cells: set, board_width: int, board_height: int) -> List[Tuple[int, int]]:
    # standard A* implementation
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
        
    frontier = []
    heapq.heappush(frontier, (0, start))
    came_from = {start: None}
    cost_so_far = {start: 0}
    
    while frontier:
        _, current = heapq.heappop(frontier)
        
        if current == target:
            break
            
        for next_node in get_neighbors(current, board_width, board_height):
            if next_node not in safe_cells and next_node != target:
                continue
                
            new_cost = cost_so_far[current] + 1
            if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                cost_so_far[next_node] = new_cost
                priority = new_cost + heuristic(target, next_node)
                heapq.heappush(frontier, (priority, next_node))
                came_from[next_node] = current
                
    if target not in came_from:
        return []
        
    path = []
    current = target
    while current is not None and current != start:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path

def direction_to(start: Tuple[int, int], target: Tuple[int, int]) -> str:
    sx, sy = start
    tx, ty = target
    if tx > sx: return "right"
    if tx < sx: return "left"
    if ty > sy: return "up"
    if ty < sy: return "down"
    return "up" # fail safe

def choose_move(data: dict) -> str:
    my_head = (data["you"]["head"]["x"], data["you"]["head"]["y"])
    board_width = data["board"]["width"]
    board_height = data["board"]["height"]
    
    safe_cells = get_safe_cells(data)
    
    possible_moves = []
    for n in get_neighbors(my_head, board_width, board_height):
        if n in safe_cells:
            possible_moves.append(n)
            
    if not possible_moves:
        # We are trapped. Just move anywhere to die gracefully.
        print("Trapped! Moving up")
        return "up"
        
    # Evaluate flood fill for each possible move
    move_scores = {}
    for move in possible_moves:
        # Treat the move we are evaluating as starting point for flood fill
        safe_cells_without_my_head = safe_cells.copy()
        if my_head in safe_cells_without_my_head:
            safe_cells_without_my_head.remove(my_head)
            
        score = flood_fill(move, safe_cells_without_my_head, board_width, board_height)
        move_scores[move] = score
        
    # Filter moves that lead to at least the length of our snake in free space
    # (or as much space as is possible)
    required_space = len(data["you"]["body"])
    survivable_moves = [m for m in possible_moves if move_scores[m] >= required_space]
    
    if not survivable_moves:
        # If no move is "fully safe", check if we can chase our own tail to survive indefinitely
        body = data["you"]["body"]
        if len(body) > 2 and body[-1] != body[-2]: # Tail is not stacked (it will move)
            tail_pos = (body[-1]["x"], body[-1]["y"])
            if tail_pos in possible_moves:
                print("No survivable space. Falling back to tail-chasing.")
                return direction_to(my_head, tail_pos)

        # If we can't chase our tail, pick the move that gives us the most space to delay death
        best_move = max(possible_moves, key=lambda m: move_scores[m])
        return direction_to(my_head, best_move)
        
    # We have survivable moves. Let's try to find food using A*
    foods = [(f["x"], f["y"]) for f in data["board"]["food"]]
    if foods:
        best_path = None
        for food in foods:
            path = a_star(my_head, food, safe_cells, board_width, board_height)
            if path and path[0] in survivable_moves:
                if best_path is None or len(path) < len(best_path):
                    best_path = path
                    
        if best_path:
            next_step = best_path[0]
            print(f"Pathing to food: {next_step}")
            return direction_to(my_head, next_step)
            
    # If no food path or no food, pick the survivable move with max flood fill space
    best_move = max(survivable_moves, key=lambda m: move_scores[m])
    print(f"Exploring space: {best_move}")
    return direction_to(my_head, best_move)
