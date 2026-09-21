"""Genesis Zero — net/routes_arena.py
Cổng kết nối đấu trường nhiều người chơi (Multi-Tenant Arena Gateway)
hỗ trợ các phòng lab nghiên cứu cắm agent và theo dõi xếp hạng Elo.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/arena", tags=["arena"])


class AgentRegistration(BaseModel):
    team_name: str = Field(..., min_length=2, max_length=64)
    model_name: str = Field(..., min_length=2, max_length=64)
    endpoint: str | None = None
    agent_type: str = Field(default="llm", pattern="^(llm|reflex|heuristic)$")


class MatchRecord(BaseModel):
    match_id: str
    seed: int
    competitors: list[str]
    winner: str | None = None
    created_at: float = Field(default_factory=time.time)


class ArenaState:
    def __init__(self) -> None:
        self.registered_agents: dict[str, dict[str, Any]] = {}
        self.elo_ratings: dict[str, float] = {}
        self.matches: list[dict[str, Any]] = []

    def register(self, reg: AgentRegistration) -> dict[str, Any]:
        agent_id = f"team_{len(self.registered_agents) + 1}_{reg.team_name.lower().replace(' ', '_')}"
        data = {
            "agent_id": agent_id,
            "team_name": reg.team_name,
            "model_name": reg.model_name,
            "endpoint": reg.endpoint,
            "agent_type": reg.agent_type,
            "registered_at": time.time(),
        }
        self.registered_agents[agent_id] = data
        if agent_id not in self.elo_ratings:
            self.elo_ratings[agent_id] = 1200.0
        return data

    def record_match_result(self, match_id: str, winner_id: str, loser_id: str) -> None:
        r_w = self.elo_ratings.get(winner_id, 1200.0)
        r_l = self.elo_ratings.get(loser_id, 1200.0)
        k = 32.0
        e_w = 1.0 / (1.0 + 10.0 ** ((r_l - r_w) / 400.0))
        e_l = 1.0 - e_w
        self.elo_ratings[winner_id] = round(r_w + k * (1.0 - e_w), 1)
        self.elo_ratings[loser_id] = round(r_l + k * (0.0 - e_l), 1)
        self.matches.append({
            "match_id": match_id,
            "winner": winner_id,
            "loser": loser_id,
            "timestamp": time.time(),
        })

    def get_leaderboard(self) -> list[dict[str, Any]]:
        sorted_ranks = sorted(self.elo_ratings.items(), key=lambda kv: kv[1], reverse=True)
        board = []
        for rank, (aid, elo) in enumerate(sorted_ranks, start=1):
            agent_info = self.registered_agents.get(aid, {})
            board.append({
                "rank": rank,
                "agent_id": aid,
                "team_name": agent_info.get("team_name", aid),
                "model_name": agent_info.get("model_name", "unknown"),
                "elo": elo,
            })
        return board


arena_state = ArenaState()


@router.post("/register")
async def register_agent(reg: AgentRegistration) -> dict[str, Any]:
    """Đăng ký một AI agent hoặc đội thi đấu vào đấu trường."""
    data = arena_state.register(reg)
    return {"ok": True, "agent": data}


@router.get("/leaderboard")
async def get_leaderboard() -> dict[str, Any]:
    """Xem bảng xếp hạng Elo hiện tại của đấu trường."""
    board = arena_state.get_leaderboard()
    return {"ok": True, "leaderboard": board}


@router.get("/matches")
async def get_recent_matches() -> dict[str, Any]:
    """Danh sách các trận đấu gần nhất trong đấu trường."""
    return {"ok": True, "matches": arena_state.matches[-50:]}
