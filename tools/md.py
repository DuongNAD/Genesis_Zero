"""Markdown -> HTML tối giản, đủ cho bộ tài liệu Genesis Zero."""
import html
import re


def slug(text):
    t = re.sub(r'<[^>]+>', '', text)
    t = t.replace('·', ' ').replace('★', ' ').replace('✦', ' ')
    t = t.lower()
    t = ''.join(c for c in t if c.isalnum() or c in ' -_')
    t = re.sub(r'\s+', '-', t.strip())
    return re.sub(r'-+', '-', t).strip('-')

CODE_TOK = '\x00CODE%d\x00'

def inline(s, linkfn):
    codes = []
    def stash(m):
        codes.append(m.group(1))
        return CODE_TOK % (len(codes) - 1)
    s = re.sub(r'`([^`]+)`', stash, s)
    s = html.escape(s, quote=False)
    # links
    def link(m):
        txt, href = m.group(1), m.group(2)
        h, cls, extra = linkfn(href)
        if h is None:
            return f'<span class="deadlink">{txt}</span>'
        return f'<a href="{html.escape(h,quote=True)}"{cls}{extra}>{txt}</a>'
    s = re.sub(r'\[([^\]]*?)\]\(([^)\s]+)\)', link, s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+?)\*(?![\w*])', r'<em>\1</em>', s)
    for i, c in enumerate(codes):
        s = s.replace(CODE_TOK % i, f'<code>{html.escape(c, quote=False)}</code>')
    return s

def render(md, linkfn, idprefix=''):
    lines = md.split('\n')
    out, i, n = [], 0, len(lines)
    heads = []

    def flush_para(buf):
        if buf:
            out.append('<p>' + inline(' '.join(buf).strip(), linkfn) + '</p>')
        return []

    def parse_list(start, base_indent):
        """Trả (html, chỉ số dòng kế tiếp)."""
        j = start
        ordered = bool(re.match(r'^\s*\d+\.\s', lines[j]))
        items, cur, cur_sub = [], None, []
        while j < n:
            L = lines[j]
            if not L.strip():
                # dòng trống: chỉ tiếp tục nếu dòng sau vẫn thuộc danh sách
                k = j + 1
                mk = re.match(r'^(\s*)(?:([-*])|(\d+)\.)\s' % (), lines[k]) if k < n else None
                if mk and len(mk.group(1)) >= base_indent and bool(mk.group(3)) == ordered:
                    j += 1; continue
                break
            m = re.match(r'^(\s*)(?:([-*])|(\d+)\.)\s+(.*)$', L)
            if m:
                ind = len(m.group(1))
                if ind < base_indent:
                    break
                if ind > base_indent:
                    sub, j = parse_list(j, ind)
                    cur_sub.append(sub)
                    continue
                if cur is not None:
                    items.append((cur, cur_sub))
                cur, cur_sub = m.group(4), []
                j += 1
            else:
                ind = len(L) - len(L.lstrip())
                if ind >= base_indent + 2 and cur is not None:
                    cur += ' ' + L.strip(); j += 1
                else:
                    break
        if cur is not None:
            items.append((cur, cur_sub))
        tag = 'ol' if ordered else 'ul'
        body = ''.join(f'<li>{inline(t, linkfn)}{"".join(sub)}</li>' for t, sub in items)
        return f'<{tag}>{body}</{tag}>', j

    para = []
    while i < n:
        L = lines[i]

        if L.startswith('```'):
            para = flush_para(para)
            lang = L[3:].strip()
            j = i + 1; buf = []
            while j < n and not lines[j].startswith('```'):
                buf.append(lines[j]); j += 1
            code = html.escape('\n'.join(buf), quote=False)
            cls = f' data-lang="{html.escape(lang,quote=True)}"' if lang else ''
            out.append(f'<div class="codewrap"{cls}><pre><code>{code}</code></pre></div>')
            i = j + 1; continue

        if re.match(r'^\s*(-{3,}|\*{3,}|_{3,})\s*$', L):
            para = flush_para(para); out.append('<hr>'); i += 1; continue

        hm = re.match(r'^(#{1,6})\s+(.*)$', L)
        if hm:
            para = flush_para(para)
            lvl, txt = len(hm.group(1)), hm.group(2).strip()
            sid = f'{idprefix}--{slug(txt)}' if idprefix else slug(txt)
            inner = inline(txt, linkfn)
            out.append(f'<h{lvl} id="{html.escape(sid,quote=True)}">{inner}</h{lvl}>')
            if lvl in (2, 3):
                heads.append((lvl, sid, re.sub(r'<[^>]+>', '', inner)))
            i += 1; continue

        if L.startswith('>'):
            para = flush_para(para)
            buf = []
            while i < n and (lines[i].startswith('>') or
                             (lines[i].strip() and buf and not re.match(r'^(#{1,6}\s|```|\||\s*[-*]\s|\s*\d+\.\s)', lines[i]))):
                buf.append(re.sub(r'^>\s?', '', lines[i])); i += 1
            sub, _ = render('\n'.join(buf), linkfn)
            out.append(f'<blockquote>{sub}</blockquote>'); continue

        if L.lstrip().startswith('|') and i + 1 < n and re.match(r'^\s*\|[\s:|-]+\|\s*$', lines[i + 1]):
            para = flush_para(para)
            def cells(row):
                r = row.strip()
                r = r.removeprefix('|')
                r = r.removesuffix('|')
                return [c.strip() for c in r.split('|')]
            head = cells(L)
            aligns = []
            for c in cells(lines[i + 1]):
                a = 'left'
                if c.startswith(':') and c.endswith(':'):
                    a = 'center'
                elif c.endswith(':'):
                    a = 'right'
                aligns.append(a)
            j = i + 2; rows = []
            while j < n and lines[j].lstrip().startswith('|'):
                rows.append(cells(lines[j])); j += 1
            def td(tag, cs, col_aligns=aligns):
                o = []
                for k, c in enumerate(cs):
                    a = col_aligns[k] if k < len(col_aligns) else 'left'
                    st = f' style="text-align:{a}"' if a != 'left' else ''
                    o.append(f'<{tag}{st}>{inline(c, linkfn)}</{tag}>')
                return '<tr>' + ''.join(o) + '</tr>'

            bare = not any(c.strip() for c in head)
            cls = ' class="meta"' if bare else ''
            t = f'<div class="tablewrap"><table{cls}>'
            if not bare:
                t += '<thead>' + td('th', head) + '</thead>'
            t += '<tbody>' + ''.join(td('td', r) for r in rows) + '</tbody></table></div>'
            out.append(t); i = j; continue

        if re.match(r'^\s*(?:[-*]|\d+\.)\s+', L):
            para = flush_para(para)
            ind = len(L) - len(L.lstrip())
            lst, i = parse_list(i, ind)
            out.append(lst); continue

        if not L.strip():
            para = flush_para(para); i += 1; continue

        para.append(L.strip()); i += 1

    flush_para(para)
    return '\n'.join(out), heads
