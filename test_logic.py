from logic import choose_move

mock_data = {
    "game": {"id": "test-game"},
    "turn": 4,
    "board": {
        "height": 11,
        "width": 11,
        "snakes": [
            {
                "id": "snake-1",
                "name": "My Snake",
                "health": 90,
                "body": [{"x": 5, "y": 5}, {"x": 5, "y": 6}, {"x": 5, "y": 7}],
                "head": {"x": 5, "y": 5},
                "length": 3
            }
        ],
        "food": [{"x": 1, "y": 1}, {"x": 9, "y": 9}],
        "hazards": []
    },
    "you": {
        "id": "snake-1",
        "name": "My Snake",
        "health": 90,
        "body": [{"x": 5, "y": 5}, {"x": 5, "y": 6}, {"x": 5, "y": 7}],
        "head": {"x": 5, "y": 5},
        "length": 3
    }
}

print(f"Testing snake logic... Move chosen: {choose_move(mock_data)}")
