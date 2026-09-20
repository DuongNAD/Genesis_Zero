"""Genesis Zero — concept_creator.py
Quy trình 2 bước Studio hoàn chỉnh:
1. Nhận mô tả người dùng (tối đa 500 ký tự) + Dạng sống (FAUNA, FLORA, FUNGI, HYBRID) + Thuộc tính (16/20/23 điểm, max 7).
2. Tổng hợp master prompt gửi cho AGY AI để tạo ảnh concept sinh vật / thực vật / nấm trước.
3. Đưa prompt và thông số hình thái học sang Blender để dựng model 3D hữu cơ kèm Armature Rigging và TRỌN BỘ 8 ANIMATIONS.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from genesis.creature_builder import build_creature_blender_code
from genesis.domain import Domain
from genesis.features import FEATURES
from genesis.traits import Traits

ROOT = Path(__file__).resolve().parent.parent
CONCEPTS_DIR = ROOT / "web" / "concepts"
CREATURES_DIR = ROOT / "assets" / "creatures"

logger = logging.getLogger(__name__)


def _find_blender() -> str | None:
    candidates = [os.environ.get("BLENDER_BIN"), shutil.which("blender"),
                  "/Applications/Blender.app/Contents/MacOS/Blender"]
    base = Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Blender Foundation"
    candidates.extend(str(p) for p in sorted(base.glob("Blender*/blender.exe"), reverse=True))
    return next((p for p in candidates if p and os.path.isfile(p) and os.access(p, os.X_OK)), None)


def build_master_concept_prompt(
    name: str,
    latin: str,
    domain: str,
    diet: str,
    strategy: str,
    traits: list[int] | None,
    features: list[str] | None,
    description: str = "",
    kingdom: str = "FAUNA",
) -> str:
    """Tổng hợp master prompt đa dạng sinh học (Động vật, Thực vật, Nấm, Lai)."""
    parts = []
    user_desc = description.strip()[:500]

    # Nhận diện tự động dạng sống từ mô tả nếu chưa set rõ
    lower_desc = (user_desc + " " + name).lower()
    if any(k in lower_desc for k in ["cây", "thực vật", "hoa", "dây leo", "gỗ", "lá", "plant", "flora", "tree"]):
        kingdom = "FLORA"
    elif any(k in lower_desc for k in ["nấm", "bào tử", "mush", "fung"]):
        kingdom = "FUNGI"
    elif any(k in lower_desc for k in ["lai", "cộng sinh", "hybrid"]):
        kingdom = "HYBRID"

    # 1. Mô tả chi tiết của người dùng
    if user_desc:
        parts.append(f"Mô tả nguyên mẫu sinh thái: {user_desc}.")

    # 2. Định danh và Giới Sinh Học
    kingdom_vn = {
        "FAUNA": "Giới Động vật (Fauna) di động",
        "FLORA": "Giới Thực vật (Flora) di động đặc hữu (cây ăn thịt, rễ bước, hoa dây leo bẫy gai)",
        "FUNGI": "Giới Nấm (Fungi) phát quang và cộng sinh bào tử",
        "HYBRID": "Dạng sống Sinh học Lai (Bio-Hybrid cộng sinh thú - thảo mộc)",
    }
    parts.append(f"Dạng sống: {kingdom_vn.get(kingdom, kingdom_vn['FAUNA'])}.")
    parts.append(f"Danh pháp: {name} ({latin}).")

    # 3. Vận động theo Tầng sống
    if kingdom == "FLORA":
        dom_flora = {
            "CAN": "Thân gỗ uốn dẻo bám đất bằng hệ thống 4 rễ cọc bẩy đất bò trườn, có dây leo tua cuốn",
            "NUOC": "Thảo mộc thủy sinh nổi rễ rủ nước, đài hoa xòe phao khí và vây lá chèo",
            "TROI": "Thực vật biểu sinh lơ lửng, phát tán bào tử và hạt có cánh lượn theo gió",
        }
        parts.append(f"Vận động cơ sinh học: {dom_flora.get(domain, dom_flora['CAN'])}.")
    else:
        dom_fauna = {
            "CAN": "Sống trên cạn, bốn chi choãi vững chãi và linh hoạt, có đuôi thăng bằng",
            "NUOC": "Sống dưới nước, thân thuôn hình thoi rẽ nước, vây ngực xoè rộng và vây đuôi đứng",
            "TROI": "Biết bay trên không, sải cánh lớn, xương nhẹ, chân có móng vuốt quắp cành",
        }
        parts.append(f"Môi trường & vận động: {dom_fauna.get(domain, dom_fauna['CAN'])}.")

    # 4. Chế độ dinh dưỡng & Chuyển hóa
    if kingdom == "FLORA":
        diet_flora = {
            "HERBIVORE": "Quang hợp tự dưỡng thuần khiết qua diệp lục và hút khoáng chất rễ",
            "CARNIVORE": "Thực vật ăn thịt săn mồi chủ động, bẫy kẹp thủy lực (Snap-trap) và tiết enzym tiêu hóa",
            "OMNIVORE": "Thực vật dị dưỡng kết hợp quang hợp và bẫy côn trùng mùn hữu cơ",
        }
        parts.append(f"Dinh dưỡng: {diet_flora.get(diet, diet_flora['HERBIVORE'])}.")
    else:
        diet_fauna = {
            "HERBIVORE": "Động vật ăn thực vật, mõm gặm cỏ hiền hòa",
            "CARNIVORE": "Thợ săn ăn thịt, cơ hàm khỏe và nanh nhọn",
            "OMNIVORE": "Động vật ăn tạp thích nghi cao",
        }
        parts.append(f"Chế độ ăn: {diet_fauna.get(diet, diet_fauna['HERBIVORE'])}.")

    # 5. Phân bổ Traits (0..7)
    if traits and len(traits) == 6:
        br, at, ar, sp, se, st = traits
        t_descs = []
        if kingdom == "FLORA":
            if br >= 3:
                t_descs.append("mạng rễ thần kinh dẫn truyền xung điện sinh học thông minh")
            if at >= 3:
                t_descs.append("bẫy kẹp đớp mồi chớp nhoáng hoặc chùm dây leo gai quất roi mạnh mẽ")
            if ar >= 3:
                t_descs.append("vỏ gỗ bần cổ thụ cứng cáp phủ rêu sáp kháng chấn")
            if sp >= 3:
                t_descs.append("rễ cọc vươn dài linh hoạt búng thân tốc lực")
            if se >= 3:
                t_descs.append("đài hoa bắt phấn và lông tơ cảm ứng chấn động địa chấn")
            if st >= 3:
                t_descs.append("bọng dịch tiêu hóa phồng to chứa đầy enzym đậm đặc")
        else:
            if br >= 3:
                t_descs.append("vòm sọ phồng cao thông minh")
            if at >= 3:
                t_descs.append("cơ bắp cuồn cuộn kèm móng vuốt và nanh nhọn")
            if ar >= 3:
                t_descs.append("vảy sừng cứng cáp xếp lớp bảo vệ lưng")
            if sp >= 3:
                t_descs.append("chân dài gân guốc nhanh nhẹn")
            if se >= 3:
                t_descs.append("đôi mắt to tròn hổ phách tinh tường")
            if st >= 3:
                t_descs.append("bụng tròn đầy đặn chứa nhiều năng lượng")

        if t_descs:
            parts.append(f"Đặc điểm giải phẫu: {', '.join(t_descs)}.")

    # 6. Đặc điểm sinh học (Features)
    if features:
        feat_vn_map = {
            "WEB_FEET": "chân có màng bơi giữa các ngón",
            "HARD_SHELL": "mai vỏ gỗ cứng che chắn lưng",
            "FANGS": "răng nanh hoặc gai nhọn bẫy mồi",
            "CAMOUFLAGE": "hoa văn vỏ cây ngụy trang hòa vào rừng lá",
            "CHEEK_POUCH": "túi chứa dinh dưỡng phình to",
            "GLIDER_FLAP": "màng lá lượn đón gió",
            "LUONG_CU": "chân màng, da rêu ẩm bóng",
            "GAI_DOC": "chùm gai độc tiết nhựa dọc thân",
            "RANG_NANH": "hai nanh nhọn chìa ra",
            "MAT_DEM": "mắt phát quang sinh học ban đêm",
            "DAO_HANG": "rễ bới đất ăn sâu vào lòng địa hình",
            "LONG_DAI": "lớp rêu lông tơ dày bảo ôn",
            "VAY_CUNG": "lớp vảy vỏ bần xếp lớp",
            "VO_SO": "vỏ mai cứng chắc",
            "RAU_CAM_UNG": "râu xúc tu hoa cảm nhận khí quyển",
            "TUI_MA": "bọng dự trữ nhựa",
            "CANH_LUOT": "cánh phiến lá lượn",
            "TREO_GIOI": "dây leo bám cành",
        }
        f_texts = [feat_vn_map[f] for f in features if f in feat_vn_map]
        if f_texts:
            parts.append(f"Đột biến sinh học: {', '.join(f_texts)}.")

    # 7. Phong cách mỹ thuật 3D
    parts.append(
        "Phong cách 3D sinh học hữu cơ tự nhiên cao cấp, bề mặt chi tiết sắc nét, "
        "độ bóng mờ Subsurface Scattering (SSS) sinh động, ánh sáng studio mềm mại, góc chụp 3/4, "
        "thể hiện rõ cả cấu trúc thân và các chi chuyển động, nền trung tính sạch sẽ."
    )

    return " ".join(parts)


def slugify(text: str) -> str:
    text = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[-\s]+", "_", text).strip("_") or "lifeform"


def create_svg_concept_card(
    filename: Path,
    name: str,
    latin: str,
    domain: str,
    diet: str,
    strategy: str,
    description: str,
    traits: list[int] | None,
    kingdom: str = "FAUNA",
) -> None:
    """Tạo concept card đồ họa vector SVG chuyên nghiệp cho mọi dạng sống (Động vật, Thực vật, Nấm)."""
    user_desc_safe = (description[:180] + "...") if len(description) > 180 else description

    lower_desc = (description + " " + name).lower()
    if any(k in lower_desc for k in ["cây", "thực vật", "hoa", "dây leo", "gỗ", "lá", "plant", "flora", "tree"]):
        kingdom = "FLORA"
    elif any(k in lower_desc for k in ["nấm", "bào tử", "mush", "fung"]):
        kingdom = "FUNGI"

    if kingdom == "FLORA":
        c_primary = "#22c55e" # Green
        c_secondary = "#a855f7" # Violet flower
        dom_badge = "🌿 THỰC VẬT"
    elif kingdom == "FUNGI":
        c_primary = "#eab308" # Bioluminescent yellow
        c_secondary = "#06b6d4" # Cyan glow
        dom_badge = "🍄 NẤM / BÀO TỬ"
    elif kingdom == "HYBRID":
        c_primary = "#06b6d4"
        c_secondary = "#ec4899"
        dom_badge = "🧬 SINH VẬT LAI"
    else:
        c_primary = "#38bdf8"
        c_secondary = "#f59e0b"
        dom_badge = "🐾 ĐỘNG VẬT"

    # SVG Center Graphic
    if kingdom == "FLORA":
        center_motif = f'''
    <!-- Carnivorous Plant / Treant Silhouette Motif -->
    <g transform="translate(180, 205)">
      <!-- Main Stem & Bark Core -->
      <path d="M-15,65 Q-5,0 0,-45 Q5,0 15,65" fill="{c_primary}" opacity="0.85"/>
      <!-- Flower Snap-Trap Head -->
      <ellipse cx="0" cy="-55" rx="35" ry="24" fill="{c_secondary}" opacity="0.9"/>
      <path d="M-35,-55 Q0,-72 35,-55" stroke="#facc15" stroke-width="3" fill="none"/>
      <!-- Trap Teeth -->
      <polygon points="-25,-55 -20,-42 -15,-55" fill="#f8fafc"/>
      <polygon points="-10,-55 -5,-40 0,-55" fill="#f8fafc"/>
      <polygon points="5,-55 10,-40 15,-55" fill="#f8fafc"/>
      <polygon points="20,-55 25,-42 30,-55" fill="#f8fafc"/>
      <!-- Walking Roots -->
      <path d="M-15,55 Q-45,75 -65,95" stroke="#78350f" stroke-width="10" stroke-linecap="round" fill="none"/>
      <path d="M15,55 Q45,75 65,95" stroke="#78350f" stroke-width="10" stroke-linecap="round" fill="none"/>
      <path d="M-5,60 Q-25,90 -35,100" stroke="#78350f" stroke-width="7" stroke-linecap="round" fill="none"/>
      <path d="M5,60 Q25,90 35,100" stroke="#78350f" stroke-width="7" stroke-linecap="round" fill="none"/>
      <!-- Vine Tendrils -->
      <path d="M-10,-10 Q-60,-20 -75,-60 Q-80,-75 -65,-75" stroke="{c_primary}" stroke-width="5" stroke-linecap="round" fill="none"/>
      <path d="M10,-10 Q60,-20 75,-60 Q80,-75 65,-75" stroke="{c_primary}" stroke-width="5" stroke-linecap="round" fill="none"/>
      <!-- Bioluminescent Spore Glows -->
      <circle cx="-65" cy="-75" r="4" fill="#facc15"/>
      <circle cx="65" cy="-75" r="4" fill="#facc15"/>
      <circle cx="0" cy="-25" r="6" fill="#facc15" opacity="0.8"/>
    </g>
        '''
    else:
        center_motif = f'''
    <!-- Fauna Silhouette Motif -->
    <g transform="translate(180, 205)">
      <ellipse cx="0" cy="15" rx="75" ry="38" fill="{c_primary}" opacity="0.35"/>
      <ellipse cx="0" cy="12" rx="65" ry="30" fill="{c_primary}" opacity="0.8"/>
      <circle cx="-50" cy="-6" r="28" fill="{c_primary}" opacity="0.9"/>
      <circle cx="-56" cy="-12" r="6" fill="#facc15"/>
      <circle cx="-56" cy="-12" r="2.5" fill="#0b1120"/>
      <path d="M-68,6 C-62,18 -45,18 -38,10" stroke="#0b1120" stroke-width="3" fill="none"/>
      <path d="M-30,30 Q-45,60 -60,65" stroke="{c_primary}" stroke-width="8" stroke-linecap="round" fill="none"/>
      <path d="M25,30 Q35,60 48,65" stroke="{c_primary}" stroke-width="8" stroke-linecap="round" fill="none"/>
      <path d="M60,10 Q105,-15 115,20" stroke="{c_primary}" stroke-width="12" stroke-linecap="round" fill="none"/>
      <polygon points="-20,-12 -14,-34 -6,-12" fill="#f59e0b"/>
      <polygon points="5,-14 12,-38 20,-14" fill="#f59e0b"/>
      <polygon points="30,-12 36,-32 44,-12" fill="#f59e0b"/>
    </g>
        '''

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 450" width="100%" height="100%">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090e17"/>
      <stop offset="100%" stop-color="#141e33"/>
    </linearGradient>
    <linearGradient id="glow" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{c_primary}" stop-opacity="0.8"/>
      <stop offset="100%" stop-color="{c_secondary}" stop-opacity="0.8"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="6" stdDeviation="10" flood-color="#000" flood-opacity="0.6"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="600" height="450" rx="14" fill="url(#bg)" stroke="rgba(56, 189, 248, 0.3)" stroke-width="1.5"/>

  <!-- Top Badge -->
  <rect x="25" y="22" width="550" height="42" rx="8" fill="rgba(15, 23, 42, 0.9)" stroke="rgba(255,255,255,0.1)"/>
  <text x="40" y="48" font-family="system-ui, sans-serif" font-size="14" font-weight="bold" fill="#f8fafc">🧬 AGY CONCEPT ART · {name.upper()}</text>
  <text x="560" y="48" font-family="system-ui, sans-serif" font-size="12" fill="{c_primary}" text-anchor="end" font-weight="bold">{dom_badge} · {domain}</text>

  <!-- Center Motif Creature Box -->
  <rect x="25" y="76" width="310" height="260" rx="10" fill="rgba(2, 6, 23, 0.6)" stroke="url(#glow)" stroke-width="1.2" filter="url(#shadow)"/>
  {center_motif}
  <text x="180" y="322" font-family="system-ui, sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle" font-style="italic">"{latin}"</text>

  <!-- Right Attribute Panel -->
  <rect x="350" y="76" width="225" height="260" rx="10" fill="rgba(15, 23, 42, 0.7)" stroke="rgba(255,255,255,0.08)"/>
  <text x="365" y="102" font-family="system-ui, sans-serif" font-size="11" font-weight="bold" fill="#38bdf8">THUỘC TÍNH TIẾN HÓA</text>

  <text x="365" y="128" font-family="system-ui, sans-serif" font-size="11" fill="#cbd5e1">Dinh dưỡng: <tspan fill="#4ade80" font-weight="bold">{diet}</tspan></text>
  <text x="365" y="150" font-family="system-ui, sans-serif" font-size="11" fill="#cbd5e1">Chiến lược: <tspan fill="#facc15" font-weight="bold">{strategy}</tspan></text>

  <text x="365" y="180" font-family="system-ui, sans-serif" font-size="11" font-weight="bold" fill="#a78bfa">CHỈ SỐ TRAITS (Quỹ {sum(traits) if traits else 16}đ)</text>
  <text x="365" y="202" font-family="monospace" font-size="10" fill="#94a3b8">Brain:  {traits[0] if traits else 1} | Attack: {traits[1] if traits else 0}</text>
  <text x="365" y="222" font-family="monospace" font-size="10" fill="#94a3b8">Armor:  {traits[2] if traits else 1} | Speed:  {traits[3] if traits else 4}</text>
  <text x="365" y="242" font-family="monospace" font-size="10" fill="#94a3b8">Sense:  {traits[4] if traits else 3} | Stomach:{traits[5] if traits else 3}</text>

  <rect x="365" y="260" width="195" height="60" rx="6" fill="rgba(0,0,0,0.4)"/>
  <text x="375" y="278" font-family="system-ui, sans-serif" font-size="9.5" fill="{c_primary}" font-weight="bold">BLENDER 3D + 8 ANIMATIONS:</text>
  <text x="375" y="295" font-family="system-ui, sans-serif" font-size="9" fill="#4ade80">✓ Idle, Alert, Walk, Run</text>
  <text x="375" y="310" font-family="system-ui, sans-serif" font-size="9" fill="#4ade80">✓ Attack, Hurt, Eat, Death</text>

  <!-- Bottom User Prompt Quote -->
  <rect x="25" y="348" width="550" height="78" rx="8" fill="rgba(15, 23, 42, 0.85)" stroke="rgba(56, 189, 248, 0.2)"/>
  <text x="40" y="370" font-family="system-ui, sans-serif" font-size="10.5" font-weight="bold" fill="#38bdf8">MÔ TẢ CỦA BẠN ({len(description)}/500 KÝ TỰ):</text>
  <text x="40" y="392" font-family="system-ui, sans-serif" font-size="10" fill="#e2e8f0" font-style="italic">"{user_desc_safe or 'Mô tả sinh thái mặc định'}"</text>
  <text x="40" y="412" font-family="system-ui, sans-serif" font-size="9" fill="#64748b">Bản concept SVG; trạng thái xuất mô hình được báo riêng trong kết quả.</text>
</svg>'''
    filename.write_text(svg, encoding="utf-8")


def generate_creature_concept_and_3d(
    name: str = "Thỏ Đồng Cỏ",
    latin: str = "Sylvilagus Campestris",
    domain: str = "CAN",
    diet: str = "HERBIVORE",
    strategy: str = "STRAT_R",
    traits: list[int] | None = None,
    features: list[str] | None = None,
    description: str = "",
    kingdom: str = "FAUNA",
    custom_api_key: str | None = None,
) -> dict[str, Any]:
    """Tạo Concept Art (AGY/SVG) + Dựng 3D Blender trọn bộ 8 Animations."""
    slug = slugify(f"{name}_{domain}_{diet}") + "_" + uuid.uuid4().hex[:12]
    CONCEPTS_DIR.mkdir(parents=True, exist_ok=True)
    CREATURES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Tổng hợp master prompt
    master_prompt = build_master_concept_prompt(
        name=name,
        latin=latin,
        domain=domain,
        diet=diet,
        strategy=strategy,
        traits=traits,
        features=features,
        description=description,
        kingdom=kingdom,
    )

    # 2. Tạo concept art
    img_filename = f"concept_{slug}.svg"
    img_path = CONCEPTS_DIR / img_filename
    create_svg_concept_card(
        filename=img_path,
        name=name,
        latin=latin,
        domain=domain,
        diet=diet,
        strategy=strategy,
        description=description,
        traits=traits,
        kingdom=kingdom,
    )
    image_url = f"/watch/concepts/{img_filename}"

    # 3. Dựng mô hình 3D trong Blender (kèm Rigging + TRỌN BỘ 8 ANIMATIONS)
    glb_filename = f"creature_{slug}.glb"
    blend_filename = f"creature_{slug}.blend"
    out_glb = CREATURES_DIR / glb_filename
    out_blend = CREATURES_DIR / blend_filename

    @dataclass
    class CreatureStats:
        brain: int
        attack: int
        armor: int
        speed: int
        sense: int
        stomach: int

    t_vals = traits if (traits and len(traits) == 6) else [1, 0, 1, 4, 3, 3]
    try:
        creature_traits: Any = Traits(
            brain=t_vals[0],
            attack=t_vals[1],
            armor=t_vals[2],
            speed=t_vals[3],
            sense=t_vals[4],
            stomach=t_vals[5],
        )
    except (AssertionError, ValueError):
        creature_traits = CreatureStats(
            brain=t_vals[0],
            attack=t_vals[1],
            armor=t_vals[2],
            speed=t_vals[3],
            sense=t_vals[4],
            stomach=t_vals[5],
        )

    active_feats = []
    feat_lookup = {f.key: f for f in FEATURES}
    if features:
        for fid in features:
            if fid in feat_lookup:
                active_feats.append(feat_lookup[fid])
            elif fid == "CAMOUFLAGE":
                active_feats.append(feat_lookup.get("LUONG_CU", FEATURES[0]))

    creature_domain = Domain(domain) if domain in ("CAN", "NUOC", "TROI") else Domain.CAN

    blender_code = build_creature_blender_code(
        species_id=slug[:8],
        seed=1,
        traits=creature_traits,
        domain=creature_domain,
        features=active_feats,
        out_glb=str(out_glb),
        out_blend=str(out_blend),
    )

    blender_bin = _find_blender()
    model_ready = False
    error: str | None = "BLENDER_UNAVAILABLE"
    if blender_bin:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", encoding="utf-8", delete=False) as tf:
            tf.write(blender_code)
            tmp_py = tf.name
        try:
            cmd = [blender_bin, "--background", "--python", tmp_py]
            result = subprocess.run(cmd, capture_output=True, text=True,
                                    encoding="utf-8", errors="replace", timeout=18)
            model_ready = (result.returncode == 0 and out_glb.is_file()
                           and out_glb.stat().st_size > 0 and out_blend.is_file()
                           and out_blend.stat().st_size > 0)
            error = None if model_ready else "BLENDER_FAILED_OR_MISSING_OUTPUT"
        except (OSError, subprocess.SubprocessError) as exc:
            error = "BLENDER_TIMEOUT" if isinstance(exc, subprocess.TimeoutExpired) else "BLENDER_FAILED"
            logger.warning("Concept model generation failed: %s", error)
        finally:
            if os.path.isfile(tmp_py):
                os.remove(tmp_py)

    return {
        "ok": model_ready,
        "status": "complete" if model_ready else "concept_only",
        "error": error,
        "image_kind": "svg_card",
        "name": name,
        "latin": latin,
        "kingdom": kingdom,
        "prompt": master_prompt,
        "image_url": image_url,
        "glb_url": f"/assets/creatures/{glb_filename}" if model_ready else None,
        "blend_url": f"/assets/creatures/{blend_filename}" if model_ready else None,
        "message": "Đã tạo SVG và xuất mô hình." if model_ready else "Đã tạo SVG; chưa xuất được mô hình 3D.",
    }
