from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

app = FastAPI(title="Level Counter API")

API_KEY = "dlok"
rooms: Dict[str, Dict[str, Dict[str, Any]]] = {}

class Player(BaseModel):
    id: str
    name: str
    level: int

class StatsResponse(BaseModel):
    room: str
    players: List[Player]

class JoinRequest(BaseModel):
    room: str
    user_id: str
    name: str

class UpRequest(BaseModel):
    room: str
    user_id: str

class ApiResult(BaseModel):
    ok: bool
    level: Optional[int] = None
    message: Optional[str] = None

def check_key(x_api_key: Optional[str]):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")

@app.get("/stats", response_model=StatsResponse)
def http_stats(room: str, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    if room not in rooms:
        return StatsResponse(room=room, players=[])
    players = [Player(**p) for p in rooms[room].values()]
    return StatsResponse(room=room, players=players)

@app.post("/join", response_model=ApiResult)
def http_join(body: JoinRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    uid = str(body.user_id)
    name = body.name or "Игрок"
    if r not in rooms:
        rooms[r] = {}
    if uid not in rooms[r]:
        rooms[r][uid] = {"id": uid, "name": name, "level": 1}
        return ApiResult(ok=True, level=1, message="joined")
    else:
        return ApiResult(ok=True, level=rooms[r][uid]["level"], message="already_in_room")

@app.post("/up", response_model=ApiResult)
def http_up(body: UpRequest, x_api_key: Optional[str] = Header(default=None)):
    check_key(x_api_key)
    r = body.room
    uid = str(body.user_id)
    if r not in rooms or uid not in rooms[r]:
        return ApiResult(ok=False, message="not_in_room")
    rooms[r][uid]["level"] += 1
    return ApiResult(ok=True, level=rooms[r][uid]["level"], message="leveled_up")
