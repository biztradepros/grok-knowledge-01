#!/usr/bin/env python3
"""REPORT.md -> one self-contained HTML file (fonts subset + screenshots inlined, no network).

usage: python3 export/build_report.py --fonts <dir with fontsource kr/ and mono/>
needs:  pip install markdown pymdown-extensions fonttools brotli
The PDF is printed from this HTML by export/render_pdf.js (Chromium), so both stay identical.
"""
import argparse, base64, html, io, re, subprocess
from pathlib import Path

import markdown
from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'export' / 'remote-kernel-v0.1-report.html'
SHOTS = [
    ('evidence-snapshot/f07-hold-explained.png', 'F07 DATA REFINERY — STEP → HOLD, EXPLAIN_HOLD가 누락 증거 source_manifest를 반환'),
    ('evidence-snapshot/f04-publish-rejected.png', 'F04 SOCIAL CARD — HANDOFF 이후 PUBLISH → COMMAND_REJECTED / HUMAN_GATE_REQUIRED, real_state_changed=false, side_effect_count=0'),
]
GRADES = {
    'NOT_VERIFIED': 'nv', 'HQ-REPORTED': 'nv', 'VERIFIED': 'ok', 'INFERRED': 'inf',
}

def commit_of(path):
    try:
        return subprocess.check_output(['git', 'log', '-1', '--format=%h', '--', str(path)], cwd=ROOT, text=True).strip()
    except Exception:
        return 'unknown'

def normalize_lists(md):
    """python-markdown needs a blank line before a list that follows a paragraph line."""
    out, fence, prev = [], False, ''
    for line in md.splitlines():
        if line.lstrip().startswith('```'):
            fence = not fence
        is_item = re.match(r'^(?:[-*]|\d+\.)\s', line)
        if not fence and is_item and prev.strip() and not re.match(r'^\s*(?:[-*]|\d+\.)\s', prev) and not prev.startswith('|'):
            out.append('')
        out.append(line)
        prev = line
    return '\n'.join(out)

def badge_grades(fragment):
    """Turn evidence-grade words into badges, but never inside tags, <code> or <pre>."""
    parts = re.split(r'(<pre>.*?</pre>|<code>.*?</code>|<[^>]+>)', fragment, flags=re.S)
    word = re.compile(r'\b(NOT_VERIFIED|HQ-REPORTED|VERIFIED|INFERRED)\b')
    for i, p in enumerate(parts):
        if p and not p.startswith('<'):
            parts[i] = word.sub(lambda m: f'<span class="grade grade-{GRADES[m.group(1)]}">{m.group(1)}</span>', p)
    return ''.join(parts)

def parse_fontsource(css_path):
    blocks = re.findall(r"url\(\./files/([^)]+\.woff2)\).*?unicode-range:\s*([^;]+);", css_path.read_text(), re.S)
    faces = []
    for fname, ranges in blocks:
        cps = []
        for r in ranges.split(','):
            r = r.strip()[2:]
            a, _, b = r.partition('-')
            cps.append((int(a, 16), int(b or a, 16)))
        faces.append((fname, cps))
    return faces

def subset_face(woff2_path, chars):
    font = TTFont(woff2_path)
    cmap = font.getBestCmap()
    keep = [c for c in chars if c in cmap]
    if not keep:
        return None
    opts = subset.Options()
    opts.flavor = 'woff2'
    opts.layout_features = ['*']
    opts.name_IDs = ['*']
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=keep)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = 'woff2'
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()

def font_faces(fonts_dir, text):
    chars = sorted({ord(c) for c in text} | set(range(0x20, 0x7f)))
    css = []
    for family, pkg, prefix, weights in [
        ('Noto Sans KR', 'kr', '', (400, 700)),
        ('JetBrains Mono', 'mono', '', (400, 700)),
    ]:
        for w in weights:
            for fname, ranges in parse_fontsource(fonts_dir / pkg / f'{w}.css'):
                if pkg == 'mono' and 'latin' not in fname:
                    continue
                if pkg == 'mono' and 'latin-ext' in fname:
                    continue
                wanted = [c for c in chars if any(a <= c <= b for a, b in ranges)]
                if not wanted:
                    continue
                data = subset_face(fonts_dir / pkg / 'files' / fname, wanted)
                if data:
                    css.append(f"@font-face{{font-family:'{family}';font-weight:{w};font-style:normal;font-display:block;"
                               f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")
    return '\n'.join(css)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fonts', required=True, type=Path)
    args = ap.parse_args()

    src = (ROOT / 'REPORT.md').read_text()
    lines = src.splitlines()
    title = lines[0].lstrip('# ').strip()
    meta_author = lines[2].strip()
    meta_scope = lines[3].replace('범위:', '').strip()
    body_md = normalize_lists('\n'.join(lines[4:]))

    md = markdown.Markdown(extensions=['tables', 'toc', 'pymdownx.superfences', 'sane_lists'],
                           extension_configs={'toc': {'toc_depth': '2-2', 'permalink': False}})
    body = md.convert(body_md)
    toc = md.toc_tokens
    body = re.sub(r'<table>', '<div class="table-wrap"><table>', body).replace('</table>', '</table></div>')
    body = re.sub(r'<hr\s*/?>', '', body)
    body = badge_grades(body)

    shots = ''.join(
        f'<figure><img alt="{html.escape(cap)}" src="data:image/png;base64,{base64.b64encode((ROOT / p).read_bytes()).decode()}">'
        f'<figcaption>{html.escape(cap)}</figcaption></figure>' for p, cap in SHOTS)
    toc_html = ''.join(f'<li><a href="#{t["id"]}">{html.escape(t["name"])}</a></li>' for t in toc)

    commit = commit_of(ROOT / 'REPORT.md')
    author_bits = [b.strip() for b in meta_author.replace('작성:', '').split('·')]
    doc = TEMPLATE.format(
        title=html.escape(title),
        eyebrow='DREAM FACTORIES · REMOTE SYSTEM ADVANCED R&amp;D',
        author=html.escape(author_bits[0]), date=html.escape(author_bits[1] if len(author_bits) > 1 else ''),
        branch=html.escape(re.sub(r'.*`([^`]+)`.*', r'\1', meta_author)),
        commit=html.escape(commit), scope=html.escape(meta_scope),
        toc=toc_html, body=body, shots=shots, fonts='{fonts}',
    )
    visible = re.sub(r'<[^>]+>', '', doc)
    doc = doc.replace('{fonts}', font_faces(args.fonts, html.unescape(visible)))
    OUT.write_text(doc)
    print(f'{OUT.relative_to(ROOT)}  {len(doc) / 1024:.0f} KiB  commit={commit}')

TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; font-src data:">
<title>Remote Kernel v0.1 보고서</title>
<style>
{fonts}
:root {{
  --bg:#fbfaf7; --surface:#f1efe9; --fg:#1c1b19; --muted:#6a675f; --line:#dcd8cf; --accent:#1f4e79;
  --ok:#1d6b3a; --ok-bg:#e3f1e7; --nv:#8a3b12; --nv-bg:#fbe9dc; --inf:#3d4f6b; --inf-bg:#e6ebf3;
  --sans:'Noto Sans KR','Apple SD Gothic Neo','Malgun Gothic',system-ui,sans-serif;
  --mono:'JetBrains Mono','Noto Sans KR',ui-monospace,Menlo,Consolas,monospace;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --bg:#151513; --surface:#1f1f1c; --fg:#ebe9e3; --muted:#a19d93; --line:#34332e; --accent:#8cb8e6;
    --ok:#7fd29a; --ok-bg:#1b3324; --nv:#f0a57a; --nv-bg:#3a2317; --inf:#a9bbd8; --inf-bg:#222b3a;
  }}
}}
:root[data-theme="dark"] {{
  --bg:#151513; --surface:#1f1f1c; --fg:#ebe9e3; --muted:#a19d93; --line:#34332e; --accent:#8cb8e6;
  --ok:#7fd29a; --ok-bg:#1b3324; --nv:#f0a57a; --nv-bg:#3a2317; --inf:#a9bbd8; --inf-bg:#222b3a;
}}
* {{ box-sizing:border-box; }}
html {{ -webkit-text-size-adjust:100%; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.72 var(--sans); word-break:keep-all; overflow-wrap:anywhere; }}
main {{ max-width:880px; margin:0 auto; padding:48px 16px 80px; }}
.eyebrow {{ font-size:12px; letter-spacing:.12em; color:var(--muted); font-weight:700; }}
h1 {{ font-size:30px; line-height:1.3; margin:10px 0 18px; letter-spacing:-.01em; }}
.meta {{ display:grid; grid-template-columns:max-content 1fr; gap:4px 16px; font-size:13.5px; margin:0 0 24px;
        padding:14px 16px; border:1px solid var(--line); border-radius:10px; background:var(--surface); }}
.meta dt {{ color:var(--muted); }} .meta dd {{ margin:0; }}
nav.toc {{ margin:0 0 36px; }}
nav.toc h2 {{ border:0; padding:0; margin:0 0 8px; font-size:13px; letter-spacing:.08em; color:var(--muted); }}
nav.toc ol {{ margin:0; padding-left:0; list-style:none; columns:2 280px; column-gap:28px; font-size:14px; }}
nav.toc li {{ break-inside:avoid; padding:2px 0; }}
nav.toc a {{ color:var(--fg); text-decoration:none; border-bottom:1px solid var(--line); }}
h2 {{ font-size:21px; line-height:1.4; margin:52px 0 14px; padding-top:22px; border-top:2px solid var(--fg); scroll-margin-top:16px; }}
h3 {{ font-size:17px; margin:28px 0 8px; }}
p {{ margin:0 0 12px; }}
a {{ color:var(--accent); }}
strong {{ font-weight:700; }}
ul, ol {{ padding-left:22px; margin:0 0 14px; }} li {{ margin:3px 0; }}
code {{ font-family:var(--mono); font-size:.86em; background:var(--surface); border:1px solid var(--line); border-radius:4px; padding:0 4px; }}
pre {{ font-family:var(--mono); font-size:12.5px; line-height:1.6; background:var(--surface); border:1px solid var(--line);
      border-radius:8px; padding:14px 16px; overflow-x:auto; margin:0 0 16px; }}
pre code {{ background:none; border:0; padding:0; font-size:inherit; }}
.table-wrap {{ overflow-x:auto; margin:0 0 18px; border:1px solid var(--line); border-radius:8px; }}
table {{ border-collapse:collapse; width:100%; font-size:13.5px; line-height:1.55; }}
th, td {{ text-align:left; vertical-align:top; padding:8px 10px; border-bottom:1px solid var(--line); }}
th {{ background:var(--surface); font-weight:700; white-space:nowrap; }}
td:first-child {{ overflow-wrap:normal; }}
tr:last-child td {{ border-bottom:0; }}
.grade {{ display:inline-block; font:700 11.5px/1.5 var(--mono); letter-spacing:.02em; padding:0 6px; border-radius:4px; white-space:nowrap; }}
.grade-ok {{ color:var(--ok); background:var(--ok-bg); }}
.grade-nv {{ color:var(--nv); background:var(--nv-bg); }}
.grade-inf {{ color:var(--inf); background:var(--inf-bg); }}
figure {{ margin:0 0 24px; }}
figure img {{ width:100%; height:auto; border:1px solid var(--line); border-radius:8px; display:block; background:#fff; }}
figcaption {{ font-size:13px; color:var(--muted); margin-top:6px; }}
footer {{ margin-top:48px; padding-top:14px; border-top:1px solid var(--line); font-size:12.5px; color:var(--muted); }}
@media (max-width:600px) {{ main {{ padding-top:28px; }} h1 {{ font-size:24px; }} body {{ font-size:14.5px; }} th, td {{ min-width:7.5em; }} }}
@page {{ size:A4; margin:16mm 14mm 18mm; }}
@media print {{
  :root, :root[data-theme="dark"] {{ --bg:#fff; --surface:#f4f3ef; --fg:#1c1b19; --muted:#5f5c55; --line:#d6d2c8; --accent:#1f4e79;
    --ok:#1d6b3a; --ok-bg:#e3f1e7; --nv:#8a3b12; --nv-bg:#fbe9dc; --inf:#3d4f6b; --inf-bg:#e6ebf3; }}
  body {{ font-size:10.5pt; -webkit-print-color-adjust:exact; print-color-adjust:exact; }}
  main {{ max-width:none; padding:0; }}
  h1 {{ font-size:22pt; }}
  h2 {{ font-size:15pt; margin-top:22pt; break-after:avoid; }}
  h2#appendix {{ break-before:page; }}
  h3 {{ break-after:avoid; }}
  pre {{ white-space:pre-wrap; overflow:visible; break-inside:avoid; font-size:8.6pt; }}
  .table-wrap {{ overflow:visible; }}
  tr, figure {{ break-inside:avoid; }}
  nav.toc a {{ border:0; }}
  a {{ color:inherit; text-decoration:none; }}
}}
</style>
</head>
<body>
<main>
  <div class="eyebrow">{eyebrow}</div>
  <h1>{title}</h1>
  <dl class="meta">
    <dt>작성</dt><dd>{author}</dd>
    <dt>날짜</dt><dd>{date}</dd>
    <dt>브랜치</dt><dd><code>{branch}</code> · 보고서 커밋 <code>{commit}</code></dd>
    <dt>범위</dt><dd>{scope}</dd>
  </dl>
  <nav class="toc" aria-label="목차"><h2>목차</h2><ol>{toc}<li><a href="#appendix">부록 · 브라우저 증거 스크린샷</a></li></ol></nav>
  {body}
  <h2 id="appendix">부록 · 브라우저 증거 스크린샷</h2>
  <p>이 세션의 Playwright Chromium 실행에서 저장한 화면이다. 대상은 fixture Site이며 실제 Factory가 아니다.</p>
  {shots}
  <footer>원본: <code>research/remote-kernel-v0.1/REPORT.md</code> · 이 파일은 네트워크 없이 열린다(글꼴·이미지 내장).</footer>
</main>
</body>
</html>
"""

if __name__ == '__main__':
    main()
