#!/usr/bin/env python3
"""Build the post from post.md + template.html + algorithms/ + figures/.

    python3 build.py            build once  -> out/index.html, out/votor-diff.html
    python3 build.py --watch    rebuild whenever a source file changes
    python3 build.py --serve    watch + serve out/ on http://localhost:8641

post.md syntax (plain Markdown plus two directives):

    @figure step1: caption text          a figure from figures/step1.html, numbered in order
    ... see @fig(step1) ...              inline cross-reference -> "Figure 1"

Headings: `# ...` is a section heading (in the sidebar TOC), `## ...` a subsection.
Raw HTML lines pass through untouched. Anything under static/ is copied to out/static/. Algorithm listings live in algorithms/<id>.txt
and are referenced by data-alg="<id>" inside the figure snippets.
"""
import html, os, re, sys, time, threading, functools, http.server, socketserver, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
P = lambda *a: os.path.join(ROOT, *a)

# ----------------------------------------------------------------------------- markdown
def slug(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'[^\w\s-]', '', s.lower()).strip()
    return re.sub(r'[\s_]+', '-', s) or 'section'

def inline(s, fignum):
    codes = []
    def stash(m):
        codes.append('<code>' + html.escape(m.group(1)) + '</code>')
        return '\x00%d\x00' % (len(codes) - 1)
    s = re.sub(r'`([^`]+)`', stash, s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])', r'<em>\1</em>', s)
    s = re.sub(r'(?<![\w_])_(?!\s)(.+?)(?<!\s)_(?![\w_])', r'<em>\1</em>', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)\s]+)\)', r'<a href="\2">\1</a>', s)
    s = re.sub(r'@fig\(([\w-]+)\)', lambda m: 'Figure %s' % fignum.get(m.group(1), '?'), s)
    s = s.replace(' -- ', ' — ')
    return re.sub(r'\x00(\d+)\x00', lambda m: codes[int(m.group(1))], s)

def parse_front(lines):
    meta = {}
    if lines and lines[0].strip() == '---':
        i = 1
        while i < len(lines) and lines[i].strip() != '---':
            if ':' in lines[i]:
                k, v = lines[i].split(':', 1); meta[k.strip()] = v.strip()
            i += 1
        return meta, lines[i + 1:]
    return meta, lines

def render(md):
    lines = md.split('\n')
    meta, lines = parse_front(lines)

    # first pass: figure numbers
    fignum, n = {}, 0
    for ln in lines:
        m = re.match(r'@figure\s+([\w-]+)', ln)
        if m: n += 1; fignum[m.group(1)] = n

    out, para, lst, code = [], [], None, None
    def flush_para():
        if para:
            out.append('<p>' + inline(' '.join(x.strip() for x in para), fignum) + '</p>'); para.clear()
    def flush_list():
        nonlocal lst
        if lst:
            tag, items = lst
            out.append('<%s>%s</%s>' % (tag, ''.join('<li>' + inline(i, fignum) + '</li>' for i in items), tag)); lst = None

    for ln in lines:
        if code is not None:
            if ln.strip().startswith('```'):
                out.append('<pre><code>' + html.escape('\n'.join(code)) + '</code></pre>'); code = None
            else: code.append(ln)
            continue
        s = ln.strip()
        if not s:
            flush_para(); flush_list(); continue
        if s.startswith('```'):
            flush_para(); flush_list(); code = []; continue
        m = re.match(r'(#{1,3})\s+(.*)', s)
        if m:
            flush_para(); flush_list()
            lvl, txt = len(m.group(1)), inline(m.group(2), fignum)
            if lvl == 1: out.append('<h1 id="%s" class="section-heading">%s</h1>' % (slug(txt), txt))
            else: out.append('<h%d id="%s">%s</h%d>' % (lvl, slug(txt), txt, lvl))
            continue
        m = re.match(r'@figure\s+([\w-]+)\s*:?\s*(.*)', s)
        if m:
            flush_para(); flush_list()
            fid, cap = m.group(1), inline(m.group(2), fignum)
            path = P('figures', fid + '.html')
            if not os.path.exists(path):
                out.append('<p style="color:#b3261e">[missing figure: %s]</p>' % fid); continue
            body = open(path).read().strip()
            out.append('<figure class="figure wide">\n  <div class="figure-content">%s</div>\n'
                       '  <figcaption class="figure-caption"><span class="figure-number">Figure %d:</span> %s</figcaption>\n</figure>'
                       % (body, fignum[fid], cap))
            continue
        m = re.match(r'([-*]|\d+\.)\s+(.*)', s)
        if m:
            flush_para()
            tag = 'ul' if m.group(1) in '-*' else 'ol'
            if lst is None or lst[0] != tag: flush_list(); lst = (tag, [])
            lst[1].append(m.group(2)); continue
        if lst is not None and ln.startswith(('  ', '\t')):
            lst[1][-1] += ' ' + s; continue
        if s.startswith('>'):
            flush_para(); flush_list(); out.append('<blockquote><p>' + inline(s[1:].strip(), fignum) + '</p></blockquote>'); continue
        if s.startswith('<') and not s.startswith('<code') and not s.startswith('<mark') and not s.startswith('<a ') and not s.startswith('<em') and not s.startswith('<strong'):
            flush_para(); flush_list(); out.append(ln); continue
        flush_list(); para.append(ln)
    flush_para(); flush_list()
    return meta, '\n'.join(out)

# ----------------------------------------------------------------------------- assembly
def header(meta):
    h = ['<header class="title-header-wrapper">',
         '  <h1 class="article-title">%s</h1>' % meta.get('title', '')]
    if meta.get('subtitle'): h.append('  <p class="article-subtitle">%s</p>' % meta['subtitle'])
    h += ['  <div class="byline-dateline-container">',
          '    <p class="byline">By <a href="%s">%s</a></p>' % (meta.get('author_url', '#'), meta.get('author', '')),
          '    <p class="dateline">%s</p>' % meta.get('date', ''),
          '  </div>', '</header>']
    return '\n'.join(h)

def algorithms():
    parts = ['<!-- ============ algorithm sources ============ -->']
    for f in sorted(os.listdir(P('algorithms'))):
        if f.endswith('.txt'):
            parts.append('<script type="text/plain" data-src="%s">\n%s</script>\n' % (f[:-4], open(P('algorithms', f)).read()))
    return '\n'.join(parts)

def build():
    meta, body = render(open(P('post.md')).read())
    tpl = open(P('template.html')).read()
    tpl = re.sub(r'<title>.*?</title>', '<title>%s</title>' % html.escape(meta.get('title', '')), tpl, count=1)
    page = tpl.replace('{{CONTENT}}', header(meta) + '\n\n' + body).replace('{{ALGORITHMS}}', algorithms())
    os.makedirs(P('out'), exist_ok=True)
    if os.path.isdir(P('static')): shutil.copytree(P('static'), P('out', 'static'), dirs_exist_ok=True)  # images etc.
    open(P('out', 'votor-diff.html'), 'w').write(page)                         # artifact source
    open(P('out', 'index.html'), 'w').write('<!doctype html>\n<meta charset="utf-8">\n' + page)  # local preview
    return page

def sources():
    fs = [P('post.md'), P('template.html'), P('build.py')]
    for d in ('algorithms', 'figures'):
        fs += [P(d, f) for f in os.listdir(P(d))]
    for root, _, files in os.walk(P('static')):
        fs += [os.path.join(root, f) for f in files]
    return {f: os.stat(f).st_mtime for f in fs if os.path.exists(f)}

def watch():
    last = sources()
    while True:
        time.sleep(0.5)
        cur = sources()
        if cur != last:
            last = cur
            try: build(); print(time.strftime('%H:%M:%S'), 'rebuilt')
            except Exception as e: print(time.strftime('%H:%M:%S'), 'ERROR', e)

def serve(port):
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def end_headers(self):
            self.send_header('Cache-Control', 'no-store'); super().end_headers()
    H = functools.partial(Q, directory=P('out'))
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(('127.0.0.1', port), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print('serving http://localhost:%d/  (ctrl-c to stop)' % port)

if __name__ == '__main__':
    build(); print('built out/index.html')
    if '--serve' in sys.argv:
        port = next((int(a) for a in sys.argv if a.isdigit()), 8641)
        serve(port); watch()
    elif '--watch' in sys.argv:
        watch()
