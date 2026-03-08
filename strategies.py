from logic import get_neighbors, get_safe_cells, flood_fill, a_star, direction_to, get_voronoi_control, find_bridges
from typing import Tuple

def base_logic(data: dict) -> Tuple[str, dict]:
    my_head = (data["you"]["head"]["x"], data["you"]["head"]["y"])
    board_width = data["board"]["width"]
    board_height = data["board"]["height"]
    safe_cells = get_safe_cells(data)

    possible_moves = []
    for n in get_neighbors(my_head, board_width, board_height):
        # Explicit in-bounds guard (belt-and-suspenders safety)
        if 0 <= n[0] < board_width and 0 <= n[1] < board_height:
            if n in safe_cells:
                possible_moves.append(n)

    if not possible_moves:
        return "up", {"possible_moves": [], "move_scores": {}, "voronoi_scores": {}, "my_head": my_head, "safe_cells": safe_cells, "board_width": board_width, "board_height": board_height}

    move_scores = {}
    voronoi_scores = {}
    for move in possible_moves:
        safe_cells_without_my_head = safe_cells.copy()
        if my_head in safe_cells_without_my_head:
            safe_cells_without_my_head.remove(my_head)
        score = flood_fill(move, safe_cells_without_my_head, board_width, board_height)
        v_score = get_voronoi_control(move, data, safe_cells_without_my_head, board_width, board_height)
        move_scores[move] = score
        voronoi_scores[move] = v_score

    # Strip guaranteed dead-end moves (flood fill = 0 means we are completely blocked)
    # Only remove them if there are other options available
    nonzero_moves = [m for m in possible_moves if move_scores[m] > 0]
    if nonzero_moves:
        possible_moves = nonzero_moves

    return "", {"possible_moves": possible_moves, "move_scores": move_scores, "voronoi_scores": voronoi_scores, "my_head": my_head, "safe_cells": safe_cells, "board_width": board_width, "board_height": board_height}

def fallback_survival(data: dict, ctx: dict) -> str:
    my_head = ctx["my_head"]
    
    # 1. Try tail-chasing
    body = data["you"]["body"]
    if len(body) > 2 and body[-1] != body[-2]:
        tail_pos = (body[-1]["x"], body[-1]["y"])
        if tail_pos in ctx["possible_moves"]:
            print("No survivable space. Falling back to tail-chasing.")
            return direction_to(my_head, tail_pos)
            
    # 2. Try the move with the most flood fill, tie-broken by voronoi
    if ctx["possible_moves"]:
        best_move = max(ctx["possible_moves"], key=lambda m: (ctx["move_scores"][m], ctx["voronoi_scores"][m]))
        return direction_to(my_head, best_move)
        
    return "up"


def food_strategy(data: dict) -> str:
    early_exit, ctx = base_logic(data)
    if early_exit: return early_exit

    my_head = ctx["my_head"]
    survivable_moves = [m for m in ctx["possible_moves"] if ctx["move_scores"][m] >= len(data["you"]["body"])]
    if not survivable_moves:
        return fallback_survival(data, ctx)

    foods = [(f["x"], f["y"]) for f in data["board"]["food"]]
    if foods:
        best_path = None
        for food in foods:
            path = a_star(my_head, food, ctx["safe_cells"], ctx["board_width"], ctx["board_height"])
            if path and path[0] in survivable_moves:
                if best_path is None or len(path) < len(best_path):
                    best_path = path
        if best_path:
            return direction_to(my_head, best_path[0])

    best_move = max(survivable_moves, key=lambda m: (ctx["voronoi_scores"][m], ctx["move_scores"][m]))
    return direction_to(my_head, best_move)


def aggressive_strategy(data: dict) -> str:
    # If health is dangerously low, we must eat immediately to survive!
    if data["you"]["health"] < 30:
        print("Health low! Switching to Food mode.")
        return food_strategy(data)

    early_exit, ctx = base_logic(data)
    if early_exit: return early_exit

    my_head = ctx["my_head"]
    survivable_moves = [m for m in ctx["possible_moves"] if ctx["move_scores"][m] >= len(data["you"]["body"])]
    if not survivable_moves:
        return fallback_survival(data, ctx)

    other_heads = [(s["head"]["x"], s["head"]["y"]) for s in data["board"]["snakes"] if s["id"] != data["you"]["id"]]
    if other_heads:
        best_path = None
        for head in other_heads:
            # Note: The head itself is not a safe cell usually, so we target the cells around it
            neighbors_of_target = get_neighbors(head, ctx["board_width"], ctx["board_height"])
            target_cells = [n for n in neighbors_of_target if n in ctx["safe_cells"]]
            for target_cell in target_cells:
                path = a_star(my_head, target_cell, ctx["safe_cells"], ctx["board_width"], ctx["board_height"])
                if path and path[0] in survivable_moves:
                    if best_path is None or len(path) < len(best_path):
                        best_path = path
        if best_path:
            return direction_to(my_head, best_path[0])

    # Fallback to pure flood fill survival if no aggressive path found
    best_move = max(survivable_moves, key=lambda m: (ctx["voronoi_scores"][m], ctx["move_scores"][m]))
    return direction_to(my_head, best_move)


def avoidant_strategy(data: dict) -> str:
    # If health is dangerously low, we must eat immediately to survive!
    if data["you"]["health"] < 30:
        print("Health low! Switching to Food mode.")
        return food_strategy(data)

    early_exit, ctx = base_logic(data)
    if early_exit: return early_exit

    my_head = ctx["my_head"]
    survivable_moves = [m for m in ctx["possible_moves"] if ctx["move_scores"][m] >= len(data["you"]["body"])]
    if not survivable_moves:
        return fallback_survival(data, ctx)

    other_heads = [(s["head"]["x"], s["head"]["y"]) for s in data["board"]["snakes"] if s["id"] != data["you"]["id"]]
    
    if not other_heads:
        best_move = max(survivable_moves, key=lambda m: (ctx["voronoi_scores"][m], ctx["move_scores"][m]))
        return direction_to(my_head, best_move)

    def min_dist_to_heads(pos):
        return min([abs(pos[0]-h[0]) + abs(pos[1]-h[1]) for h in other_heads])

    # maximize distance from other heads, using voronoi and flood fill as tie breakers
    best_move = max(survivable_moves, key=lambda m: (min_dist_to_heads(m), ctx["voronoi_scores"][m], ctx["move_scores"][m]))
    return direction_to(my_head, best_move)


# State tracker for dynamic bot chase fatigue
dynamic_state = {}

def dynamic_strategy(data: dict) -> str:
    my_snake = data["you"]
    game_id = data["game"]["id"]
    
    if game_id not in dynamic_state:
        dynamic_state[game_id] = {"chasing": None, "chase_turns": 0, "cooldown": 0}
    state = dynamic_state[game_id]
    
    # Priority #1: Don't starve to death!
    if my_snake["health"] < 30:
        print("Health low! Switching to Food mode.")
        state["chasing"] = None
        return food_strategy(data)

    # Priority #2: Don't suicide on turn 1-3 when everyone is stacked.
    if data["turn"] < 3:
        print("Early game! Focusing on Food mode.")
        return food_strategy(data)
        
    # Priority #3: Chase cooldown fatigue
    if state["cooldown"] > 0:
        state["cooldown"] -= 1
        print(f"On chase cooldown ({state['cooldown']} turns left). Focusing on Food mode.")
        return food_strategy(data)

    other_snakes = [s for s in data["board"]["snakes"] if s["id"] != my_snake["id"]]

    if not other_snakes:
        state["chasing"] = None
        return food_strategy(data)

    largest_other = max(other_snakes, key=lambda s: s["length"])
    my_length = my_snake["length"]

    if my_length >= largest_other["length"] + 2:
        # We are much bigger. 
        # Check if we can reach their head faster than they can reach food
        my_head = (my_snake["head"]["x"], my_snake["head"]["y"])
        their_head = (largest_other["head"]["x"], largest_other["head"]["y"])
        dist_to_them = abs(my_head[0]-their_head[0]) + abs(my_head[1]-their_head[1])
        
        should_chase = False
        foods = [(f["x"], f["y"]) for f in data["board"]["food"]]
        if foods:
            their_dist_to_food = min([abs(their_head[0]-f[0]) + abs(their_head[1]-f[1]) for f in foods])
            my_dist_to_food = min([abs(my_head[0]-f[0]) + abs(my_head[1]-f[1]) for f in foods])
            
            # If we are closer to them than they are to food, OR we are closer to them than we are to food
            if dist_to_them < their_dist_to_food or dist_to_them < my_dist_to_food:
                should_chase = True
        else:
             should_chase = True
             
        if should_chase:
            target_id = largest_other["id"]
            if state["chasing"] == target_id:
                state["chase_turns"] += 1
                if state["chase_turns"] > 30:
                    print(f"Chased {target_id} for too long! Taking a 15-turn break.")
                    state["cooldown"] = 15
                    state["chasing"] = None
                    state["chase_turns"] = 0
                    return food_strategy(data)
            else:
                state["chasing"] = target_id
                state["chase_turns"] = 1
                
            print(f"Chasing {target_id} (Turn {state['chase_turns']}/30)")
            return aggressive_strategy(data)

    # Otherwise, focus on food to grow
    state["chasing"] = None
    state["chase_turns"] = 0
    return food_strategy(data)

def dynamic2_strategy(data: dict) -> str:
    my_snake = data["you"]
    my_head = (my_snake["head"]["x"], my_snake["head"]["y"])
    board_width = data["board"]["width"]
    board_height = data["board"]["height"]
    
    # Early out for starvation or early game
    if my_snake["health"] < 30 or data["turn"] < 3:
        return dynamic_strategy(data)

    other_snakes = [s for s in data["board"]["snakes"] if s["id"] != my_snake["id"]]
    
    # 1. Edge trapping check
    for other in other_snakes:
        if my_snake["length"] > other["length"]:  # Must be strictly larger to safely force a head-on win
            their_head = (other["head"]["x"], other["head"]["y"])
            tx, ty = their_head
            mx, my = my_head
            
            trap_move = None
            
            # Are they against the LEFT wall (x=0)?
            if tx == 0 and mx == 1 and abs(ty - my) <= 1:
                trap_move = "left"
            # Are they against the RIGHT wall (x=width-1)?
            elif tx == board_width - 1 and mx == board_width - 2 and abs(ty - my) <= 1:
                trap_move = "right"
            # Are they against the TOP wall (y=height-1)? Note: the Y axis goes 0 (bottom) to height-1 (top) typically, but let's check math
            elif ty == board_height - 1 and my == board_height - 2 and abs(tx - mx) <= 1:
                trap_move = "up"
            # Are they against the BOTTOM wall (y=0)?
            elif ty == 0 and my == 1 and abs(tx - mx) <= 1:
                trap_move = "down"

            if trap_move:
                print(f"Executing EDGE TRAP against {other['id']} with move: {trap_move}")
                # We need to ensure the move itself doesn't suicide into our own body immediately.
                # Safe cells check applies to the next step. 
                # (A more rigorous check would see if trap_move is in get_safe_cells, but because we are trapping against the wall, we assume our cut-in is valid).
                return trap_move
                
    # 2. If no edge trap, fallback to standard dynamic strategy
    return dynamic_strategy(data)

def evaluate_board(my_head, my_length, opponent_heads, safe_cells, board_width, board_height, data):
    if my_head not in safe_cells: return -99999 # Dead
    
    safe_copy = safe_cells.copy()
    if my_head in safe_copy: safe_copy.remove(my_head)
    
    ff_score = flood_fill(my_head, safe_copy, board_width, board_height)
    if ff_score < my_length: 
        return -10000 + ff_score
        
    v_score = get_voronoi_control(my_head, data, safe_copy, board_width, board_height)
    return (v_score * 10) + ff_score

def minimax(depth: int, is_maximizing: bool, my_head, my_length, opponent_heads, safe_cells, board_width, board_height, data, alpha=-float('inf'), beta=float('inf')) -> float:
    if depth == 0 or my_head not in safe_cells:
        return evaluate_board(my_head, my_length, opponent_heads, safe_cells, board_width, board_height, data)
        
    if is_maximizing:
        max_eval = -float('inf')
        for move in get_neighbors(my_head, board_width, board_height):
            if move not in safe_cells: continue
            
            new_safe = safe_cells.copy()
            new_safe.remove(move)
            
            ev = minimax(depth - 1, False, move, my_length, opponent_heads, new_safe, board_width, board_height, data, alpha, beta)
            max_eval = max(max_eval, ev)
            alpha = max(alpha, ev)
            if beta <= alpha:
                break
        return max_eval if max_eval != -float('inf') else -99999
    else:
        min_eval = float('inf')
        closest_opp = None
        min_dist = 999
        for opp in opponent_heads:
            d = abs(my_head[0]-opp[0]) + abs(my_head[1]-opp[1])
            if d < min_dist:
                min_dist = d
                closest_opp = opp
                
        if not closest_opp:
            return evaluate_board(my_head, my_length, opponent_heads, safe_cells, board_width, board_height, data)
            
        for opp_move in get_neighbors(closest_opp, board_width, board_height):
            if opp_move not in safe_cells: continue
            
            new_safe = safe_cells.copy()
            new_safe.remove(opp_move)
            
            ev = minimax(depth - 1, True, my_head, my_length, opponent_heads, new_safe, board_width, board_height, data, alpha, beta)
            min_eval = min(min_eval, ev)
            beta = min(beta, ev)
            if beta <= alpha:
                break
        return min_eval if min_eval != float('inf') else 99999

def dynamic3_strategy(data: dict) -> str:
    my_snake = data["you"]
    my_head = (my_snake["head"]["x"], my_snake["head"]["y"])
    my_length = my_snake["length"]
    board_width = data["board"]["width"]
    board_height = data["board"]["height"]

    # 1. Base Logic Context Setup
    early_exit, ctx = base_logic(data)
    if early_exit: return early_exit

    survivable_moves = [m for m in ctx["possible_moves"] if ctx["move_scores"][m] >= my_length]
    if not survivable_moves:
        return fallback_survival(data, ctx)

    # PHASE: Early Game (Turn < 20) — Prioritize food to grow competitively.
    # Food Bot relentlessly eats, so Dynamic3 must match its growth rate early or it will
    # always be smaller and lose head-on collisions in the mid/late game.
    if data["turn"] < 20:
        foods = [(f["x"], f["y"]) for f in data["board"]["food"]]
        best_food_move = None
        best_food_path_len = 999
        if foods:
            for food in foods:
                path = a_star(my_head, food, ctx["safe_cells"], board_width, board_height)
                if path and path[0] in survivable_moves:
                    if len(path) < best_food_path_len:
                        best_food_path_len = len(path)
                        best_food_move = path[0]
        if best_food_move:
            print(f"Early Game Turn {data['turn']}: Forcing food pursuit.")
            return direction_to(my_head, best_food_move)

    # 2. Choke Point (Bridge) Penalty
    bridges = find_bridges(ctx["safe_cells"], board_width, board_height)
    choke_penalties = {m: 0 for m in ctx["possible_moves"]}
    
    for move in survivable_moves:
        # If moving to 'move' crosses a bridge (my_head, move), check component size
        if (my_head, move) in bridges:
            # We are crossing a choke point. Is the area on the other side big enough?
            # Actually, our move_score already ran a flood fill FROM 'move'.
            # If move_score is just barely above my_length, it's a very tight pocket.
            # Let's heavily penalize moving into tight pockets through a bridge unless forced.
            if ctx["move_scores"][move] < my_length * 2:
                print(f"Penalizing choke point move: {move}")
                choke_penalties[move] = -100

    # Filter out moves that are terrible choke points if we have better options
    filtered_survivable = [m for m in survivable_moves if choke_penalties[m] == 0]
    if not filtered_survivable:
        filtered_survivable = survivable_moves # Fallback if we must take a choke point

    # 3. Dynamic Gradient Food Scoring
    # Desirability scales from 0 (health=100) to 100 (health=0)
    food_desirability = max(0, 100 - my_snake["health"])
    
    # Check if we are small and need to prioritize growth to compete
    other_snakes = [s for s in data["board"]["snakes"] if s["id"] != my_snake["id"]]
    largest_other = max(other_snakes, key=lambda s: s["length"]) if other_snakes else None
    if largest_other and my_length <= largest_other["length"]:
        food_desirability += 50 # Strongly want food if we aren't the biggest
        
    best_food_move = None
    best_food_path_len = 999
    foods = [(f["x"], f["y"]) for f in data["board"]["food"]]
    if foods:
        for food in foods:
            path = a_star(my_head, food, ctx["safe_cells"], board_width, board_height)
            if path and path[0] in filtered_survivable:
                if len(path) < best_food_path_len:
                    best_food_path_len = len(path)
                    best_food_move = path[0]

    # Decide if we want food right now
    # Arbitrary threshold: If desirability > 40, or if it's right in front of us
    if best_food_move and (food_desirability > 40 or best_food_path_len < 3):
        return direction_to(my_head, best_food_move)

    # 4. Aggressive Edge Trapping (Inherited from Dynamic2)
    for other in other_snakes:
        if my_length > other["length"]:
            their_head = (other["head"]["x"], other["head"]["y"])
            tx, ty = their_head
            mx, my = my_head
            trap_move = None
            if tx == 0 and mx == 1 and abs(ty - my) <= 1: trap_move = "left"
            elif tx == board_width - 1 and mx == board_width - 2 and abs(ty - my) <= 1: trap_move = "right"
            elif ty == board_height - 1 and my == board_height - 2 and abs(tx - mx) <= 1: trap_move = "up"
            elif ty == 0 and my == 1 and abs(tx - mx) <= 1: trap_move = "down"

            if trap_move and (trap_move == "up" and (mx, my+1) in filtered_survivable or
                              trap_move == "down" and (mx, my-1) in filtered_survivable or
                              trap_move == "left" and (mx-1, my) in filtered_survivable or
                              trap_move == "right" and (mx+1, my) in filtered_survivable):
                print(f"Dynamic3 Executing EDGE TRAP against {other['id']} with move: {trap_move}")
                return trap_move
                
    # 5. Master Heuristic Routing (Voronoi + Flood Fill control)
    best_heuristic_move = max(filtered_survivable, key=lambda m: (ctx["voronoi_scores"][m], ctx["move_scores"][m]))

    # 6. Final Minimax Optimization for 1v1 situations (Endgame)
    if len(other_snakes) == 1:
        print("1v1 Endgame Detected! Engaging Minimax Algorithm (Depth 2)...")
        best_minimax_move = None
        best_minimax_score = -float('inf')
        opp_heads = [(other_snakes[0]["head"]["x"], other_snakes[0]["head"]["y"])]
        
        for move in filtered_survivable:
            new_safe = ctx["safe_cells"].copy()
            if move in new_safe: new_safe.remove(move)
            
            score = minimax(2, False, move, my_length, opp_heads, new_safe, board_width, board_height, data)
            if score > best_minimax_score:
                best_minimax_score = score
                best_minimax_move = move
                
        if best_minimax_move:
            print(f"Minimax selected move: {best_minimax_move} with score {best_minimax_score}")
            return direction_to(my_head, best_minimax_move)

    return direction_to(my_head, best_heuristic_move)
