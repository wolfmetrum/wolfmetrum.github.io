// Home: old ?v=<youtube_id> links, catalogue filters, and the next church-year date.
(() => {
  const params = new URLSearchParams(location.search);
  const prefix = document.documentElement.lang === 'en' ? '/en' : '';
  const vid = params.get('v'), map = JSON.parse(document.getElementById('video-map').textContent);
  if (vid && map[vid]) { location.replace(`${prefix}/songs/${map[vid]}/?v=${encodeURIComponent(vid)}`); return; }

  const norm = (s) => s.toLowerCase().replace(/\s+/g, '');
  const q = document.getElementById('q'), mode = document.getElementById('mode'), key = document.getElementById('key'), occ = document.getElementById('o');
  const rows = [...document.querySelectorAll('.index tbody tr')], more = document.querySelector('.more'), empty = document.querySelector('.empty');
  rows.forEach((r) => { r.search = norm(r.dataset.search); r.keys = r.dataset.keys.split(' '); r.occ = r.dataset.o.split(' '); });
  let expanded = false;
  const apply = () => {
    const t = norm(q.value), k = key.value, m = mode.value, o = occ.value, kd = document.querySelector('input[name=kind]:checked').value;
    const filtering = t || k || m || o || kd;
    let shown = 0;
    rows.forEach((r) => {
      const ok = (!t || r.search.includes(t)) && (!k || r.keys.includes(k)) && (!m || r.keys.some((x) => x.endsWith('m') === (m === 'minor')))
        && (!o || r.occ.includes(o)) && (!kd || r.dataset.kind === kd);
      r.hidden = !(ok && (filtering || expanded || shown < 12));
      if (ok) shown++;
    });
    empty.hidden = shown > 0;
    more.hidden = filtering || expanded || shown <= 12;
  };
  if (params.get('q')) q.value = params.get('q');
  if (params.get('o') && [...occ.options].some((x) => x.value === params.get('o'))) occ.value = params.get('o');
  [q, key, mode, occ].forEach((el) => el.addEventListener('input', apply));
  document.querySelectorAll('input[name=kind]').forEach((el) => el.addEventListener('change', apply));
  more.addEventListener('click', () => { expanded = true; apply(); });
  apply();
  if (params.get('q')) document.getElementById('catalog').scrollIntoView();

  // Mark the next season within six weeks (Western Easter; Taiwan's Mother's Day and Father's Day)
  const day = 864e5, now = new Date(); now.setHours(0, 0, 0, 0);
  const easter = (y) => { const a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4, f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3), h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4, l = (32 + 2 * e + 2 * i - h - k) % 7, m2 = Math.floor((a + 11 * h + 22 * l) / 451), mo = Math.floor((h + l - 7 * m2 + 114) / 31), da = ((h + l - 7 * m2 + 114) % 31) + 1; return new Date(y, mo - 1, da); };
  const nth = (y, mo, wd, n) => { const d = new Date(y, mo, 1); d.setDate(1 + ((wd - d.getDay() + 7) % 7) + 7 * (n - 1)); return d; };
  const dates = (y) => {
    const e = easter(y), add = (n) => new Date(e.getTime() + n * day), xmas = new Date(y, 11, 25);
    const advent = new Date(xmas); advent.setDate(25 - (xmas.getDay() || 7) - 21);
    return { advent, christmas: xmas, newyear: new Date(y, 0, 1), palm: add(-7), goodfriday: add(-2), easter: e, pentecost: add(49), parents: nth(y, 4, 0, 2), thanksgiving: nth(y, 10, 4, 4) };
  };
  const all = [dates(now.getFullYear()), dates(now.getFullYear() + 1)].flatMap((o) => Object.entries(o));
  const next = all.filter(([, d]) => d >= now && d - now <= 42 * day).sort((a, b) => a[1] - b[1])[0];
  const li = next && document.querySelector(`.year [data-season="${next[0]}"]`);
  if (li) { li.setAttribute('aria-current', 'date'); li.querySelector('.now').hidden = false; }
})();
