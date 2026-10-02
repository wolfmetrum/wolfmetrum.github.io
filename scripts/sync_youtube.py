"""Append new YouTube uploads to _data/songs.yml.

Reads the channel's uploads via YouTube Data API v3 (key from YOUTUBE_API_KEY),
parses the "作品與版權資訊" block in each video description, and appends entries
for video ids that are not yet in songs.yml. Existing entries are never touched.
A PR description is written to the path in PR_BODY_PATH (default pr_body.md).
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SONGS_PATH = os.path.join(ROOT, "_data", "songs.yml")
CONFIG_PATH = os.path.join(ROOT, "_config.yml")

HEADER = "作品與版權資訊"
BULLET_RE = re.compile(r"^\s*[•・·\-\*]\s*(.+?)\s*[：:]\s*(.*?)\s*$")
KEYED_FIELDS = {"曲名": "title", "作曲": "composer", "作詞": "lyricist", "標籤": "tags"}
NOTE_INDEX = 3  # 第 4 列固定為備註，不論欄位名稱
TRANSPOSED_RE = re.compile(r"^[(（]\s*移調\s*[)）]\s*")
KEY_RE = re.compile(r"^[A-G][#b]?m?")
PLAIN_UNSAFE_RE = re.compile(r"(^[\s\[\]{}&*!|>'\"%@`#,-]|\s$|: | #|:$|[\[\]{},])")
YAML_SPECIAL_RE = re.compile(r"^(true|false|yes|no|on|off|null|~|[-+]?[\d.][\d._:eE+-]*)$", re.I)


def parse_description(desc):
    """Return a dict of song fields parsed from the info block, or None if absent."""
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
    for idx, (key, value) in enumerate(bullets):
        field = next((f for k, f in KEYED_FIELDS.items() if key.startswith(k)), None)
        if field is None and idx == NOTE_INDEX and not key.startswith(("鋼琴", "調性")):
            field = "note"
        if key.startswith("調性"):
            if TRANSPOSED_RE.match(value):
                fields["dontplay"] = True
                value = TRANSPOSED_RE.sub("", value)
            m = KEY_RE.match(value.strip())
            if m:
                fields["key"] = m.group(0)
            continue
        if field and value:
            fields[field] = value

    if "tags" in fields:
        fields["tags"] = [t.strip() for t in re.split(r"[,，、]", fields["tags"]) if t.strip()]
    return fields


def yaml_scalar(value):
    if PLAIN_UNSAFE_RE.search(value) or YAML_SPECIAL_RE.match(value):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def render_entry(song):
    lines = [f"- title: {yaml_scalar(song['title'])}"]
    for key in ("composer", "lyricist", "note"):
        if song.get(key):
            lines.append(f"  {key}: {yaml_scalar(song[key])}")
    lines.append(f"  youtube_id: {song['youtube_id']}")
    if song.get("key"):
        lines.append(f"  key: {song['key']}")
    lines.append("  tags: [" + ", ".join(yaml_scalar(t) for t in song.get("tags", [])) + "]")
    if song.get("dontplay"):
        lines.append("  dontplay: true")
    return "\n".join(lines)


def api_get(endpoint, **params):
    params["key"] = os.environ["YOUTUBE_API_KEY"]
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        sys.exit(f"YouTube API error {e.code}: {e.read().decode('utf-8', 'replace')}")


def fetch_uploads(channel_id):
    playlist = "UU" + channel_id[2:]
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
        data = api_get("videos", part="snippet", id=",".join(ids[i:i + 50]))
        for item in data.get("items", []):
            videos[item["id"]] = item["snippet"]
    return videos


def main():
    with open(CONFIG_PATH, encoding="utf-8") as f:
        channel_id = re.search(r"^youtube_channel_id:\s*(\S+)", f.read(), re.M).group(1)
    with open(SONGS_PATH, encoding="utf-8", newline="") as f:
        raw = f.read()
    existing = set(re.findall(r"youtube_id:\s*(\S+)", raw))

    upload_ids = fetch_uploads(channel_id)
    new_ids = [v for v in upload_ids if v not in existing]
    videos = fetch_videos(new_ids)

    added, flagged, skipped = [], [], []
    entries = []
    for vid in reversed(new_ids):  # 舊的在前，新的在後
        snippet = videos.get(vid)
        if not snippet:
            continue  # 私人或已刪除
        fields = parse_description(snippet.get("description", ""))
        if fields and fields.get("title"):
            song = dict(fields, youtube_id=vid)
            added.append(song["title"])
        else:
            m = re.search(r"《(.+?)》", snippet.get("title", ""))
            if not m:
                skipped.append(f"{snippet.get('title', vid)} (https://youtu.be/{vid})")
                continue
            song = {"title": m.group(1), "youtube_id": vid, "tags": []}
            flagged.append(f"{song['title']} (https://youtu.be/{vid})")
        entries.append(render_entry(song))

    if entries:
        nl = "\r\n" if "\r\n" in raw else "\n"
        text = raw.replace("\r\n", "\n").rstrip("\n") + "\n\n" + "\n\n".join(entries) + "\n"
        with open(SONGS_PATH, "w", encoding="utf-8", newline="") as f:
            f.write(text.replace("\n", nl))

    body = ["自動從 YouTube 頻道同步新曲目。", ""]
    if added:
        body += ["### 已加入", *[f"- {t}" for t in added], ""]
    if flagged:
        body += ["### ⚠️ 缺少「作品與版權資訊」區塊（僅填入曲名，請補作曲／作詞／備註／標籤）",
                 *[f"- {t}" for t in flagged], ""]
    if skipped:
        body += ["### 已略過（描述無資訊區塊，標題也沒有《》）", *[f"- {t}" for t in skipped], ""]
    body.append("提醒：`sheet_music` 無法自動帶入，需要的話請手動補上。")
    with open(os.environ.get("PR_BODY_PATH", "pr_body.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(body) + "\n")

    print(f"new={len(entries)} flagged={len(flagged)} skipped={len(skipped)}")


if __name__ == "__main__":
    main()
