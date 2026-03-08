# 🐍 BattleSnek

> An elite-tier competitive Battlesnake AI built in Python, featuring multiple adaptive strategies and advanced graph-theory algorithms.

---

## 🧠 Strategies

Six distinct snake personalities are hosted on a single FastAPI server, each accessible via its own endpoint:

| Snake | Endpoint | Personality |
|---|---|---|
| 🍎 **Food** | `/food` | Hyper-focused on eating. Pursues the nearest food on every turn using A\*. |
| ⚔️ **Aggressive** | `/aggressive` | Hunts opponent heads. Targets cells adjacent to enemy heads to force collisions. |
| 🛡️ **Avoidant** | `/avoidant` | Maximizes distance from all opponents. Prefers large open board sections. |
| 🔄 **Dynamic** | `/dynamic` | Size-adaptive. Focuses on food until it's 2+ segments larger than the biggest opponent, then hunts. Includes chase fatigue to break off failed pursuits. |
| 🥇 **Dynamic2** | `/dynamic2` | Everything in Dynamic, plus **Edge Trapping** — if a smaller opponent is running along a wall, it cuts them off for the kill. |
| 👑 **Dynamic3** | `/dynamic3` | **Elite Tier.** The pinnacle of this codebase. See below. |

---

## 👑 Dynamic3 — Elite Architecture

Dynamic3 stacks **five independent decision layers**, evaluated in priority order each turn:

### 1. 🌉 Choke Point Detection (Tarjan's Algorithm)
Runs a full **Tarjan's Bridge-Finding** pass on the graph of safe board cells every turn. If crossing an edge into a cell leads into a dead-end pocket smaller than the snake's own length, that move receives a massive penalty. This prevents the snake from ever trapping itself in a "roomy-looking but fatal" enclosed space.

### 2. 🌡️ Gradient Food Desirability
Instead of a hard health threshold (e.g. "panic if health < 30"), Dynamic3 computes a continuous **food heat score** on every turn: `heat = 100 - health`. At full health, food is deprioritized. As health drops, food becomes increasingly urgent. A size-deficit bonus (+50) is added if the snake is smaller than the biggest opponent, encouraging growth.

### 3. 🧱 Edge Trapping
Identifies opponents running along board walls. If Dynamic3 is the larger snake and is positioned parallel just one square inward, it executes a perpendicular cut to force the opponent into a head-on collision they cannot avoid.

### 4. 🗺️ Voronoi Territory Control
Computes a **multi-source BFS** for every snake on the board simultaneously. Tiles are assigned to whichever snake can reach them fastest (with size as a tiebreaker). Dynamic3 biases towards moves that maximize its share of uncontested board territory — naturally boxing opponents out of open space.

### 5. 🔭 Minimax with Alpha-Beta Pruning (1v1 Endgame)
In **1v1 endgame scenarios**, the full heuristic is wrapped inside a recursive **Minimax Decision Tree** (depth=2) with **Alpha-Beta Pruning**. The bot literally simulates the next 2 turns of the game, assumes the opponent plays optimally against it, and picks the move that guarantees the best worst-case outcome. This kills drawn-out stalemates and forces wins in tight corridors.

---

## ⚙️ Shared Core Algorithms

All strategies share a common base logic engine in `logic.py`:

- **A\* Pathfinding** — Optimal path to any target on the board
- **Flood Fill** — Measures the volume of reachable safe space from any position
- **Voronoi BFS** — Multi-source shortest-path for territory control
- **Tarjan's Bridge Finding** — Graph theory algorithm for choke point detection
- **Tail-Chasing Fallback** — When no survivable moves exist, the snake circles its own tail (which moves forward each turn), surviving indefinitely until the board opens up
- **Head-to-Head Collision Avoidance** — Adjacent cells of equal/larger snakes are pre-emptively marked as hazards

---

## 🛠️ Tech Stack

| Category | Technology |
|---|---|
| Language | Python 3 |
| Web Framework | FastAPI |
| ASGI Server | Uvicorn |
| Algorithms | A\*, Flood Fill, Voronoi BFS, Tarjan's Bridges, Minimax + Alpha-Beta |
| Tunnel | ngrok |
| API | Battlesnake Game API |
| Local Testing | Battlesnake CLI |

---

## 🚀 Running Locally

```bash
# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the server
uvicorn main:app --port 8000

# Run a local 5-snake simulation
./run_local_game.sh
```

Snakes will be available at:
- `http://localhost:8000/food`
- `http://localhost:8000/aggressive`
- `http://localhost:8000/avoidant`
- `http://localhost:8000/dynamic`
- `http://localhost:8000/dynamic2`
- `http://localhost:8000/dynamic3`
