#!/usr/bin/env python3
"""R-03 · GRPO + LoRA trên dữ liệu do ván sinh ra.

    python scripts/r03_train.py --data runs/train.jsonl --out runs/lora/ [--dry-run]
    python scripts/r03_train.py --data runs/train.jsonl --out runs/lora/ \
        --model Qwen/Qwen2.5-0.5B-Instruct --steps 40

**GRPO ngoại tuyến (offline).** Bản GRPO thường sinh rollout NGAY TRONG vòng
huấn luyện; ở đây rollout đã có sẵn — chúng là những ván đã chơi — nên vòng lặp
chỉ cần tính lại log-prob. Điều đó bỏ được phần đắt nhất và cũng đúng bản chất
bài toán: phần thưởng của v5 là **của cả ván** (03 §0), nên không có gì để sinh
lại giữa chừng.

Mục tiêu:

    L = − Σ  A_i · log π(y_i | x_i)  +  β · KL(π ‖ π_ref)

`A_i` chuẩn hoá **trong nhóm** (cùng seed, cùng cá thể, cùng lượt) — cùng đề bài,
khác lần bốc. So hai rollout khác seed là so hai đề bài khác nhau, và "lợi thế"
đo được sẽ là *đề nào dễ hơn* chứ không phải *lần nào nghĩ khá hơn*.

`π_ref` là chính base model đóng băng: với LoRA thì chỉ cần **tắt adapter**, không
cần nạp bản sao thứ hai vào RAM.

**KHÔNG cần `trl`.** `GRPOTrainer` của nó dựng cho vòng sinh trực tuyến; ở đây
nó chỉ thêm một tầng phụ thuộc mà không làm hộ được gì.

Ba điều đã **đo được** và chúng định hình thiết kế bên dưới:

1. Môi trường nhanh hơn ngân sách ~200× (0,07 s cho một ván 150 tick). Nút cổ
   chai là model, không phải Python.
2. Trên máy này (llama.cpp/Metal), **4 lời gọi song song mất 2,3× thời gian một
   lời gọi** — decode gần như tuần tự. Nên tăng số worker không tăng thông lượng;
   thứ tăng được là **số máy**, và đó đúng là hình dạng chế độ mở ở docs/04.
3. Reward là **của cả ván**, không của từng bước (docs/03 §0): tín hiệu kiểm
   chứng được chỉ tồn tại ở cuối ván. Vì thế GRPO — so các rollout **cùng một
   đề bài** với nhau — hợp hơn PPO có value head: không cần học một hàm giá trị
   cho một tín hiệu chỉ xuất hiện một lần.

Nhóm GRPO phải là **cùng một seed** (cùng luật ẩn, cùng thế giới), khác nhau ở
sampling. So hai rollout khác seed là so hai đề bài khác nhau, và lợi thế đo được
sẽ là "đề nào dễ hơn" chứ không phải "lần nào nghĩ khá hơn".
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
import statistics
import sys
from typing import Any

MIN_GROUP = 2


def load(path: Path) -> list[dict[str, Any]]:
    return [json.loads(l) for l in Path(path).read_text(encoding="utf-8").splitlines() if l.strip()]


def group_for_grpo(rows: list[dict[str, Any]]) -> dict[tuple, list[dict]]:
    """Nhóm theo (seed, creature_id, t): cùng đề bài, khác lần bốc.

    Nhóm chỉ có MỘT phần tử thì bỏ: GRPO chuẩn hoá lợi thế **trong nhóm**, nên
    một nhóm một phần tử cho lợi thế bằng 0 và chỉ làm loãng gradient.
    """
    g: dict[tuple, list[dict]] = collections.defaultdict(list)
    for r in rows:
        g[(r["seed"], r["creature_id"], r["t"])].append(r)
    return {k: v for k, v in g.items() if len(v) >= MIN_GROUP}


def advantages(group: list[dict[str, Any]]) -> list[float]:
    """Lợi thế chuẩn hoá trong nhóm. Phương sai 0 -> toàn 0, không chia cho 0."""
    rs = [float(r["reward"]) for r in group]
    mu = statistics.fmean(rs)
    sd = statistics.pstdev(rs)
    if sd == 0:
        return [0.0] * len(rs)
    return [round((r - mu) / sd, 6) for r in rs]


def prepare(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key, group in sorted(group_for_grpo(rows).items()):
        for r, adv in zip(group, advantages(group)):
            if adv == 0.0:
                continue        # không có tín hiệu thì không có gradient
            out.append({"prompt": r["prompt"], "response": r["response"],
                        "advantage": adv, "reward": r["reward"], "group": list(key)})
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("runs/lora"))
    ap.add_argument("--dry-run", action="store_true",
                    help="chỉ chuẩn bị dữ liệu và in thống kê, không nạp model")
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B-Instruct")
    ap.add_argument("--steps", type=int, default=40)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--beta", type=float, default=0.1,
                    help="hệ số phạt KL — 0.02 quá nhẹ, KL trôi đều suốt 30 bước đầu")
    ap.add_argument("--max-len", type=int, default=1024)
    a = ap.parse_args(argv)

    rows = load(a.data)
    prepared = prepare(rows)
    groups = group_for_grpo(rows)
    print(f"mẫu thô        : {len(rows)}")
    print(f"nhóm GRPO >= {MIN_GROUP} : {len(groups)}")
    print(f"mẫu có lợi thế : {len(prepared)}")
    if prepared:
        advs = [abs(r["advantage"]) for r in prepared]
        print(f"|lợi thế| trung vị: {statistics.median(advs):.3f}")

    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / "grpo_data.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in prepared) + "\n",
        encoding="utf-8",
    )
    print(f"đã ghi {a.out / 'grpo_data.jsonl'}")

    if a.dry_run:
        return 0
    if not prepared:
        print("không có mẫu nào mang lợi thế khác 0 — không có gì để học.",
              file=sys.stderr)
        return 1
    return train(prepared, a)


def train(prepared: list[dict[str, Any]], a: argparse.Namespace) -> int:
    try:
        import torch
        from peft import LoraConfig, get_peft_model
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:
        print(f"thiếu thư viện huấn luyện: {exc}\n"
              "  pip install 'torch' 'transformers>=4.45' 'peft>=0.7'", file=sys.stderr)
        return 2

    device = ("mps" if torch.backends.mps.is_available()
              else "cuda" if torch.cuda.is_available() else "cpu")
    print(f"thiết bị: {device} · model: {a.model}")

    tok = AutoTokenizer.from_pretrained(a.model)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float32)
    model = get_peft_model(model, LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.0, bias="none", task_type="CAUSAL_LM",
        target_modules=["q_proj", "v_proj"],
    )).to(device)
    model.print_trainable_parameters()

    opt = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad], lr=a.lr
    )

    def logprob(sample: dict, use_adapter: bool) -> "torch.Tensor":
        """log π(response | prompt), tổng trên các token của response.

        Chỉ tính trên phần **response**: prompt bị che bằng -100. Không che thì
        model được thưởng vì dự đoán lại chính prompt của nó, và gradient bị chi
        phối bởi một thứ không liên quan gì tới quyết định.
        """
        p_ids = tok(sample["prompt"], return_tensors="pt",
                    truncation=True, max_length=a.max_len).input_ids
        r_ids = tok(sample["response"], return_tensors="pt",
                    add_special_tokens=False).input_ids
        ids = torch.cat([p_ids, r_ids], dim=1)[:, -a.max_len:].to(device)
        n_resp = min(r_ids.shape[1], ids.shape[1] - 1)
        if n_resp <= 0:
            return None

        ctx = model.disable_adapter() if not use_adapter else _nullctx()
        with ctx:
            out = model(ids).logits[:, :-1, :]
        target = ids[:, 1:]
        logp = torch.log_softmax(out.float(), dim=-1)
        picked = logp.gather(-1, target.unsqueeze(-1)).squeeze(-1)
        return picked[:, -n_resp:].sum()

    def _resp_len(sample: dict, tokenizer, max_len: int) -> int:
        return len(tokenizer(sample["response"], add_special_tokens=False).input_ids)

    history: list[float] = []
    n = min(a.steps, len(prepared))
    for step in range(n):
        s_i = prepared[step % len(prepared)]
        lp = logprob(s_i, use_adapter=True)
        if lp is None:
            continue
        with torch.no_grad():
            lp_ref = logprob(s_i, use_adapter=False)

        adv = float(s_i["advantage"])
        # Chuẩn hoá theo ĐỘ DÀI câu trả lời. Không chuẩn hoá thì một câu dài
        # được (hoặc bị) nhân lên chỉ vì nó dài: tổng log-prob tỉ lệ với số
        # token, nên gradient bị chi phối bởi độ dài chứ không bởi lợi thế.
        # KL xấp xỉ bằng chênh lệch log-prob trên chính chuỗi đã lấy mẫu — ước
        # lượng một mẫu, đủ cho mục đích giữ policy không trôi xa.
        kl = lp - lp_ref
        n_tok = max(1, _resp_len(s_i, tok, a.max_len))
        loss = (-(adv * lp) + a.beta * kl.abs()) / n_tok

        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(
            [p for p in model.parameters() if p.requires_grad], 1.0
        )
        opt.step()
        history.append(float(loss.detach()))
        if (step + 1) % max(1, n // 10) == 0 or step == 0:
            print(f"  bước {step + 1:>3}/{n}  loss {history[-1]:+9.3f}  "
                  f"adv {adv:+.3f}  KL {float(kl.detach()):+.3f}")

    model.save_pretrained(str(a.out / "adapter"))
    print(f"đã lưu adapter vào {a.out / 'adapter'}")
    if len(history) >= 4:
        h = len(history) // 2
        print(f"loss trung bình: nửa đầu {statistics.fmean(history[:h]):+.3f} "
              f"-> nửa sau {statistics.fmean(history[h:]):+.3f}")
    return 0


class _nullctx:
    def __enter__(self): return None
    def __exit__(self, *a): return False


if __name__ == "__main__":
    raise SystemExit(main())
