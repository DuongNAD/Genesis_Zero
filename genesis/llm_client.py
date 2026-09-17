"""Genesis Zero — llm_client: một lớp gọi model duy nhất (B-03).

Dùng cho cả Lab lẫn client ở chế độ mở (docs/04-THE-GIOI-MO.md). Bốn bất biến,
theo docs/tasks/B-03-llm-client.md §2:

1. Gọi `/completion`, **không** `/v1/chat/completions` — chỉ endpoint gốc của
   llama-server nhận `id_slot`, và không có `id_slot` thì không có prefix cache.
2. `id_slot` + `cache_prompt` luôn có mặt. Cùng `creature_id` → **cùng slot
   suốt ván**, không bao giờ đổi; slot đổi là cache vỡ.
3. Lỗi → trả `None`, không ném. Người gọi rơi về phản xạ. Nhưng luôn log:
   `except: pass` biến một model chết thành một ván "bình thường" chỉ hơi ngu.
4. `httpx.AsyncClient` + `asyncio.gather`. Đừng `await` tuần tự trong vòng lặp —
   nó biến 4 giây thành 15 giây mà không báo lỗi gì.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import httpx

from genesis import law_config

logger = logging.getLogger(__name__)

DEFAULT_THRESHOLD = 3
DEFAULT_OPEN_TICKS = 50


class CircuitBreaker:
    """Ngắt mạch khi model hỏng liên tiếp, để ván chạy tiếp bằng phản xạ.

    Ba lỗi liên tiếp thì mở, và mở trong 50 tick. Cái đồng hồ là cần thiết:
    khi đã mở thì không ai gọi model nữa, nên sẽ không bao giờ có một lần thành
    công để đóng nó lại. Không có hạn tự mở, ngắt mạch là vĩnh viễn.
    """

    def __init__(
        self,
        failure_threshold: int = DEFAULT_THRESHOLD,
        open_ticks: int = DEFAULT_OPEN_TICKS,
    ) -> None:
        self.failure_threshold = failure_threshold
        self.open_ticks = open_ticks
        self._consecutive = 0
        self._open_until: int | None = None

    def record(self, ok: bool, tick_no: int = 0) -> None:
        if ok:
            self._consecutive = 0
            self._open_until = None
            return
        self._consecutive += 1
        if self._consecutive >= self.failure_threshold:
            self._open_until = tick_no + self.open_ticks
            logger.warning(
                "ngắt mạch: %d lỗi liên tiếp, đóng model tới tick %d",
                self._consecutive,
                self._open_until,
            )

    def is_open_at(self, tick_no: int) -> bool:
        """Còn đang ngắt ở lượt này không. Hết hạn thì tự đóng lại (half-open)."""
        if self._open_until is None:
            return False
        if tick_no >= self._open_until:
            self._open_until = None
            self._consecutive = 0
            return False
        return True

    @property
    def is_open(self) -> bool:
        """Đang ngắt hay không, không xét đồng hồ."""
        return self._open_until is not None


def detect_backend(base_url: str = "http://127.0.0.1:8080") -> str:
    """Xác định backend LLM dựa trên URL hoặc cổng kết nối."""
    raw = base_url.lower()
    if ":11434" in raw or "/api/chat" in raw or "/api/" in raw:
        return "ollama"
    if ":8000" in raw or ":8001" in raw or "/v1" in raw or "/chat/completions" in raw:
        return "vllm"
    if ":8099" in raw:
        return "mock"
    return "llama.cpp"


async def ask(
    base_url: str = "http://127.0.0.1:8080",
    slot_id: int = 0,
    system: str = "",
    user: str = "",
    max_tokens: int = 64,
    schema: dict[str, Any] | None = None,
    timeout: float = law_config.LLM_TIMEOUT_S,
    temperature: float = 0.7,
    transport: httpx.AsyncBaseTransport | None = None,
    client: httpx.AsyncClient | None = None,
    backend: str = "auto",
    model: str = "default",
    thinking_tokens: int | None = None,
    api_key: str | None = None,
    **kwargs: Any,
) -> dict[str, Any] | None:
    """Gọi LLM backend (llama.cpp, Ollama, vLLM, Mock, hoặc fallback Reflex).

    `client` cho phép dùng lại một pool kết nối qua nhiều lời gọi — người gọi
    nào bắn cả đàn bằng `asyncio.gather` thì nên truyền vào.
    """
    if backend == "reflex":
        return None

    if backend == "auto":
        backend = os.environ.get("GENESIS_LLM_BACKEND", "auto")
    if model == "default":
        model = os.environ.get("GENESIS_LLM_MODEL", "default")
    resolved_backend = detect_backend(base_url) if backend == "auto" else backend.lower()
    root = base_url.rstrip("/")

    owns_client = client is None
    if owns_client:
        client = httpx.AsyncClient(timeout=timeout, transport=transport)
    try:
        if resolved_backend == "ollama":
            url = root if root.endswith("/api/chat") else f"{root}/api/chat"
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            if user:
                messages.append({"role": "user", "content": user})
            payload: dict[str, Any] = {
                "model": model if model and model != "default" else "llama3",
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
            if schema is not None:
                payload["format"] = schema

            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.warning(
                    "Ollama gọi hỏng %s: HTTP %d %s",
                    url, resp.status_code, resp.text[:200],
                )
                return None
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            if not isinstance(content, str):
                logger.warning("Ollama phản hồi không hợp lệ: %r", str(data)[:200])
                return None
            return {
                "json": json.loads(content),
                "n": int(data.get("eval_count", 0)),
                "raw": content,
                "timings": {"eval_duration": data.get("eval_duration")},
            }

        elif resolved_backend in ("vllm", "openai", "frontier"):
            url = (root if root.endswith("/chat/completions") else
                   f"{root}/chat/completions" if root.endswith("/v1") else
                   f"{root}/v1/chat/completions")
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            if user:
                messages.append({"role": "user", "content": user})
            payload = {
                "model": model if model and model != "default" else "default",
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "response_format": {"type": "json_object"},
            }
            headers = {}
            if resolved_backend == "frontier":
                from genesis.prompt import completion_budget
                reserve = (int(os.environ.get("GENESIS_THINKING_TOKENS", "2048"))
                           if thinking_tokens is None else thinking_tokens)
                payload["max_completion_tokens"] = completion_budget(max_tokens, reserve)
                del payload["max_tokens"]
                del payload["temperature"]
                key = api_key or os.environ.get("GENESIS_LLM_API_KEY")
                if key:
                    headers["Authorization"] = f"Bearer {key}"
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code != 200:
                logger.warning(
                    "vLLM gọi hỏng %s: HTTP %d %s",
                    url, resp.status_code, resp.text[:200],
                )
                return None
            data = resp.json()
            choices = data.get("choices", [])
            content = choices[0].get("message", {}).get("content", "") if choices else ""
            if not isinstance(content, str):
                logger.warning("vLLM phản hồi không hợp lệ: %r", str(data)[:200])
                return None
            if choices[0].get("finish_reason") in ("length", "content_filter"):
                logger.warning("model response incomplete (slot %d)", slot_id)
                return None
            if resolved_backend == "frontier":
                # Strip only a leading, closed thinking block, never search for
                # JSON inside reasoning (which may itself contain examples).
                content = re.sub(r"^\s*<think>.*?</think>\s*", "", content, flags=re.S)
                if "<think>" in content or "</think>" in content:
                    return None
                content = content.strip()
                if content.startswith("```json\n") and content.endswith("```"):
                    content = content[8:-3].strip()
            answer = json.loads(content)
            if not isinstance(answer, dict):
                return None
            usage = data.get("usage") or {}
            total = int(usage.get("completion_tokens", 0))
            reasoning = int((usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))
            if not 0 <= reasoning <= total:
                return None
            return {
                "json": answer,
                "n": total,  # Charge all generated tokens, including reasoning.
                "thinking_tokens": reasoning,
                "answer_tokens": total - reasoning,
                "raw": content,
                "timings": usage,
            }

        else:
            # llama.cpp / mock / default
            url = root if root.endswith("/completion") else f"{root}/completion"
            payload = {
                "prompt": system + user,
                "id_slot": slot_id,
                "cache_prompt": True,
                "json_schema": schema,
                "n_predict": max_tokens,
                "temperature": temperature,
            }
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                logger.warning(
                    "gọi model hỏng %s (slot %d): HTTP %d %s",
                    url, slot_id, resp.status_code, resp.text[:200],
                )
                return None
            data = resp.json()
            content = data.get("content")
            if not isinstance(content, str):
                logger.warning(
                    "phản hồi model không có trường 'content' dạng chuỗi (slot %d): %r",
                    slot_id, str(data)[:200],
                )
                return None
            return {
                "json": json.loads(content),
                "n": int(data.get("tokens_predicted", 0)),
                "raw": content,
                # `timings` là cách DUY NHẤT đo được prefill tách khỏi decode. Đo
                # bằng đồng hồ ngoài thì với model nhỏ, decode át hết prefill và
                # tỉ lệ "lần 2 / lần 1" nói về tốc độ sinh chứ không nói về cache.
                "timings": data.get("timings") or {},
            }
    except json.JSONDecodeError as exc:
        # Grammar của llama-server lẽ ra chặn được, nhưng cắt vì `n_predict` thì
        # vẫn ra JSON cụt. Người gọi ghi LLM_MISS.
        tail = (content or "")[-60:] if isinstance(locals().get("content"), str) else ""
        logger.warning("model trả JSON hỏng (slot %d, %d token): %s | ...%s",
                       slot_id, int((data or {}).get("tokens_predicted", -1))
                       if isinstance(locals().get("data"), dict) else -1, exc, tail)
        return None
    except (ValueError, TypeError, AttributeError, KeyError, IndexError) as exc:
        logger.warning("invalid model response/config (slot %d): %s", slot_id, type(exc).__name__)
        return None
    except httpx.HTTPError as exc:
        logger.warning("lỗi mạng khi gọi %s (slot %d): %s", base_url, slot_id, exc)
        return None
    finally:
        if owns_client:
            await client.aclose()
