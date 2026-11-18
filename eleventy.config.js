import yaml from 'js-yaml';
import t from './src/_data/t.js';

const KIND = ['original', 'hymn', 'contemporary'];
const VTYPE = ['vocal', 'piano'];
const KEY = /^[A-G][b#]?m?$/;

// Parse works.yml and refuse to build on data mistakes (bad key, duplicate slug or video, missing field).
function loadWorks(works, occasions) {
  const seen = new Set(), vids = new Set();
  for (const w of works) {
    const where = `works.yml: ${w.slug || w.title}`;
    for (const f of ['slug', 'title', 'title_en', 'kind', 'versions']) if (!w[f]) throw new Error(`${where}: missing ${f}`);
    if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(w.slug)) throw new Error(`${where}: slug must be kebab-case`);
    if (seen.has(w.slug)) throw new Error(`${where}: duplicate slug`);
    seen.add(w.slug);
    if (!KIND.includes(w.kind)) throw new Error(`${where}: kind must be ${KIND.join(' | ')}`);
    for (const o of w.occasions || []) if (!occasions.includes(o)) throw new Error(`${where}: unknown occasion ${o}`);
    for (const v of w.versions) {
      if (!v.youtube_id || vids.has(v.youtube_id)) throw new Error(`${where}: missing or duplicate youtube_id ${v.youtube_id}`);
      vids.add(v.youtube_id);
      if (!VTYPE.includes(v.type)) throw new Error(`${where}: version type must be vocal | piano`);
      if (!KEY.test(v.key || '')) throw new Error(`${where}: bad key ${v.key} (write C, Bb, C#, Cm)`);
    }
    for (const l of w.lyrics || []) if (!t.zh.parts[l.part] || !l.text) throw new Error(`${where}: lyrics part must be ${Object.keys(t.zh.parts).join(' | ')} with text`);
    if (w.lyrics && w.kind !== 'original') throw new Error(`${where}: lyrics are for originals only (copyright)`);
    w.occasions ||= [];
    w.keys = [...new Set(w.versions.map((v) => v.key))];
  }
  return works;
}

export default function (eleventyConfig) {
  eleventyConfig.addDataExtension('yml', (contents, filePath) => {
    const data = yaml.load(contents);
    return filePath.endsWith('works.yml') ? loadWorks(data, [...t.seasons, ...t.uses]) : data;
  });

  for (const p of ['assets', 'CNAME', 'robots.txt', 'googlef453320dbab9cf01.html']) eleventyConfig.addPassthroughCopy(p);

  // ©️ in the data carries an emoji variation selector; drop it everywhere text is shown
  eleventyConfig.addFilter('clean', (s) => String(s ?? '').replace(/️/g, ''));
  eleventyConfig.addFilter('keySign', (k) => (k || '').replace(/b/g, '♭').replace(/#/g, '♯'));
  eleventyConfig.addFilter('keyName', (k, t) => {
    if (!k) return '';
    const minor = k.endsWith('m'), root = (minor ? k.slice(0, -1) : k).replace(/b/g, '♭').replace(/#/g, '♯');
    return `${root}${t.keyGap}${minor ? t.minor : t.major}`;
  });
  // English display of a Chinese name or source: exact name map first, then ordered term replacement
  eleventyConfig.addFilter('tr', (s, t) => {
    s = String(s ?? '').replace(/️/g, '');
    if (!t.names) return s;
    if (t.names[s]) return t.names[s];
    for (const { from, to } of t.terms) s = s.split(from).join(to);
    return s.replace(/\s+(\d)/g, ' $1').trim();
  });
  eleventyConfig.addFilter('fmt', (s, n) => String(s).replace('{n}', n));
  eleventyConfig.addFilter('thumb', (id) => `https://i.ytimg.com/vi/${id}/maxresdefault.jpg`);
  eleventyConfig.addFilter('altUrl', (url, lang) => (lang === 'en' ? url.replace(/^\/en/, '') || '/' : '/en' + url));
  eleventyConfig.addFilter('versionLabel', (v, t) => {
    const extra = [v.lyrics === 2 ? t.lyrics2 : '', v.transpose ? t.transpose.replace('{n}', -v.transpose) : ''].filter(Boolean);
    return t[v.type] + (extra.length ? `${t.paren[0]}${extra.join(t.comma)}${t.paren[1]}` : '');
  });
  eleventyConfig.addFilter('byKind', (works, kind) => works.filter((w) => w.kind === kind));
  eleventyConfig.addFilter('withSheet', (works) => works.filter((w) => w.sheet_music));
  eleventyConfig.addFilter('related', (works, w) => works.filter((x) => x.kind === w.kind && x.slug !== w.slug).slice(0, 8));
  eleventyConfig.addFilter('countOccasion', (works, o) => works.filter((w) => w.occasions.includes(o)).length);
  eleventyConfig.addFilter('usedOccasions', (works, ids) => ids.filter((o) => works.some((w) => w.occasions.includes(o))));
  eleventyConfig.addFilter('videoMap', (works) => JSON.stringify(Object.fromEntries(works.flatMap((w) => w.versions.map((v) => [v.youtube_id, w.slug])))));
  eleventyConfig.addFilter('json', (v) => JSON.stringify(v));
  eleventyConfig.addFilter('sortedKeys', (works) => [...new Set(works.flatMap((w) => w.keys))].sort((a, b) => {
    const r = (k) => 'CDEFGAB'.indexOf(k[0]) * 10 + (k[1] === 'b' ? 0 : k[1] === '#' ? 2 : 1) + (k.endsWith('m') ? 0.5 : 0);
    return r(a) - r(b);
  }));

  return {
    dir: { input: 'src', includes: '_includes', data: '_data', output: '_site' },
    htmlTemplateEngine: 'njk',
    markdownTemplateEngine: 'njk',
  };
}
