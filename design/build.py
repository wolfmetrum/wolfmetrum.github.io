"""Build the static design mockups (home.html, song.html) from _data/songs.yml.

Throwaway prototype for the redesign; the real site will be Eleventy templates.
Run: python design/build.py
"""
import html
import os
import re

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
songs = yaml.safe_load(open(os.path.join(HERE, '..', '_data', 'songs.yml'), encoding='utf-8'))
e = lambda s: html.escape(str(s or '').replace('️', ''), quote=True)  # ©️ in the data renders as an emoji; drop the variation selector
key_disp = lambda k: (k or '').replace('b', '♭').replace('#', '♯')
thumb = lambda vid: f'https://i.ytimg.com/vi/{vid}/maxresdefault.jpg'

ICON = {
    'play': '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><polygon points="7 4 20 12 7 20 7 4"/></svg>',
    'download': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" x2="12" y1="15" y2="3"/></svg>',
    'search': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
}


def kind(s):
    t = s.get('tags', [])
    return '原創' if '狼的格律原創' in t else '傳統詩歌' if '傳統詩歌' in t else '現代詩歌'


def head(title):
    return f'''<!doctype html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="以琴聲獻上讚美。狼的格律收錄原創詩歌與教會鋼琴伴奏，皆附完整調性，原創曲目附樂譜。">
<link rel="icon" href="../assets/images/wolfmetrum-mark.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;500&family=Noto+Serif+TC:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="site.css">
<script>document.documentElement.classList.add('js');</script>
</head>
<body>
<a class="skip" href="#main">跳到主要內容</a>
<header class="nav"><div class="container nav__in">
  <a class="brand" href="home.html" aria-label="狼的格律 首頁"><img src="../assets/images/wolfmetrum-mark.svg" width="40" height="40" alt=""><span>狼的格律</span><small>讓未馴的靈魂，臣服於恩典的格律</small></a>
  <ul class="nav__links">
    <li><a href="home.html#catalog">曲目</a></li>
    <li class="hide-s"><a href="home.html#year">節期</a></li>
    <li class="hide-s"><a href="home.html#serve">服事需求</a></li>
    <li><a href="#" lang="en" hreflang="en">English</a></li>
  </ul>
</div></header>
'''


FOOT = '''<footer class="foot"><div class="container">
  <div class="foot__in">
    <div>
      <a class="brand" href="home.html" aria-label="狼的格律 首頁"><img src="../assets/images/wolfmetrum-mark.svg" width="40" height="40" alt=""><span>狼的格律</span></a>
      <blockquote>豺狼必與綿羊羔同居，豹子與山羊羔同臥，少壯獅子與牛犢並肥畜同群，小孩子要牽引牠們。<cite>以賽亞書 11:6</cite></blockquote>
    </div>
    <div><h2>網站</h2><ul><li><a href="home.html#catalog">曲目</a></li><li><a href="home.html#year">節期</a></li><li><a href="home.html#serve">服事需求</a></li><li><a href="#" lang="en">English</a></li></ul></div>
    <div><h2>聯絡</h2><ul><li><a href="https://www.youtube.com/@WolfMetrumRs">YouTube 頻道</a></li><li><a href="mailto:wolfmetrum@outlook.com">wolfmetrum@outlook.com</a></li><li><a href="#" data-todo="KO_FI_URL">Ko-fi 奉獻</a></li></ul></div>
  </div>
  <small>© 2026 狼的格律 Wolf Metrum　原創曲目與樂譜版權屬狼的格律所有。</small>
</div></footer>
'''

# ---------- home ----------
originals = {}
for s in songs:
    if kind(s) != '原創':
        continue
    base = s['title'].split('(')[0]
    w = originals.setdefault(base, {'title': base, 'en': s['title_en'].split(' (')[0], 'vid': s['youtube_id'], 'key': s.get('key'), 'versions': [], 'sheet': s.get('sheet_music')})
    w['versions'].append('鋼琴版' if '鋼琴' in s['title'] else '演唱版')

rail = '\n'.join(f'''    <li><a class="work" href="{'song.html' if w['title'] == '榮耀真光' else '#catalog'}">
      <span class="cover"><img src="{thumb(w['vid'])}" width="1280" height="720" alt="" loading="lazy"></span>
      <h3>{e(w['title'])}<span class="en" lang="en">{e(w['en'])}</span></h3>
      <span class="work__meta">{'、'.join(w['versions'])}{'，附樂譜' if w['sheet'] else ''}</span>
    </a></li>''' for w in originals.values())

YEAR = [('待降節', '聖誕前四個主日'), ('聖誕節', '12 月 25 日'), ('新年', '1 月 1 日'), ('棕枝主日', '復活節前一週'), ('受難節', '復活節前的週五'),
        ('復活節', '3 月至 4 月'), ('五旬節', '復活節後第 50 天'), ('母親節與父親節', '5 月與 8 月'), ('感恩節', '11 月第四個週四')]
year = '\n'.join(f'''    <li{' aria-current="date"' if n == '待降節' else ''}><a href="#catalog"><b>{n}</b><span>{d}</span>{'<span class="now">即將到來</span>' if n == '待降節' else ''}</a></li>''' for n, d in YEAR)
USES = ['敬拜讚美', '默想禱告', '聖餐', '洗禮', '奉獻', '差遣祝福', '婚禮', '追思安息', '安慰盼望']
uses = '\n'.join(f'    <li><a class="chip" href="#catalog">{u}</a></li>' for u in USES)

# one row per work: versions (演唱版／鋼琴版／降N／第二詞) share the title before their trailing parentheses
works = {}
for s_ in songs:
    base = re.sub(r'(\([^)]*\))+$', '', s_['title']).strip()
    w = works.setdefault(base, {'title': base, 'en': re.sub(r'( \([^)]*\))+$', '', s_['title_en']), 'items': []})
    w['items'].append(s_)
for w in works.values():
    w['keys'] = list(dict.fromkeys(i['key'] for i in w['items'] if i.get('key')))
    w['kind'] = kind(w['items'][0])
    w['note'] = w['items'][0].get('note')
rows = '\n'.join(f"""      <tr data-kind="{w['kind']}" data-keys="{e(' '.join(w['keys']))}" data-search="{e(' '.join(str(i.get(k) or '') for i in w['items'] for k in ('title', 'title_en', 'composer', 'lyricist', 'note', 'key')).lower())}">
        <td><a href="{'song.html' if w['title'] == '榮耀真光' else '#'}">{e(w['title'])}</a><span class="en"><span lang="en">{e(w['en'])}</span>{'　共 %d 個版本' % len(w['items']) if len(w['items']) > 1 else ''}</span></td>
        <td class="key">{e('、'.join(key_disp(k) for k in w['keys']))}</td><td>{e(w['note'])}</td><td>{w['kind']}</td>
      </tr>""" for w in works.values())
keys = sorted({s['key'] for s in songs if s.get('key')}, key=lambda k: ('CDEFGAB'.index(k[0]), 'b#'.find(k[1]) if len(k) > 1 and k[1] in 'b#' else 0.5, k.endswith('m')))
keyopts = '\n'.join(f'        <option value="{k}">{key_disp(k)}</option>' for k in keys)

latest = songs[0]
home = head('狼的格律 Wolf Metrum：原創詩歌與教會鋼琴伴奏') + f'''<main id="main">
<section class="hero"><div class="container">
  <div class="hero__top">
    <h1 class="motto">讓未馴的靈魂，臣服於恩典的格律</h1>
    <div class="hero__aside">
      <p class="lead">以琴聲獻上讚美，收錄原創詩歌與伴奏，每首皆附上完整調性。</p>
      <div class="hero__actions">
        <a class="btn" href="#latest">{ICON['play']}播放〈平安降臨〉</a>
        <a class="btn btn--quiet" href="#catalog">查看 {len(works)} 首曲目</a>
      </div>
    </div>
  </div>
  <div class="release" id="latest">
    <a class="cover" href="https://www.youtube.com/watch?v={latest['youtube_id']}" aria-label="在 YouTube 播放 平安降臨">
      <img src="{thumb(latest['youtube_id'])}" width="1280" height="720" alt="平安降臨 影片封面" fetchpriority="high">
      <span class="cover__play">{ICON['play']}</span>
    </a>
    <div>
      <h2>{e(latest['title'])}<span class="en" lang="en">{e(latest['title_en'])}</span></h2>
      <dl class="facts">
        <dt>調性</dt><dd class="key">{key_disp(latest['key'])} 大調</dd>
        <dt>詞曲</dt><dd>狼的格律</dd>
        <dt>節期</dt><dd>聖誕節</dd>
      </dl>
      <a class="link" href="../assets/sheets/平安降臨.pdf">下載樂譜 PDF</a>
    </div>
  </div>
</div></section>

<section class="sec sec--well" aria-labelledby="h-orig"><div class="container">
  <div class="sec__head"><h2 class="h2" id="h-orig">狼的格律的原創曲目</h2><p>皆包含演唱版，原創樂譜供下載。</p></div>
  <ul class="rail" tabindex="0" aria-label="原創作品">
{rail}
  </ul>
</div></section>

<section class="sec" id="year" aria-labelledby="h-year"><div class="container">
  <div class="sec__head"><h2 class="h2" id="h-year">依教會節期擇選詩歌</h2><p>自待降節至感恩節，為各節期預備合宜的詩歌。</p></div>
  <ol class="year">
{year}
  </ol>
  <ul class="uses" aria-label="聚會用途">
{uses}
  </ul>
</div></section>

<section class="sec sec--well" id="catalog" aria-labelledby="h-cat"><div class="container">
  <div class="sec__head"><h2 class="h2" id="h-cat">全部 {len(works)} 首詩歌，可依調性檢索</h2></div>
  <div class="tools">
    <div class="field">{ICON['search']}<label class="visually-hidden" for="q">搜尋曲目</label><input id="q" type="search" name="q" autocomplete="off" placeholder="曲名、作者，或「聖徒詩歌 95」"></div>
    <label class="visually-hidden" for="mode">大調或小調</label>
    <select id="mode" name="mode"><option value="">大調與小調</option><option value="major">大調</option><option value="minor">小調</option></select>
    <label class="visually-hidden" for="key">調性</label>
    <select id="key" name="key"><option value="">全部調性</option>
{keyopts}
    </select>
  </div>
  <fieldset class="types"><legend class="visually-hidden">類型</legend>
    <input type="radio" name="kind" id="k0" value="" checked><label for="k0">全部</label>
    <input type="radio" name="kind" id="k1" value="原創"><label for="k1">原創</label>
    <input type="radio" name="kind" id="k2" value="傳統詩歌"><label for="k2">傳統詩歌</label>
    <input type="radio" name="kind" id="k3" value="現代詩歌"><label for="k3">現代詩歌</label>
  </fieldset>
  <table class="index">
    <thead><tr><th scope="col">曲名</th><th scope="col">調性</th><th scope="col">出處</th><th scope="col">類型</th></tr></thead>
    <tbody>
{rows}
    </tbody>
  </table>
  <p class="empty" role="status" hidden>查無符合的曲目，請更換關鍵字或清除篩選。</p>
  <button class="btn btn--quiet more" type="button" hidden>顯示全部 {len(works)} 首</button>
</div></section>

<section class="sec" id="serve" aria-labelledby="h-serve"><div class="container">
  <div class="sec__head"><h2 class="h2" id="h-serve">為您的聚會預備伴奏</h2><p>為教會與團契錄製鋼琴伴奏，隨心奉獻。</p></div>
  <ol class="serve__grid">
    <li><h3 class="h3">新詩歌鋼琴伴奏</h3><p>提供曲名與出處，即為您錄製鋼琴伴奏。</p></li>
    <li><h3 class="h3">現有影片移調</h3><p>依會眾音域，重新錄製合宜的調性。</p></li>
    <li class="serve__act"><a class="btn btn--quiet" href="#" data-todo="GOOGLE_FORM_URL">填寫需求表單</a><a class="link" href="#" data-todo="KO_FI_URL">在 Ko-fi 奉獻</a><p class="terms">僅供教會及非營利用途，收到後將以 Email 回覆。</p></li>
  </ol>
</div></section>
</main>
''' + FOOT + '''<script>
(() => {
  const q = document.getElementById('q'), mode = document.getElementById('mode'), key = document.getElementById('key');
  const rows = [...document.querySelectorAll('.index tbody tr')], more = document.querySelector('.more'), empty = document.querySelector('.empty');
  let expanded = false;
  const apply = () => {
    const t = q.value.trim().toLowerCase(), k = key.value, m = mode.value, kd = document.querySelector('input[name=kind]:checked').value;
    const filtering = t || k || m || kd;
    let shown = 0;
    rows.forEach((r) => {
      const rk = r.dataset.keys.split(' ').filter(Boolean), ok = (!t || r.dataset.search.includes(t)) && (!k || rk.includes(k)) && (!m || rk.some((x) => (x.endsWith('m') ? 'minor' : 'major') === m)) && (!kd || r.dataset.kind === kd);
      const visible = ok && (filtering || expanded || shown < 12);
      r.hidden = !visible; if (ok) shown++;
    });
    empty.hidden = shown > 0;
    more.hidden = filtering || expanded;
  };
  [q, key, mode].forEach((el) => el.addEventListener('input', apply));
  document.querySelectorAll('input[name=kind]').forEach((el) => el.addEventListener('change', apply));
  more.addEventListener('click', () => { expanded = true; apply(); });
  apply();
})();
</script>
</body>
</html>
'''
open(os.path.join(HERE, 'home.html'), 'w', encoding='utf-8').write(home)

# ---------- song (榮耀真光) ----------
vers = [s for s in songs if s['title'].startswith('榮耀真光')]
others = [w for w in originals.values() if w['title'] != '榮耀真光']
tabs = '\n'.join(f'''      <button type="button" role="tab" id="v{i}" aria-selected="{'true' if i == 0 else 'false'}" tabindex="{0 if i == 0 else -1}" data-vid="{s['youtube_id']}">{'鋼琴版' if '鋼琴' in s['title'] else '演唱版'}</button>''' for i, s in enumerate(vers))
v0 = vers[0]
related = '\n'.join(f'''    <li><a class="work" href="#">
      <span class="cover"><img src="{thumb(w['vid'])}" width="1280" height="720" alt="" loading="lazy"></span>
      <h3>{e(w['title'])}<span class="en" lang="en">{e(w['en'])}</span></h3>
      <span class="work__meta">{'、'.join(w['versions'])}</span>
    </a></li>''' for w in others)

song = head('榮耀真光 鋼琴與演唱版，C 大調樂譜｜狼的格律') + f'''<main id="main"><div class="container">
  <nav aria-label="位置"><ol class="crumbs"><li><a href="home.html">首頁</a></li><li><a href="home.html#catalog">曲目</a></li><li aria-current="page">榮耀真光</li></ol></nav>
  <div class="song">
    <div>
      <h1>榮耀真光<span class="en" lang="en">True Light of Glory</span></h1>
      <div class="versions" role="tablist" aria-label="版本">
{tabs}
      </div>
      <a class="cover" id="player" href="https://www.youtube.com/watch?v={v0['youtube_id']}" aria-label="播放 榮耀真光">
        <img src="{thumb(v0['youtube_id'])}" width="1280" height="720" alt="榮耀真光 影片封面" fetchpriority="high">
        <span class="cover__play">{ICON['play']}</span>
      </a>
    </div>
    <aside class="side" aria-label="曲目資訊">
      <dl class="facts">
        <dt>調性</dt><dd class="key">C 大調</dd>
        <dt>作曲</dt><dd>狼的格律</dd>
        <dt>作詞</dt><dd>狼的格律</dd>
        <dt>版本</dt><dd>演唱版、鋼琴版</dd>
      </dl>
      <a class="btn" href="../assets/sheets/榮耀真光.pdf" download>{ICON['download']}下載樂譜 PDF</a>
      <a class="link" href="../assets/sheets/榮耀真光.pdf">在瀏覽器開啟樂譜</a>
    </aside>
  </div>

  <section class="sec" style="padding-top: 0" aria-labelledby="h-lyr">
    <h2 class="h2" id="h-lyr">歌詞</h2>
    <p style="margin-top: var(--space-md)"><span class="fill" data-fill="lyrics">歌詞待提供</span></p>
    <h2 class="h2" style="margin-top: var(--space-2xl)">經文與簡介</h2>
    <p style="margin-top: var(--space-md)"><span class="fill" data-fill="devotion">靈修經文與簡介，草擬後待審</span></p>
  </section>
</div>

<section class="sec sec--well" aria-labelledby="h-more"><div class="container">
  <div class="sec__head"><h2 class="h2" id="h-more">狼的格律的其他原創曲目</h2></div>
  <ul class="rail" tabindex="0" aria-label="其他原創">
{related}
  </ul>
</div></section>
</main>
''' + FOOT + '''<script>
(() => {
  const tabs = [...document.querySelectorAll('.versions [role=tab]')], player = document.getElementById('player');
  const select = (t) => {
    tabs.forEach((x) => { const on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; });
    const id = t.dataset.vid, p = document.getElementById('player');
    if (p.tagName === 'A') { p.href = 'https://www.youtube.com/watch?v=' + id; p.querySelector('img').src = 'https://i.ytimg.com/vi/' + id + '/maxresdefault.jpg'; }
    else p.querySelector('iframe').src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1';
  };
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => select(t));
    t.addEventListener('keydown', (ev) => { const d = ev.key === 'ArrowRight' ? 1 : ev.key === 'ArrowLeft' ? -1 : 0; if (d) { const n = tabs[(i + d + tabs.length) % tabs.length]; n.focus(); select(n); } });
  });
  player.addEventListener('click', (ev) => {
    ev.preventDefault();
    const id = document.querySelector('.versions [aria-selected=true]').dataset.vid, box = document.createElement('div');
    box.className = 'cover'; box.id = 'player';
    box.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1" title="榮耀真光 影片" allow="autoplay; encrypted-media; fullscreen" allowfullscreen style="width:100%;height:100%;border:0"></iframe>';
    player.replaceWith(box);
  }, { once: true });
})();
</script>
</body>
</html>
'''
open(os.path.join(HERE, 'song.html'), 'w', encoding='utf-8').write(song)
print('built', len(songs), 'songs,', len(originals), 'originals')
