#!/usr/bin/env python3
"""Dựng docs/site.html từ toàn bộ bộ tài liệu. Chạy lại sau mỗi lần sửa .md."""
import re, html, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import md as MD

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
TASKS = DOCS / "tasks"

# Trạng thái đọc từ docs/01-STATUS.md — nguồn sự thật duy nhất.
STATUS_RE = re.compile(r"\|\s*\[([SWLBNXR]-\d\d)\]\([^)]*\)\s*\|[^|]*\|\s*([✅🟨⬜🚫])\s*\|")

TRACKS = {
    "S": ("Chuẩn bị",   "Môi trường, model, công cụ"),
    "W": ("Thế giới",   "Sandbox 2D — v4 M0+M1 và mở rộng v5"),
    "L": ("Luật",       "Động cơ luật ẩn và bộ chấm"),
    "B": ("Tâm trí",    "Tầng LLM, prompt, Sổ Luật, điểm"),
    "N": ("Thế giới mở","Nhiều máy qua internet"),
}

STATUS = dict(STATUS_RE.findall((DOCS / "01-STATUS.md").read_text(encoding="utf-8")))

# ── thu thập ────────────────────────────────────────────────────────────
sections = []          # (sid, kind, code, title, subtitle, markdown_text)
path2sid = {}

readme = (ROOT / "README.md").read_text(encoding="utf-8")
sections.append(("overview", "doc", "", "Genesis Zero", "Tổng quan", readme))
path2sid["README.md"] = "overview"

doc_files = sorted(p for p in DOCS.glob("*.md") if not p.name.startswith("_"))
for p in doc_files:
    num = p.name[:2]
    sid = "d" + num
    txt = p.read_text(encoding="utf-8")
    m = re.match(r"^#\s*(.*)", txt)
    full = m.group(1).strip() if m else p.stem
    title = full.split("·", 1)[1].strip() if "·" in full else full
    sections.append((sid, "doc", num, title, "", txt))
    path2sid[f"docs/{p.name}"] = sid
    path2sid[p.name] = sid

task_meta = []
for p in sorted(TASKS.glob("*.md")):
    if p.name.startswith("_"):
        continue
    code = p.stem.split("-")[0] + "-" + p.stem.split("-")[1]
    sid = "t" + code
    txt = p.read_text(encoding="utf-8")
    m = re.match(r"^#\s*(.*)", txt)
    full = m.group(1).strip() if m else code
    title = full.split("·", 1)[1].strip() if "·" in full else full
    title = title.replace("✦", "").replace("★", "").strip()
    dm = re.search(r"Giao cho model rẻ\?\*{0,2}\s*\|\s*([✅⚠️❌])", txt)
    st = STATUS.get(code, "⬜")
    if not dm:
        dm = re.search(r"Giao cho model rẻ\?\*{0,2}\s*\|\s*\**\s*([✅⚠️❌])", txt)
    deleg = dm.group(1) if dm else "❌"
    gate = "✦" in full or "★" in full
    sections.append((sid, "task", code, title, "", txt))
    path2sid[f"docs/tasks/{p.name}"] = sid
    path2sid[f"tasks/{p.name}"] = sid
    path2sid[p.name] = sid
    task_meta.append({"code": code, "sid": sid, "title": title,   # thô; nav dùng plain()
                      "track": code[0], "deleg": deleg, "gate": gate,
                      "status": st, "done": st == "✅"})

DEAD = {"config.py", "genesis-zero-plan (4).md", "docs/tasks/", "docs/_goc-plan-v4.md",
        "docs/tasks/_MAU.md", "_MAU.md", "tasks/_MAU.md"}

def make_linkfn(cur_dir):
    def fn(href):
        if href.startswith(("http://", "https://", "mailto:")):
            return href, ' class="ext"', ' target="_blank" rel="noopener"'
        raw = html.unescape(href)
        base, _, anchor = raw.partition("#")
        base = base.replace("%20", " ")
        if not base:
            return "#" + anchor, ' class="xref"', ""
        try:
            norm = (cur_dir / base).resolve().relative_to(ROOT).as_posix()
        except Exception:
            norm = base
        if norm in DEAD or base in DEAD:
            return None, "", ""
        sid = path2sid.get(norm) or path2sid.get(base) or path2sid.get(pathlib.Path(base).name)
        if not sid:
            return None, "", ""
        target = f"#{sid}--{anchor}" if anchor else f"#{sid}"
        return target, ' class="xref"', ""
    return fn

bodies, tocs = {}, {}
for sid, kind, code, title, sub, txt in sections:
    cur_dir = ROOT if sid == "overview" else (TASKS if kind == "task" else DOCS)
    body = re.sub(r"^#\s.*\n", "", txt, count=1)          # bỏ h1, đã có ở header
    body = re.sub(r"^>\s*\[00 Bản đồ\].*\n", "", body, flags=re.M)  # bỏ dải nav .md
    h, heads = MD.render(body, make_linkfn(cur_dir), idprefix=sid)
    bodies[sid] = h
    tocs[sid] = [(s, t) for lvl, s, t in heads if lvl == 2]

# ── HTML ────────────────────────────────────────────────────────────────
def esc(s): return html.escape(s, quote=True)

def plain(s):
    return s.replace('`', '').replace('**', '').replace('*', '')

def rich(s):
    return MD.inline(s, lambda h: (None, "", ""))

nav = []
nav.append('<div class="navgroup"><div class="navgroup-h">Tài liệu</div><ul class="navlist">')
for sid, kind, code, title, sub, _ in sections:
    if kind != "doc":
        continue
    label = code if code else "—"
    nav.append(f'<li><a class="navitem" data-sid="{sid}" data-hay="{esc((code+" "+title).lower())}" href="#{sid}">'
               f'<span class="chip chip-doc">{esc(label)}</span><span class="nav-t">{esc(plain(title))}</span></a></li>')
nav.append("</ul></div>")

for tk, (tname, tdesc) in TRACKS.items():
    items = [t for t in task_meta if t["track"] == tk]
    nav.append(f'<div class="navgroup" data-track="{tk}">'
               f'<div class="navgroup-h"><span class="tdot" style="background:var(--t-{tk})"></span>{esc(tname)}'
               f'<span class="navgroup-n">{len(items)}</span></div><ul class="navlist">')
    for t in items:
        g = '<span class="gate" title="Mốc chốt">✦</span>' if t["gate"] else ""
        scls = {"✅": "st-done", "🟨": "st-wip", "🚫": "st-blk"}.get(t["status"], "st-todo")
        nav.append(f'<li><a class="navitem" data-sid="{t["sid"]}" data-deleg="{t["deleg"]}" '
                   f'data-hay="{esc((t["code"]+" "+t["title"]).lower())}" href="#{t["sid"]}">'
                   f'<span class="chip" style="--c:var(--t-{tk})">{esc(t["code"])}</span>'
                   f'<span class="nav-t">{esc(plain(t["title"]))}</span>{g}'
                   f'<span class="dg dg-{"y" if t["deleg"]=="✅" else ("m" if t["deleg"]=="⚠️" else "n")}"></span>'
                   f'<span class="st {scls}"></span></a></li>')
    nav.append("</ul></div>")

arts = []
for sid, kind, code, title, sub, _ in sections:
    tk = code[0] if kind == "task" else None
    eyebrow = ""
    if kind == "task":
        tname = TRACKS[tk][0]
        st = next((m["status"] for m in task_meta if m["code"] == code), "⬜")
        stt = {"✅": "Xong", "🟨": "Đang làm", "🚫": "Bị chặn"}.get(st, "Chưa bắt đầu")
        scls = {"✅": "st-done", "🟨": "st-wip", "🚫": "st-blk"}.get(st, "st-todo")
        eyebrow = (f'<div class="eyebrow"><span class="chip chip-lg" style="--c:var(--t-{tk})">{esc(code)}</span>'
                   f'<span class="eyebrow-t">{esc(tname)}</span>'
                   f'<span class="statepill"><span class="st {scls}"></span>{stt}</span></div>')
    elif code:
        eyebrow = f'<div class="eyebrow"><span class="chip chip-doc chip-lg">{esc(code)}</span><span class="eyebrow-t">Tài liệu</span></div>'
    else:
        eyebrow = f'<div class="eyebrow"><span class="eyebrow-t">{esc(sub)}</span></div>'
    toc = ""
    if len(tocs[sid]) > 2:
        toc = '<nav class="toc" aria-label="Mục trong trang"><div class="toc-h">Trong trang</div><ul>' + "".join(
            f'<li><a href="#{s}">{esc(t)}</a></li>' for s, t in tocs[sid]) + "</ul></nav>"
    arts.append(f'<article class="doc" id="{sid}" hidden>{eyebrow}'
                f'<h1 class="doc-h">{rich(title)}</h1>{toc}'
                f'<div class="prose">{bodies[sid]}</div></article>')

DATA = json.dumps({"tasks": task_meta}, ensure_ascii=False)

CSS = r"""
:root{
  --bg:#F1F3F2; --bg-2:#E8ECEA; --surface:#FFFFFF; --surface-2:#F7F9F8;
  --ink:#15211E; --ink-2:#4E5B57; --ink-3:#5F6C66;
  --rule:#D3DBD8; --rule-soft:#E4E9E7;
  --accent:#9C5C16; --accent-2:#B87428; --accent-soft:#F3E6D4;
  --teal:#0E6355; --teal-soft:#DCEBE7;
  --code-bg:#F4F7F6; --code-ink:#233029; --code-rule:#E1E8E5;
  --shadow:0 1px 2px rgba(21,33,30,.05),0 8px 24px -16px rgba(21,33,30,.25);
  --t-S:#456479; --t-W:#376F49; --t-L:#8E5313; --t-B:#634FA0; --t-N:#1E7280; --t-X:#95492F; --t-R:#8F4571;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --bg:#0E1413; --bg-2:#0A100F; --surface:#151D1B; --surface-2:#111917;
  --ink:#E3EAE7; --ink-2:#A6B4AF; --ink-3:#7C8A85;
  --rule:#25312E; --rule-soft:#1B2523;
  --accent:#DFA157; --accent-2:#EDBB7C; --accent-soft:#2A2115;
  --teal:#55BAA6; --teal-soft:#122A26;
  --code-bg:#0C1211; --code-ink:#C6D3CE; --code-rule:#1E2A27;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 12px 32px -20px rgba(0,0,0,.8);
  --t-S:#7DA3C0; --t-W:#68B383; --t-L:#DFA157; --t-B:#A38FDC; --t-N:#4FB6C4; --t-X:#D28468; --t-R:#D084B0;
}}
:root[data-theme="dark"]{
  --bg:#0E1413; --bg-2:#0A100F; --surface:#151D1B; --surface-2:#111917;
  --ink:#E3EAE7; --ink-2:#A6B4AF; --ink-3:#7C8A85;
  --rule:#25312E; --rule-soft:#1B2523;
  --accent:#DFA157; --accent-2:#EDBB7C; --accent-soft:#2A2115;
  --teal:#55BAA6; --teal-soft:#122A26;
  --code-bg:#0C1211; --code-ink:#C6D3CE; --code-rule:#1E2A27;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 12px 32px -20px rgba(0,0,0,.8);
  --t-S:#7DA3C0; --t-W:#68B383; --t-L:#DFA157; --t-B:#A38FDC; --t-N:#4FB6C4; --t-X:#D28468; --t-R:#D084B0;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
 font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;font-size:15.5px;line-height:1.68;
 -webkit-font-smoothing:antialiased}
a{color:var(--teal);text-decoration:none}
a:hover{text-decoration:underline;text-underline-offset:3px}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:3px}

/* ── vỏ ── */
.shell{display:grid;grid-template-columns:302px minmax(0,1fr);min-height:100vh}
.rail{position:sticky;top:0;height:100vh;overflow:hidden;display:flex;flex-direction:column;
 background:var(--bg-2);border-right:1px solid var(--rule)}
.brand{padding:20px 20px 14px;border-bottom:1px solid var(--rule)}
.brand-t{font-family:"IBM Plex Serif",Georgia,serif;font-weight:600;font-size:19px;letter-spacing:-.01em;margin:0}
.brand-s{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:10.5px;letter-spacing:.11em;
 text-transform:uppercase;color:var(--ink-3);margin-top:5px}
.meter{margin-top:12px;display:flex;align-items:center;gap:9px}
.meter-bar{flex:1;height:4px;background:var(--rule);border-radius:99px;overflow:hidden}
.meter-fill{height:100%;width:0%;background:var(--accent)}
.meter-n{font-family:"IBM Plex Mono",monospace;font-size:11px;color:var(--ink-2);font-variant-numeric:tabular-nums}

.tools{padding:12px 14px;border-bottom:1px solid var(--rule);display:flex;flex-direction:column;gap:9px}
.search{width:100%;padding:7px 10px;border:1px solid var(--rule);border-radius:6px;background:var(--surface);
 color:var(--ink);font:inherit;font-size:13.5px}
.search::placeholder{color:var(--ink-3)}
.filters{display:flex;gap:5px}
.fbtn{flex:1;padding:5px 4px;border:1px solid var(--rule);background:var(--surface);color:var(--ink-2);
 border-radius:6px;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.03em}
.fbtn:hover{border-color:var(--ink-3)}
.fbtn[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:var(--bg-2)}

.nav{flex:1;overflow-y:auto;padding:10px 8px 40px}
.navgroup{margin-bottom:14px}
.navgroup-h{display:flex;align-items:center;gap:7px;padding:6px 10px;font-family:"IBM Plex Mono",monospace;
 font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--ink-3)}
.navgroup-n{margin-left:auto;font-variant-numeric:tabular-nums;opacity:.75}
.tdot{width:7px;height:7px;border-radius:2px;flex:none}
.navlist{list-style:none;margin:0;padding:0}
.navitem{display:flex;align-items:center;gap:8px;padding:5px 10px;border-radius:6px;color:var(--ink-2);
 font-size:13.5px;line-height:1.35}
.navitem:hover{background:var(--surface);color:var(--ink);text-decoration:none}
.navitem.on{background:var(--surface);color:var(--ink);box-shadow:var(--shadow)}
.navitem.on .chip{opacity:1}
.nav-t{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1}
.chip{font-family:"IBM Plex Mono",monospace;font-size:10.5px;font-weight:600;letter-spacing:.02em;
 padding:2px 5px;border-radius:4px;flex:none;color:var(--c,var(--ink-2));
 background:color-mix(in srgb,var(--c,var(--ink-3)) 14%,transparent);
 border:1px solid color-mix(in srgb,var(--c,var(--ink-3)) 30%,transparent);opacity:.9}
.chip-doc{--c:var(--ink-3)}
.gate{color:var(--accent);font-size:11px;flex:none}
.dg{width:5px;height:5px;border-radius:99px;flex:none}
.st{width:8px;height:8px;border-radius:2px;flex:none}
.st-todo{border:1px solid var(--ink-3);background:transparent}
.st-wip{background:var(--accent)}
.st-done{background:var(--t-W)}
.st-blk{background:var(--t-X)}
.statepill{margin-left:auto;display:inline-flex;align-items:center;gap:6px;
 font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
 color:var(--ink-3);border:1px solid var(--rule);border-radius:99px;padding:3px 10px}
.dg-y{background:var(--t-W)} .dg-m{background:var(--accent)} .dg-n{background:var(--rule);border:1px solid var(--ink-3)}

/* ── nội dung ── */
.main{min-width:0;padding:0 0 96px}
.topbar{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:12px;
 padding:11px 40px;background:color-mix(in srgb,var(--bg) 88%,transparent);
 backdrop-filter:saturate(1.4) blur(8px);border-bottom:1px solid var(--rule-soft)}
.crumb{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:var(--ink-3)}
.topbar-sp{flex:1}
.iconbtn{border:1px solid var(--rule);background:var(--surface);color:var(--ink-2);border-radius:6px;
 padding:5px 9px;cursor:pointer;font-family:"IBM Plex Mono",monospace;font-size:11px}
.iconbtn:hover{color:var(--ink);border-color:var(--ink-3)}
.menu{display:none}

.doc{max-width:min(1080px,100%);margin:0 auto;padding:34px 40px 0}
.eyebrow{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.chip-lg{font-size:12px;padding:3px 8px}
.eyebrow-t{font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.11em;text-transform:uppercase;color:var(--ink-3)}
.doc-h code{font-family:"IBM Plex Mono",monospace;font-size:.82em;font-weight:500;
 background:var(--code-bg);border:1px solid var(--code-rule);border-radius:6px;padding:1px 7px;color:var(--accent)}
.doc-h{font-family:"IBM Plex Serif",Georgia,serif;font-weight:600;font-size:clamp(27px,3.4vw,38px);
 line-height:1.16;letter-spacing:-.017em;margin:0 0 26px;text-wrap:balance;max-width:22ch}

.toc{float:right;width:206px;margin:0 0 22px 30px;padding:13px 15px;background:var(--surface);
 border:1px solid var(--rule-soft);border-radius:9px}
.toc-h{font-family:"IBM Plex Mono",monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;
 color:var(--ink-3);margin-bottom:7px}
.toc ul{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:4px}
.toc a{color:var(--ink-2);font-size:12.5px;line-height:1.4;display:block}
.toc a:hover{color:var(--accent);text-decoration:none}

.prose{max-width:74ch}
.prose h2{font-family:"IBM Plex Serif",Georgia,serif;font-weight:600;font-size:23px;line-height:1.28;
 letter-spacing:-.012em;margin:44px 0 14px;padding-top:18px;border-top:1px solid var(--rule-soft);text-wrap:balance}
.prose h2:first-child{border-top:0;padding-top:0;margin-top:0}
.prose h3{font-family:"IBM Plex Serif",Georgia,serif;font-weight:600;font-size:17.5px;margin:30px 0 10px;text-wrap:balance}
.prose h4{font-family:"IBM Plex Mono",monospace;font-size:12px;letter-spacing:.08em;text-transform:uppercase;
 color:var(--ink-2);margin:24px 0 8px}
.prose p{margin:0 0 15px}
.prose ul,.prose ol{margin:0 0 16px;padding-left:22px;display:flex;flex-direction:column;gap:5px}
.prose li>ul,.prose li>ol{margin:6px 0 0}
.prose li::marker{color:var(--ink-3)}
.prose hr{border:0;border-top:1px solid var(--rule);margin:34px 0}
.prose strong{font-weight:600;color:var(--ink)}
.prose code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:.875em;background:var(--code-bg);
 border:1px solid var(--code-rule);border-radius:4px;padding:1px 4px;color:var(--code-ink)}
.prose a code{color:var(--teal)}
.deadlink{color:var(--ink-3);border-bottom:1px dotted var(--rule)}

.prose blockquote{margin:20px 0;padding:14px 18px;background:var(--surface);border:1px solid var(--rule-soft);
 border-left:3px solid var(--accent);border-radius:0 8px 8px 0}
.prose blockquote p:last-child{margin-bottom:0}

.codewrap{position:relative;margin:0 0 18px;background:var(--code-bg);border:1px solid var(--code-rule);
 border-radius:9px;overflow-x:auto}
.codewrap pre{margin:0;padding:15px 17px;min-width:min-content}
.codewrap code{font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12.9px;line-height:1.62;
 background:none;border:0;padding:0;color:var(--code-ink);white-space:pre}
.codewrap[data-lang]::after{content:attr(data-lang);position:absolute;top:0;right:0;
 font-family:"IBM Plex Mono",monospace;font-size:9.5px;letter-spacing:.11em;text-transform:uppercase;
 color:var(--ink-3);padding:5px 10px;pointer-events:none}

.tablewrap{overflow-x:auto;margin:0 0 20px;border:1px solid var(--rule);border-radius:9px;background:var(--surface)}
table{border-collapse:collapse;width:100%;font-size:13.8px}
th,td{padding:9px 13px;text-align:left;vertical-align:top;border-bottom:1px solid var(--rule-soft)}
th{font-family:"IBM Plex Mono",monospace;font-size:10.5px;letter-spacing:.09em;text-transform:uppercase;
 color:var(--ink-3);font-weight:500;background:var(--surface-2);white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:var(--surface-2)}
td code{font-size:.86em}

.empty{padding:40px;color:var(--ink-3);font-size:14px}
table.meta{font-size:13.4px}
table.meta td:first-child{width:1%;white-space:nowrap;color:var(--ink-3);
 font-family:"IBM Plex Mono",monospace;font-size:11px;letter-spacing:.05em;text-transform:uppercase;
 padding-right:22px;background:var(--surface-2)}
table.meta td:first-child strong{font-weight:500;color:var(--ink-3)}

@media (max-width:940px){
  .shell{grid-template-columns:1fr}
  .rail{position:fixed;inset:0 auto 0 0;width:298px;z-index:20;transform:translateX(-100%);
   transition:transform .22s ease;box-shadow:var(--shadow)}
  .rail.open{transform:none}
  .menu{display:inline-block}
  .scrim{position:fixed;inset:0;background:rgba(8,14,13,.5);z-index:15;opacity:0;pointer-events:none;transition:opacity .2s}
  .scrim.on{opacity:1;pointer-events:auto}
  .topbar,.doc{padding-left:20px;padding-right:20px}
  .toc{float:none;width:auto;margin:0 0 24px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

JS = r"""
(function(){
  var D=%%DATA%%;
  var rail=document.getElementById('rail'), scrim=document.getElementById('scrim');
  var items=[].slice.call(document.querySelectorAll('.navitem'));
  var arts=[].slice.call(document.querySelectorAll('.doc'));
  var crumb=document.getElementById('crumb');
  var search=document.getElementById('search');

  function store(k,v){try{localStorage.setItem(k,v)}catch(e){}}
  function load(k){try{return localStorage.getItem(k)}catch(e){return null}}

  function show(sid, anchor){
    var found=false;
    arts.forEach(function(a){ var on=a.id===sid; a.hidden=!on; if(on) found=true; });
    if(!found){ arts[0].hidden=false; sid=arts[0].id; }
    items.forEach(function(n){ n.classList.toggle('on', n.dataset.sid===sid); });
    var act=items.filter(function(n){return n.dataset.sid===sid})[0];
    if(act){ crumb.textContent=act.querySelector('.nav-t').textContent; }
    store('gz.sid', sid);
    if(anchor){
      var el=document.getElementById(sid+'--'+anchor);
      if(el){ el.scrollIntoView({block:'start'}); return; }
    }
    window.scrollTo(0,0);
  }

  function go(target, push){
    var sid=target, anchor='';
    var k=target.indexOf('--');
    if(k>0){ sid=target.slice(0,k); anchor=target.slice(k+2); }
    if(!document.getElementById(sid)){
      var el=document.getElementById(target);
      if(el){ var par=el.closest('.doc'); if(par){ sid=par.id; anchor=target.replace(sid+'--',''); } }
    }
    show(sid, anchor);
    if(push!==false){
      try{ history.replaceState(null,'','#'+target); }catch(e){ }
    }
    close();
  }

  // bắt MỌI liên kết trong trang, không phụ thuộc hashchange
  document.addEventListener('click', function(e){
    var a=e.target.closest('a[href^="#"]');
    if(!a) return;
    e.preventDefault();
    go(decodeURIComponent(a.getAttribute('href').slice(1)));
  });

  function route(){
    var h='';
    try{ h=decodeURIComponent(location.hash.slice(1)); }catch(e){ }
    go(h || load('gz.sid') || 'overview', false);
  }
  window.addEventListener('hashchange', route);

  // lọc
  var mode='all';
  function apply(){
    var q=(search.value||'').trim().toLowerCase();
    items.forEach(function(n){
      var okQ=!q || n.dataset.hay.indexOf(q)>-1;
      var d=n.dataset.deleg, okM;
      if(mode==='all') okM=true;
      else if(!d) okM=false;
      else okM=(mode==='y' ? d==='\u2705' : d==='\u274C');
      n.parentNode.style.display=(okQ&&okM)?'':'none';
    });
    document.querySelectorAll('.navgroup').forEach(function(g){
      var vis=[].slice.call(g.querySelectorAll('.navlist>li')).some(function(li){return li.style.display!=='none'});
      g.style.display=vis?'':'none';
    });
  }
  search.addEventListener('input', apply);
  document.querySelectorAll('.fbtn').forEach(function(b){
    b.addEventListener('click', function(){
      mode=b.dataset.mode;
      document.querySelectorAll('.fbtn').forEach(function(x){x.setAttribute('aria-pressed', String(x===b))});
      apply();
    });
  });

  function close(){ rail.classList.remove('open'); scrim.classList.remove('on'); }
  document.getElementById('menu').addEventListener('click', function(){
    rail.classList.toggle('open'); scrim.classList.toggle('on');
  });
  scrim.addEventListener('click', close);

  var tbtn=document.getElementById('theme');
  function curTheme(){
    var s=document.documentElement.getAttribute('data-theme');
    if(s) return s;
    return matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';
  }
  tbtn.addEventListener('click', function(){
    var next=curTheme()==='dark'?'light':'dark';
    document.documentElement.setAttribute('data-theme', next);
    store('gz.theme', next);
    tbtn.textContent = next==='dark'?'◑ Sáng':'◐ Tối';
  });
  var saved=load('gz.theme');
  if(saved){ document.documentElement.setAttribute('data-theme', saved); }
  tbtn.textContent = curTheme()==='dark'?'◑ Sáng':'◐ Tối';

  document.addEventListener('keydown', function(e){
    if(e.key==='/' && document.activeElement!==search){ e.preventDefault(); search.focus(); }
    if(e.key==='Escape'){ search.blur(); close(); }
  });

  var done=D.tasks.filter(function(t){return t.done}).length;
  var total=D.tasks.length+11;   // +11 phiếu X/R chưa viết
  document.getElementById('meter-n').textContent=done+' / '+total;
  document.getElementById('meter-fill').style.width=(100*done/total)+'%';

  route();
})();
"""
JS = JS.replace("%%DATA%%", DATA)

PAGE = f"""<title>Genesis Zero</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&display=swap&subset=latin,latin-ext,vietnamese">
<style>{CSS}</style>

<div class="shell">
  <aside class="rail" id="rail">
    <div class="brand">
      <p class="brand-t">Genesis Zero</p>
      <div class="brand-s">Thế giới luật ẩn · v5</div>
      <div class="meter">
        <div class="meter-bar"><div class="meter-fill" id="meter-fill"></div></div>
        <span class="meter-n" id="meter-n">0 / 61</span>
      </div>
    </div>
    <div class="tools">
      <input class="search" id="search" type="search" placeholder="Tìm việc hoặc tài liệu   /" aria-label="Tìm">
      <div class="filters" role="group" aria-label="Lọc theo khả năng giao việc">
        <button class="fbtn" data-mode="all" aria-pressed="true">Tất cả</button>
        <button class="fbtn" data-mode="y" aria-pressed="false">✅ Giao được</button>
        <button class="fbtn" data-mode="n" aria-pressed="false">❌ Tự viết</button>
      </div>
    </div>
    <nav class="nav" aria-label="Mục lục">{''.join(nav)}</nav>
  </aside>

  <div class="main">
    <div class="topbar">
      <button class="iconbtn menu" id="menu" aria-label="Mở mục lục">☰</button>
      <span class="crumb" id="crumb">Tổng quan</span>
      <span class="topbar-sp"></span>
      <button class="iconbtn" id="theme">◐ Tối</button>
    </div>
    {''.join(arts)}
  </div>
</div>
<div class="scrim" id="scrim"></div>
<script>{JS}</script>
"""

out = DOCS / "site.html"
out.write_text(PAGE, encoding="utf-8")
print(f"{out} — {len(PAGE):,} bytes · {len(sections)} mục · {len(task_meta)} phiếu việc")
