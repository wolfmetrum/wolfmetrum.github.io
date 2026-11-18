// Song page: version tabs (?v= picks one) and a click-to-load YouTube player.
(() => {
  const tabs = [...document.querySelectorAll('.versions [role=tab]')], box = document.getElementById('player');
  const keyOut = document.querySelector('[data-key-out]');
  let current = tabs.length ? tabs[0].dataset.vid : new URL(box.querySelector('a').href).searchParams.get('v');
  const load = (autoplay) => {
    const f = document.createElement('iframe');
    f.src = `https://www.youtube-nocookie.com/embed/${current}${autoplay ? '?autoplay=1' : ''}`;
    f.title = box.dataset.title; f.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen'; f.allowFullscreen = true;
    box.replaceChildren(f);
  };
  const select = (t, play) => {
    tabs.forEach((x) => { const on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; });
    current = t.dataset.vid;
    keyOut.textContent = t.dataset.key;
    if (t.dataset.sub) { const s = document.createElement('span'); s.className = 'sub'; s.textContent = t.dataset.sub; keyOut.append(s); }
    const a = box.querySelector('a');
    if (a) { a.href = `https://www.youtube.com/watch?v=${current}`; a.querySelector('img').src = `https://i.ytimg.com/vi/${current}/maxresdefault.jpg`; }
    else if (play) load(true);
  };
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => select(t, true));
    t.addEventListener('keydown', (ev) => {
      const d = { ArrowRight: 1, ArrowLeft: -1 }[ev.key];
      if (d) { const n = tabs[(i + d + tabs.length) % tabs.length]; n.focus(); select(n, true); }
    });
  });
  const want = tabs.find((t) => t.dataset.vid === new URLSearchParams(location.search).get('v'));
  if (want) select(want, false);
  box.addEventListener('click', (ev) => { if (ev.target.closest('a')) { ev.preventDefault(); load(true); } });
})();
