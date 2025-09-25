from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

app = FastAPI(title="Level Counter API")

API_KEY = "dlok"
rooms: Dict[str, Dict[str, Dict[str, Any]]] = {}  # room -> name -> player_data

class Player(BaseModel):
    id: str  # будет равен name
    name: str
    level: int
    items: int
    races: List[str]
    classes: List[str]
    strength: int  # вычисляемое

class StatsResponse(BaseModel):
    room: str
    players: List[Player]

class JoinRequest(BaseModel):
    room: str
    name: str  # используем name как id

class UpdateRequest(BaseModel):
    room: str
    name: str

class AddRemoveRequest(BaseModel):
    room: str
    name: str
    value: str  # для race или class

class ApiResult(BaseModel):
    ok: bool
    message: Optional[str] = None
    player: Optional[Player] = None

def check_key(x_api_key: Optional[str]):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

def get_player(room: str, name: str) -> Optional[Dict[str, Any]]:
    if room in rooms and name in rooms[room]:
        return rooms[room][name]
    return None

def compute_strength(player: Dict[str, Any]) -> int:
    return player["level"] + player["items"]

@app.get("/stats", response_model=StatsResponse)
def http_stats(room: str, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    if room not in rooms:
        return StatsResponse(room=room, players=[])
    players = []
    for p in rooms[room].values():
        strength = compute_strength(p)
        players.append(Player(id=p["id"], name=p["name"], level=p["level"], items=p["items"],
                              races=p["races"], classes=p["classes"], strength=strength))
    return StatsResponse(room=room, players=players)

@app.post("/join", response_model=ApiResult)
def http_join(body: JoinRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name.strip()
    if not name:
        return ApiResult(ok=False, message="name_required")
    if r not in rooms:
        rooms[r] = {}
    if name not in rooms[r]:
        player = {"id": name, "name": name, "level": 1, "items": 0, "races": [], "classes": []}
        rooms[r][name] = player
        strength = compute_strength(player)
        return ApiResult(ok=True, message="joined", player=Player(**player, strength=strength))
    else:
        player = rooms[r][name]
        strength = compute_strength(player)
        return ApiResult(ok=True, message="already_in_room", player=Player(**player, strength=strength))

@app.post("/up_level", response_model=ApiResult)
def http_up_level(body: UpdateRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    player["level"] += 1
    strength = compute_strength(player)
    return ApiResult(ok=True, message="leveled_up", player=Player(**player, strength=strength))

@app.post("/down_level", response_model=ApiResult)
def http_down_level(body: UpdateRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    if player["level"] > 1:  # не ниже 1
        player["level"] -= 1
    strength = compute_strength(player)
    return ApiResult(ok=True, message="level_down", player=Player(**player, strength=strength))

@app.post("/up_items", response_model=ApiResult)
def http_up_items(body: UpdateRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    player["items"] += 1
    strength = compute_strength(player)
    return ApiResult(ok=True, message="items_up", player=Player(**player, strength=strength))

@app.post("/down_items", response_model=ApiResult)
def http_down_items(body: UpdateRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    if player["items"] > 0:
        player["items"] -= 1
    strength = compute_strength(player)
    return ApiResult(ok=True, message="items_down", player=Player(**player, strength=strength))

@app.post("/add_race", response_model=ApiResult)
def http_add_race(body: AddRemoveRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    value = body.value.strip()
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    if value and value not in player["races"] and len(player["races"]) < 2:
        player["races"].append(value)
    strength = compute_strength(player)
    return ApiResult(ok=True, message="race_added", player=Player(**player, strength=strength))

@app.post("/remove_race", response_model=ApiResult)
def http_remove_race(body: AddRemoveRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    value = body.value.strip()
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    if value in player["races"]:
        player["races"].remove(value)
    strength = compute_strength(player)
    return ApiResult(ok=True, message="race_removed", player=Player(**player, strength=strength))

@app.post("/add_class", response_model=ApiResult)
def http_add_class(body: AddRemoveRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    value = body.value.strip()
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    if value and value not in player["classes"] and len(player["classes"]) < 2:
        player["classes"].append(value)
    strength = compute_strength(player)
    return ApiResult(ok=True, message="class_added", player=Player(**player, strength=strength))

@app.post("/remove_class", response_model=ApiResult)
def http_remove_class(body: AddRemoveRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    name = body.name
    value = body.value.strip()
    player = get_player(r, name)
    if not player:
        return ApiResult(ok=False, message="not_in_room")
    if value in player["classes"]:
        player["classes"].remove(value)
    strength = compute_strength(player)
    return ApiResult(ok=True, message="class_removed", player=Player(**player, strength=strength))
