from fastapi import FastAPI, Request
from strategies import food_strategy, aggressive_strategy, avoidant_strategy, dynamic_strategy, dynamic2_strategy, dynamic3_strategy

app = FastAPI()

# Strategy logic map
strategies = {
    "food": food_strategy,
    "aggressive": aggressive_strategy,
    "avoidant": avoidant_strategy,
    "dynamic": dynamic_strategy,
    "dynamic2": dynamic2_strategy,
    "dynamic3": dynamic3_strategy
}

# --- Shared Lifecycle Handlers ---

@app.get("/{strategy}")
def info(strategy: str):
    if strategy not in strategies:
        return {"error": "Strategy not found"}
        
    colors = {
        "food": "#ffcccc",
        "aggressive": "#ff0000",
        "avoidant": "#0000ff",
        "dynamic": "#880088",
        "dynamic2": "#ffd700", # GOLD
        "dynamic3": "#ffffff", # WHITE
    }
    
    return {
        "apiversion": "1",
        "author": "nico",
        "color": colors.get(strategy, "#888888"),
        "head": "default",
        "tail": "default",
    }

@app.post("/{strategy}/start")
async def start(strategy: str, request: Request):
    data = await request.json()
    print(f"[{strategy.upper()}] Game starting: {data['game']['id']}")
    return "ok"

@app.post("/{strategy}/move")
async def move(strategy: str, request: Request):
    if strategy not in strategies:
        return {"move": "up"}
        
    data = await request.json()
    try:
        move_dir = strategies[strategy](data)
    except Exception as e:
        print(f"Error in {strategy}: {e}")
        move_dir = "up"
        
    print(f"[{strategy.upper()}] MOVE: {move_dir}")
    return {"move": move_dir}

@app.post("/{strategy}/end")
async def end(strategy: str, request: Request):
    data = await request.json()
    print(f"[{strategy.upper()}] Game ended: {data['game']['id']}")
    return "ok"
