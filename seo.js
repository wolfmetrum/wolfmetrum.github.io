// Page titles, descriptions and schema.org JSON-LD for search engines.
const sign = (k) => k.replace(/b/g, '♭').replace(/#/g, '♯');
const keyName = (k, L) => (k.endsWith('m') ? `${sign(k.slice(0, -1))}${L.keyGap}${L.minor}` : `${sign(k)}${L.keyGap}${L.major}`);
const tr = (s, L) => {
  s = String(s ?? '').replace(/️/g, '');
  if (!L.names) return s;
  if (L.names[s]) return L.names[s];
  for (const { from, to } of L.terms) s = s.split(from).join(to);
  return s.replace(/\s+(\d)/g, ' $1').trim();
};
const person = (w, field, L) => (L.names ? w[`${field}_en`] || tr(w[field], L) : w[field]);
const list = (items, L) => (items.length < 2 ? items.join('') : items.slice(0, -1).join(L.seo.listSep) + L.seo.and + items.at(-1));

// What the work offers, e.g. 「演唱版、鋼琴伴奏與樂譜」 / "vocal, piano accompaniment and sheet music"
function offers(w, L) {
  const types = new Set(w.versions.map((v) => v.type));
  return list([types.has('vocal') && L.seo.vocal, types.has('piano') && L.seo.piano, w.sheet_music && L.seo.sheet].filter(Boolean), L);
}

export function songTitle(w, L) {
  const name = L.names ? w.title_en : `${w.title} ${w.title_en}`;
  const what = L.names ? offers(w, L).replace(/\b(?!and\b)\w/g, (c) => c.toUpperCase()) : offers(w, L);
  return `${name}${L.seo.titleSep}${what}${L.paren[0]}${w.keys.map(sign).join(L.seo.listSep)}${L.paren[1]}`;
}

export function songDescription(w, L) {
  const zh = !L.names;
  const name = zh ? `${w.title}（${w.title_en}）` : `${w.title_en} (${w.title})`;
  const parts = [`${name}${zh ? '' : ': '}${w.kind === 'original' ? L.seo.original : ''}${offers(w, L)}${L.seo.inKey}${w.keys.map((k) => keyName(k, L)).join(L.seo.listSep)}`];
  if (w.source && w.kind !== 'original') parts.push(`${L.seo.from}${tr(w.source, L)}`);
  if (w.composer && w.composer === w.lyricist) parts.push(`${L.wordsMusic}${L.seo.colon}${person(w, 'composer', L)}`);
  else {
    if (w.composer) parts.push(`${L.composer}${L.seo.colon}${person(w, 'composer', L)}`);
    if (w.lyricist) parts.push(`${L.lyricist}${L.seo.colon}${person(w, 'lyricist', L)}`);
  }
  if (w.lyrics) parts.push(L.seo.withLyrics);
  return parts.join(L.seo.clause) + L.seo.end;
}

const iso = (s) => `PT${Math.floor(s / 60)}M${s % 60}S`;
const thumb = (v) => `https://i.ytimg.com/vi/${v.youtube_id}/${v.thumb === 'hq' ? 'hqdefault' : 'maxresdefault'}.jpg`;

export function homeLd(t, L) {
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'MusicGroup', '@id': `${t.url}/#group`, name: t.zh.site, alternateName: t.en.site, url: `${t.url}/`,
        logo: `${t.url}/assets/images/wolfmetrum-logo-512.png`, image: `${t.url}/assets/images/wolfmetrum-logo-512.png`,
        genre: ['Christian music', 'Hymns'], sameAs: [t.youtube], member: { '@type': 'Person', name: 'Aegisulf' },
      },
      { '@type': 'WebSite', '@id': `${t.url}/#site`, url: `${t.url}/`, name: L.siteFull, inLanguage: L.htmlLang, publisher: { '@id': `${t.url}/#group` } },
    ],
  };
}

export function songLd(w, t, L, url) {
  const page = t.url + url;
  const group = { '@id': `${t.url}/#group` };
  const who = (field) => (w[field] === t.zh.site ? group : w[field] ? { '@type': 'Person', name: person(w, field, L) } : undefined);
  const desc = songDescription(w, L);
  const name = L.names ? w.title_en : w.title;
  return {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'BreadcrumbList',
        itemListElement: [
          { '@type': 'ListItem', position: 1, name: L.home, item: `${t.url}${L.prefix}/` },
          { '@type': 'ListItem', position: 2, name, item: page },
        ],
      },
      {
        '@type': 'MusicComposition', '@id': `${page}#work`, name: w.title, alternateName: w.title_en, url: page, inLanguage: 'zh-TW',
        composer: who('composer'), lyricist: who('lyricist'),
        lyrics: w.lyrics ? { '@type': 'CreativeWork', inLanguage: 'zh-TW', text: w.lyrics.map((p) => p.text).join('\n\n') } : undefined,
        subjectOf: w.versions.map((v) => ({ '@id': `${page}#${v.youtube_id}` })),
      },
      ...w.versions.map((v) => ({
        '@type': 'VideoObject', '@id': `${page}#${v.youtube_id}`,
        name: `${name}${L.paren[0]}${versionLabel(v, L)}${L.paren[1]}`, description: desc,
        thumbnailUrl: thumb(v), uploadDate: v.date, duration: iso(v.seconds),
        embedUrl: `https://www.youtube.com/embed/${v.youtube_id}`, url: `https://www.youtube.com/watch?v=${v.youtube_id}`,
        publisher: group,
      })),
    ],
  };
}

export function versionLabel(v, L) {
  const extra = [v.lyrics === 2 ? L.lyrics2 : '', v.transpose ? L.transpose.replace('{n}', -v.transpose) : ''].filter(Boolean);
  return L[v.type] + (extra.length ? `${L.paren[0]}${extra.join(L.comma)}${L.paren[1]}` : '');
}

// Self-check: run `node seo.js`
if (process.argv[1]?.endsWith('seo.js')) {
  const { default: t } = await import('./src/_data/t.js');
  const w = { title: '感謝神', title_en: 'Thanks to God', kind: 'hymn', source: '聖徒詩歌713', composer: 'A', lyricist: 'B', keys: ['Bb', 'G'], versions: [{ type: 'piano' }] };
  console.assert(songTitle(w, t.zh) === '感謝神 Thanks to God 鋼琴伴奏（B♭、G）', songTitle(w, t.zh));
  console.assert(songTitle(w, t.en) === 'Thanks to God: Piano Accompaniment (B♭, G)', songTitle(w, t.en));
  console.log(songDescription(w, t.zh));
  console.log(songDescription(w, t.en));
}
