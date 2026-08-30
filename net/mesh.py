"""Genesis Zero — net/mesh: sinh và cache mesh 3D từ vector trait (N-13).

Năm bất biến (N-13 §4):
1. Hình = trait, chỉ trait: Prompt sinh 100% từ vector trait qua body_line.
   Không có display_name, persona, client_id hay species_id.
2. Cache theo vector trait: Khoá cache là md5 của 6 trait cố định.
3. Mesh KHÔNG BAO GIỜ chạm vào sim: Không import vào world/logio/tick.
4. /join và tick không bao giờ bị chặn: ensure_mesh trả ngay (<50ms).
5. Quota: mỗi client tối đa N lượt sinh mới/ngày, toàn cục tối đa M lượt/ngày.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
import time
from typing import TYPE_CHECKING, Any

import httpx

from genesis.mesh_prompts import creature_prompt
import net_config

if TYPE_CHECKING:
    from genesis.traits import Traits

logger = logging.getLogger(__name__)


def mesh_key(traits: Traits, domain: str = "CAN", features=()) -> str:
    """md5 của SÁU trait + TẦNG + ba đặc điểm.

    TUYỆT ĐỐI không đưa `client_id`, `display_name` hay bất cứ thứ gì **do client
    viết** vào khoá — đó vẫn là bất biến gốc của N-13, và nó không đổi. Tầng và
    đặc điểm thì khác hẳn: chúng do **server bốc thăm** tất định theo
    `(loài, seed)`, không ai gõ ra được.

    Vì sao phải thêm: sau W-18/W-19, ngoại hình **không còn là hàm của riêng
    vector trait**. Khoá chỉ-theo-trait làm hai con cùng vector nhưng khác đặc
    điểm — thậm chí khác TẦNG — dùng chung một mesh, nên hình 3D của một con cá
    có thể là thân bốn chân, và một con lưỡng cư mất chân màng.

    Đó là W-19 hỏng theo chiều ngược lại: phiếu ấy dựng lên để hình dáng KHÔNG
    nói dối về cơ chế, và một khoá đệm quá thô làm nó nói dối mà không ai thấy.

    Cái giá: đệm bớt hiệu quả. `mesh_cost_probe` đếm theo trần "20 vector, không
    phải 180.000" của N-13, mà giờ mỗi vector nhân thêm tầng và tổ hợp đặc điểm.
    Nhưng đệm sai còn tệ hơn đệm ít — nó trả về một cái hình của con khác.
    """
    keys = ":".join(sorted(getattr(f, "key", str(f)) for f in features))
    raw = (f"{traits.brain}:{traits.attack}:{traits.armor}:{traits.speed}:"
           f"{traits.sense}:{traits.stomach}|{domain}|{keys}")
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def body_prompt(traits: Traits, domain: str = "CAN", features=()) -> str:
    """DÙNG LẠI `genesis.mesh_prompts.creature_prompt` — một đường tới Meshy.

    `creature_prompt` vẫn nhúng nguyên
    `prompt.body_line` cho phần số, nên bất biến 1 ("hình = trait, chỉ trait")
    giữ nguyên: đổi thang trait thì câu chữ và hình đổi cùng lúc, không lệch.

    Bản cũ gửi thẳng `body_line` — đúng về bất biến nhưng là một dòng chỉ số
    khô ("đầu óc 4 · tay 3 · …"), và Meshy không có gì để dựng từ đó.
    """
    return creature_prompt(traits, domain, features)


class MeshCache:
    """Quản lý chỉ mục mesh trên đĩa và quota sinh mesh theo ngày."""

    def __init__(
        self,
        cache_dir: Path | str,
        per_client_per_day: int,
        global_per_day: int,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.per_client_per_day = per_client_per_day
        self.global_per_day = global_per_day
        self._index_file = self.cache_dir / "index.json"
        self._quota_file = self.cache_dir / "quota.json"
        self._entries: dict[str, str] = {}
        self._client_requests: dict[str, list[float]] = {}
        self._global_requests: list[float] = []
        # Trạng thái sinh nền gắn với CACHE, không phải với module. Biến toàn cục
        # cấp module thì hai server trong một tiến trình dùng chung, và test này
        # rò trạng thái sang test kia.
        self.in_flight: set[str] = set()
        # Giữ tham chiếu mạnh tới task nền: `asyncio.create_task` mà không giữ
        # tham chiếu thì bộ dọn rác được phép thu hồi task giữa chừng. Đây là
        # cái bẫy có ghi trong tài liệu asyncio, và nó hỏng theo kiểu ngẫu nhiên.
        self._tasks: set[Any] = set()
        self._load()

    def _load(self) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            if self._index_file.exists():
                with open(self._index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._entries = {str(k): str(v) for k, v in data.items()}
        except Exception as exc:
            logger.warning("Không thể đọc cache mesh từ %s: %s", self._index_file, exc)
        # Quota phải SỐNG QUA khởi động lại. Đếm trong RAM thôi thì trần chi phí
        # toàn cục biến mất mỗi lần deploy — mà trần ấy chính là lý do có quota.
        try:
            if self._quota_file.exists():
                q = json.loads(self._quota_file.read_text(encoding="utf-8"))
                self._client_requests = {k: list(v) for k, v in (q.get("client") or {}).items()}
                self._global_requests = list(q.get("global") or [])
        except Exception as exc:
            logger.warning("Không thể đọc quota mesh từ %s: %s", self._quota_file, exc)

    def _save_quota(self) -> None:
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            tmp = self._quota_file.with_suffix(".tmp")
            tmp.write_text(json.dumps(
                {"client": self._client_requests, "global": self._global_requests}
            ), encoding="utf-8")
            tmp.replace(self._quota_file)
        except Exception as exc:
            logger.warning("Không thể ghi quota mesh vào %s: %s", self._quota_file, exc)

    def get(self, key: str) -> str | None:
        """Trả mesh_url nếu đã có trong cache, không thì None."""
        return self._entries.get(key)

    def put(self, key: str, url: str) -> None:
        """Ghi vào chỉ mục JSON trên đĩa."""
        self._entries[key] = url
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            tmp_file = self._index_file.with_suffix(".tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self._entries, f, indent=2)
            tmp_file.replace(self._index_file)
        except Exception as exc:
            logger.warning("Không thể ghi cache mesh vào %s: %s", self._index_file, exc)

    def allow(self, client_id: str, now: float, *, record: bool = True) -> bool:
        """Kiểm tra quota 24 giờ cho client_id và toàn cục.

        Nếu quota cho phép và record=True, ghi nhận lượt yêu cầu tại thời điểm now.
        """
        cutoff = now - 86400.0
        self._global_requests = [t for t in self._global_requests if t > cutoff]
        client_reqs = [t for t in self._client_requests.get(client_id, []) if t > cutoff]
        self._client_requests[client_id] = client_reqs

        if len(self._global_requests) >= self.global_per_day:
            return False
        if len(client_reqs) >= self.per_client_per_day:
            return False

        if record:
            self._global_requests.append(now)
            client_reqs.append(now)
            self._save_quota()
        return True


async def generate_mesh(
    traits: Traits,
    cache: MeshCache,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str | None:
    """Việc chạy nền thật sự: POST tới net_config.MESHY_URL với body_prompt(traits),
    poll tới khi xong, rồi cache.put. Mọi lỗi -> log warning và trả None,
    KHÔNG ném (một dịch vụ vẽ hình chết không được làm gãy ván).
    """
    key = mesh_key(traits)
    prompt = body_prompt(traits)
    url = str(net_config.MESHY_URL).rstrip("/")
    poll_interval = getattr(net_config, "MESHY_POLL_INTERVAL", 2.0)

    try:
        async with httpx.AsyncClient(timeout=30.0, transport=transport) as client:
            payload = {"prompt": prompt}
            resp = await client.post(url, json=payload)
            if resp.status_code not in (200, 202):
                logger.warning(
                    "Meshy POST thất bại %s: HTTP %d %s",
                    url,
                    resp.status_code,
                    resp.text[:200],
                )
                return None

            data = resp.json()

            model_url = (
                data.get("model_url")
                or data.get("glb_url")
                or (data.get("model_urls") and data["model_urls"].get("glb"))
            )
            if model_url and isinstance(model_url, str):
                cache.put(key, model_url)
                return model_url

            task_id = data.get("result") or data.get("id") or data.get("task_id")
            if not task_id or not isinstance(task_id, str):
                logger.warning("Meshy response không có task_id hoặc model_url: %r", data)
                return None

            poll_url = f"{url}/{task_id}"
            for _ in range(60):
                await asyncio.sleep(poll_interval)
                poll_resp = await client.get(poll_url)
                if poll_resp.status_code != 200:
                    logger.warning(
                        "Meshy poll thất bại %s: HTTP %d %s",
                        poll_url,
                        poll_resp.status_code,
                        poll_resp.text[:200],
                    )
                    return None

                poll_data = poll_resp.json()
                status = str(poll_data.get("status", "")).upper()

                if status in ("SUCCEEDED", "SUCCESS", "DONE"):
                    model_url = (
                        poll_data.get("model_url")
                        or poll_data.get("glb_url")
                        or (poll_data.get("model_urls") and poll_data["model_urls"].get("glb"))
                        or poll_data.get("result")
                    )
                    if model_url and isinstance(model_url, str):
                        cache.put(key, model_url)
                        return model_url
                    logger.warning("Meshy thành công nhưng thiếu model_url: %r", poll_data)
                    return None

                if status in ("FAILED", "EXPIRED", "CANCELED"):
                    logger.warning(
                        "Meshy task thất bại với trạng thái: %s (%r)",
                        status,
                        poll_data,
                    )
                    return None

            logger.warning("Meshy task timeout sau quá nhiều lần poll: %s", task_id)
            return None
    except Exception as exc:
        logger.warning("Lỗi trong quá trình sinh mesh cho key %s: %s", key, exc)
        return None
    finally:
        cache.in_flight.discard(key)


async def ensure_mesh(
    traits: Traits,
    cache: MeshCache,
    client_id: str,
    *,
    transport: httpx.AsyncBaseTransport | None = None,
) -> str | None:
    """Có trong cache -> trả mesh_url NGAY (không gọi mạng).
    Không có -> XẾP HÀNG sinh nền và trả None ngay lập tức. KHÔNG await lượt
    sinh của Meshy bên trong ensure_mesh: nó mất hàng PHÚT (bất biến 4).
    Dùng asyncio.create_task hoặc một hàng đợi; trả về phải dưới 50 ms.
    """
    key = mesh_key(traits)
    cached = cache.get(key)
    if cached is not None:
        return cached

    # THỨ TỰ QUAN TRỌNG: đã có người đang sinh khoá này thì về ngay, và KHÔNG tiêu
    # quota. Bản đầu tiêu quota trước rồi mới xét in-flight, nên gọi ba lần cho
    # CÙNG một vector trait ăn ba suất trong khi chỉ sinh một mesh — đo thật:
    # 3/3 suất cho một cơ thể. Ở luồng thật `/join` gọi mỗi lần vào và trang xem
    # thì poll, nên một người chơi có một cơ thể đốt sạch quota ngày mà không tạo
    # thêm được cái mesh nào. Quota phải đếm LƯỢT SINH, không đếm lượt hỏi.
    if key in cache.in_flight:
        return None
    if not cache.allow(client_id, time.time()):
        return None

    cache.in_flight.add(key)
    task = asyncio.create_task(generate_mesh(traits, cache, transport=transport))
    cache._tasks.add(task)
    task.add_done_callback(cache._tasks.discard)
    return None
