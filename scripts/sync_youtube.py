"""Add new YouTube uploads to src/_data/works.yml.

Reads the channel's uploads via YouTube Data API v3 (key from YOUTUBE_API_KEY) and parses the
"作品與版權資訊" block in each new video's description. A video whose title (without its trailing
parentheses such as (演唱版) (鋼琴版) (降3) (第二詞)) matches an existing work becomes a new version
of that work; otherwise a new work is inserted at the top (newest first). Existing data is never
rewritten, only added to. A PR description is written to PR_BODY_PATH (default pr_body.md).
"""
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKS_PATH = os.path.join(ROOT, "src", "_data", "works.yml")
CHANNEL_ID = "UCqdp7Moy1guJ1UHCocdKFWQ"

HEADER = "作品與版權資訊"
BULLET_RE = re.compile(r"^\s*[•・·\-\*]\s*(.+?)\s*[：:]\s*(.*?)\s*$")
KEYED_FIELDS = {"曲名": "title", "英文": "title_en", "作曲": "composer", "作詞": "lyricist", "標籤": "tags",
                "節期": "occasions", "用途": "occasions"}
IGNORED_KEYS = ("鋼琴", "調性")
LATIN_RE = re.compile(r"[A-Za-z]")
CJK_RE = re.compile(r"[一-鿿]")
NAME_PAIR_RE = re.compile(r"^(.*?)\s*[(（]\s*(.*?)\s*[)）]$")
TRANSPOSED_RE = re.compile(r"^[(（]\s*移調\s*[)）]\s*")
KEY_RE = re.compile(r"^[A-G][#b]?m?")
TRAILING_PARENS_RE = re.compile(r"(\s*[(（][^()（）]*[)）])+\s*$")
PLAIN_UNSAFE_RE = re.compile(r"(^[\s\[\]{}&*!|>'\"%@`#,-]|\s$|: | #|:$|[\[\]{},])")
YAML_SPECIAL_RE = re.compile(r"^(true|false|yes|no|on|off|null|~|[-+]?[\d.][\d._:eE+-]*)$", re.I)
KIND_TAGS = {"狼的格律原創": "original", "傳統詩歌": "hymn"}
DROP_TAGS = {"狼的格律原創", "傳統詩歌", "現代詩歌", "演唱版", "聖誕詩歌"}
# Occasion names as shown on the site (zh, from src/_data/t.js) plus common alternative names
OCCASION_ALIASES = {"母親節": "parents", "父親節": "parents", "聖靈降臨節": "pentecost", "受難日": "goodfriday",
                    "降臨期": "advent", "將臨期": "advent", "聖誕": "christmas", "感恩": "thanksgiving"}


def occasion_ids():
    """Map each zh occasion name in t.js (e.g. 待降節 -> advent) to its id."""
    with open(os.path.join(ROOT, "src", "_data", "t.js"), encoding="utf-8") as f:
        zh = f.read().split("const en")[0]
    names = {name: oid for oid, name in re.findall(r"(\w+): \{ name: '([^']+)'", zh)}
    return {**OCCASION_ALIASES, **names}


def is_title_en_key(key):
    return key.lower().startswith(("name", "english")) or key.startswith("英文")


def split_names(value):
    """Split "中文 (english), 中文2 (english2)" into (中文 part, english part).

    Names without parentheses (e.g. Western names) are used for both languages.
    Separators (, ， 、) between names are kept as written.
    """
    tokens, seps, buf, depth = [], [], "", 0
    for ch in value:
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth = max(depth - 1, 0)
        if ch in ",，、" and depth == 0:
            tokens.append(buf)
            seps.append(ch + (" " if ch == "," else ""))
            buf = ""
        else:
            buf += ch
    tokens.append(buf)

    zh_parts, en_parts, paired = [], [], False
    for token in tokens:
        token = token.strip()
        m = NAME_PAIR_RE.match(token)
        if m and m.group(1) and LATIN_RE.search(m.group(2)) and not CJK_RE.search(m.group(2)):
            zh_parts.append(m.group(1))
            en_parts.append(m.group(2))
            paired = True
        else:
            zh_parts.append(token)
            en_parts.append(token)

    def join(parts):
        out = parts[0]
        for sep, part in zip(seps, parts[1:]):
            out += sep.rstrip() + " " + part if sep.strip() == "," else sep + part
        return out

    return join(zh_parts), (join(en_parts) if paired else None)


def parse_description(desc):
    """Return a dict of fields parsed from the info block, or None if absent."""
    lines = desc.splitlines()
    start = next((i for i, l in enumerate(lines) if HEADER in l), None)
    if start is None:
        return None

    bullets = []
    for line in lines[start + 1:]:
        if not line.strip():
            if bullets:
                break
            continue
        m = BULLET_RE.match(line)
        if not m:
            if bullets:
                break
            continue
        bullets.append((m.group(1).strip(), m.group(2).strip()))
    if not bullets:
        return None

    fields = {}
    for key, value in bullets:
        field = "title_en" if is_title_en_key(key) else next(
            (f for k, f in KEYED_FIELDS.items() if key.startswith(k)), None)
        # 出處：第一個不是已知欄位的列（欄位名稱不限，例如「收錄」）
        if field is None and not key.startswith(IGNORED_KEYS) and "source" not in fields:
            field = "source"
        if key.startswith("調性"):
            if TRANSPOSED_RE.match(value):
                fields["transposed"] = True
                value = TRANSPOSED_RE.sub("", value)
            m = KEY_RE.match(value.strip())
            if m:
                fields["key"] = m.group(0)
            continue
        if field and value:
            fields[field] = value

    for field in ("composer", "lyricist"):
        if field in fields:
            fields[field], en = split_names(fields[field])
            if en:
                fields[field + "_en"] = en

    for field in ("tags", "occasions"):
        if field in fields:
            fields[field] = [t.strip() for t in re.split(r"[,，、]", fields[field]) if t.strip()]
    return fields


def split_title(title):
    """'感謝神(降3)' -> ('感謝神', ['降3'])"""
    m = TRAILING_PARENS_RE.search(title)
    if not m:
        return title.strip(), []
    return title[:m.start()].strip(), re.findall(r"[(（]([^()（）]*)[)）]", m.group(0))


def slugify(s):
    s = s.lower().replace("'", "").replace("’", "")
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def yaml_scalar(value):
    value = str(value)
    if PLAIN_UNSAFE_RE.search(value) or YAML_SPECIAL_RE.match(value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def iso_seconds(duration):
    m = re.fullmatch(r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration or "")
    if not m:
        return None
    d, h, mi, s = (int(x or 0) for x in m.groups())
    return ((d * 24 + h) * 60 + mi) * 60 + s


def make_version(vid, fields, parens, video):
    version = {"youtube_id": vid, "type": "vocal" if "演唱版" in parens or "演唱版" in fields.get("tags", []) else "piano",
               "key": fields.get("key")}
    if "第二詞" in parens:
        version["lyrics"] = 2
    down = next((int(m.group(1)) for p in parens for m in [re.fullmatch(r"降\s*(\d+)", p)] if m), None)
    if down:
        version["transpose"] = -down
    version["date"] = video["snippet"]["publishedAt"][:10]
    version["seconds"] = iso_seconds(video["contentDetails"]["duration"])
    if "maxres" not in video["snippet"].get("thumbnails", {}):
        version["thumb"] = "hq"
    return version


def render_version(v):
    parts = [f"youtube_id: {v['youtube_id']}", f"type: {v['type']}", f"key: {v['key']}"]
    parts += [f"{k}: {v[k]}" for k in ("lyrics", "transpose") if k in v]
    parts.append(f"date: '{v['date']}'")
    parts += [f"{k}: {v[k]}" for k in ("seconds", "thumb") if v.get(k) is not None]
    return "  - {" + ", ".join(parts) + "}"


def render_work(w):
    lines = [f"- slug: {w['slug']}", f"  title: {yaml_scalar(w['title'])}", f"  title_en: {yaml_scalar(w['title_en'])}"]
    for key in ("composer", "composer_en", "lyricist", "lyricist_en", "source"):
        if w.get(key):
            lines.append(f"  {key}: {yaml_scalar(w[key])}")
    lines.append(f"  kind: {w['kind']}")
    if w.get("tags"):
        lines.append("  tags: [" + ", ".join(yaml_scalar(t) for t in w["tags"]) + "]")
    lines.append("  occasions: [" + ", ".join(w["occasions"]) + "]")
    lines.append("  versions:")
    lines += [render_version(v) for v in w["versions"]]
    return "\n".join(lines)


def add_videos(raw, videos):
    """Merge new videos (newest first) into the works.yml text. Returns (text, report)."""
    text = raw.replace("\r\n", "\n")
    titles = dict(re.findall(r"^- slug: (\S+)\n  title: (.+)$", text, re.M))
    by_title = {yaml_unquote(t): slug for slug, t in titles.items()}
    slugs = set(titles)
    report = {"new": [], "version": [], "check": [], "skipped": [], "unclassified": []}
    occ_ids = occasion_ids()
    new_works = []  # newest first

    for vid, video in videos:
        snippet = video["snippet"]
        link = f"https://youtu.be/{vid}"
        fields = parse_description(snippet.get("description", ""))
        if not fields or not fields.get("title"):
            report["skipped"].append(f"{snippet.get('title', vid)}：描述沒有「作品與版權資訊」區塊或曲名（{link}）")
            continue
        base, parens = split_title(fields["title"])
        if not fields.get("key"):
            report["skipped"].append(f"{base}：描述缺少調性（{link}）")
            continue
        version = make_version(vid, fields, parens, video)
        if fields.get("transposed") and "transpose" not in version:
            report["check"].append(f"{base}：調性標了（移調），但曲名沒有（降N），請手動補上 transpose（{link}）")

        work = next((w for w in new_works if w["title"] == base), None)
        if work:
            work["versions"].append(version)
            report["version"].append(f"{base}（{link}）")
        elif base in by_title:
            slug = by_title[base]
            start = text.index(f"- slug: {slug}\n")
            end = text.find("\n\n- slug:", start)
            block = text[start:end if end != -1 else len(text)].rstrip("\n")
            assert block.splitlines()[-1].startswith("  - {youtube_id"), f"{slug}: versions must be the last field"
            text = text.replace(block, block + "\n" + render_version(version), 1)
            report["version"].append(f"{base}（{link}）")
        else:
            title_en = TRAILING_PARENS_RE.sub("", fields.get("title_en", "")).strip()
            if not title_en:
                report["skipped"].append(f"{base}：描述缺少英文曲名（Name：），無法產生網址（{link}）")
                continue
            slug = slugify(title_en)
            if slug in slugs:
                report["skipped"].append(f"{base}：網址 {slug} 已被其他作品使用，請手動處理（{link}）")
                continue
            slugs.add(slug)
            tags = fields.get("tags", [])
            kind = next((k for t, k in KIND_TAGS.items() if t in tags), "contemporary")
            names = fields.get("occasions", [])
            occasions = list(dict.fromkeys(occ_ids[n] for n in names if n in occ_ids))
            unknown = [n for n in names if n not in occ_ids]
            if unknown:
                report["check"].append(f"{base}：無法辨識的節期或用途「{'、'.join(unknown)}」，請手動補上（{link}）")
            work = {"slug": slug, "title": base, "title_en": title_en, "kind": kind, "occasions": occasions,
                    "tags": [t for t in tags if t not in DROP_TAGS], "versions": [version],
                    **{k: fields[k] for k in ("composer", "composer_en", "lyricist", "lyricist_en", "source") if k in fields}}
            new_works.append(work)
            hint = "（建議：聖誕節）" if "聖誕詩歌" in tags and not occasions else ""
            report["new"].append(f"{base} {title_en}{'' if occasions else '：節期待分類'}{hint}（{link}）")
            if not occasions:
                report["unclassified"].append(base)

    if new_works:
        head_end = text.index("\n- slug:") + 1
        text = text[:head_end] + "\n\n".join(render_work(w) for w in new_works) + "\n\n" + text[head_end:]
    return text, report


def yaml_unquote(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        return s[1:-1].replace('\\"', '"').replace("''", "'")
    return s


def api_get(endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"YouTube API error {e.code}: {e.read().decode('utf-8', 'replace')}")


def fetch_uploads():
    playlist = "UU" + CHANNEL_ID[2:]
    ids, token = [], None
    while True:
        params = dict(part="contentDetails", playlistId=playlist, maxResults=50)
        if token:
            params["pageToken"] = token
        data = api_get("playlistItems", **params)
        ids += [i["contentDetails"]["videoId"] for i in data.get("items", [])]
        token = data.get("nextPageToken")
        if not token:
            return ids


def fetch_videos(ids):
    videos = {}
    for i in range(0, len(ids), 50):
        data = api_get("videos", part="snippet,contentDetails", id=",".join(ids[i:i + 50]))
        for item in data.get("items", []):
            videos[item["id"]] = item
    return videos


def can_publish_directly(report):
    """Clean runs go straight to the site: something was added, nothing skipped or doubtful, every new work classified."""
    return bool(report["new"] or report["version"]) and not (report["check"] or report["skipped"] or report["unclassified"])


def pr_body(report):
    body = ["自動從 YouTube 頻道同步新曲目。", ""]
    sections = [
        ("new", "### 新作品（描述沒寫節期的，請補上 `occasions`）"),
        ("version", "### 加入既有作品的新版本"),
        ("check", "### ⚠️ 需要確認"),
        ("skipped", "### 已略過（請修正影片描述後重新同步，或手動加入）"),
    ]
    for key, title in sections:
        if report[key]:
            body += [title, *[f"- {t}" for t in report[key]], ""]
    body.append("提醒：樂譜（`sheet_music`）、原創曲歌詞（`lyrics`）、經文與簡介（`devotion`）不會自動帶入。")
    return "\n".join(body) + "\n"


def main():
    with open(WORKS_PATH, encoding="utf-8", newline="") as f:
        raw = f.read()
    existing = set(re.findall(r"youtube_id: ([\w-]+)", raw))
    new_ids = [v for v in fetch_uploads() if v not in existing]  # API 由新到舊
    fetched = fetch_videos(new_ids)
    videos = [(vid, fetched[vid]) for vid in new_ids if vid in fetched]  # 私人或已刪除的影片不會回傳

    text, report = add_videos(raw, videos)
    if text != raw.replace("\r\n", "\n"):
        nl = "\r\n" if "\r\n" in raw else "\n"
        with open(WORKS_PATH, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace("\n", nl))
    with open(os.environ.get("PR_BODY_PATH", "pr_body.md"), "w", encoding="utf-8") as f:
        f.write(pr_body(report))
    direct = can_publish_directly(report)
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
            f.write(f"direct={'true' if direct else 'false'}\n")
    print({k: len(v) for k, v in report.items()}, "direct" if direct else "review")


if __name__ == "__main__":
    main()
