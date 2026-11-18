"""Offline check of the works.yml merge: python scripts/test_sync_youtube.py"""
import os
import sys
import unittest

import yaml

sys.path.insert(0, os.path.dirname(__file__))
from sync_youtube import add_videos  # noqa: E402

WORKS = """# header

- slug: thanks-to-god
  title: 感謝神
  title_en: Thanks to God
  kind: hymn
  occasions: [thanksgiving]
  versions:
  - {youtube_id: AAA, type: piano, key: Bb, date: '2025-12-31', seconds: 180}
"""


def video(desc, date="2026-12-01T08:00:00Z", duration="PT3M5S", maxres=True):
    thumbs = {"high": {}, **({"maxres": {}} if maxres else {})}
    return {"snippet": {"title": "t", "description": desc, "publishedAt": date, "thumbnails": thumbs},
            "contentDetails": {"duration": duration}}


def desc(title, key, name=None, extra=""):
    lines = ["🎵 【作品與版權資訊】", f"• 曲名：{title}"]
    if name:
        lines.append(f"• Name：{name}")
    lines += ["• 作曲：狼的格律 (Wolf Metrum)", "• 作詞：狼的格律 (Wolf Metrum)", "• 收錄：Aegisulf©狼的格律", extra or "• 標籤：狼的格律原創, 聖誕詩歌",
              "• 鋼琴編曲／演奏／混音：狼的格律（Wolf Metrum）", f"• 調性：{key}"]
    return "\n".join(lines)


class Merge(unittest.TestCase):
    def test_new_work_new_version_and_skip(self):
        videos = [
            ("NEW1", video(desc("聖誕新歌(演唱版)", "Ebm", "A New Carol (Vocal Version)"))),
            ("NEW2", video(desc("聖誕新歌(鋼琴版)", "Ebm", "A New Carol (Piano Version)"), maxres=False)),
            ("BBB", video(desc("感謝神(降3)", "(移調)G", "Thanks to God (Key -3)", "• 標籤：傳統詩歌, 聖徒詩歌"), duration="PT1H2M")),
            ("CCC", video("no info block")),
        ]
        text, report = add_videos(WORKS, videos)
        works = {w["slug"]: w for w in yaml.safe_load(text)}
        new = works["a-new-carol"]
        self.assertEqual(new["title"], "聖誕新歌")
        self.assertEqual(new["kind"], "original")
        self.assertEqual(new["composer_en"], "Wolf Metrum")
        self.assertEqual(new["occasions"], [])
        self.assertEqual([v["type"] for v in new["versions"]], ["vocal", "piano"])
        self.assertEqual(new["versions"][1], {"youtube_id": "NEW2", "type": "piano", "key": "Ebm", "date": "2026-12-01", "seconds": 185, "thumb": "hq"})
        self.assertEqual(list(works)[0], "a-new-carol")  # new works go on top
        old = works["thanks-to-god"]["versions"]
        self.assertEqual(old[1], {"youtube_id": "BBB", "type": "piano", "key": "G", "transpose": -3, "date": "2026-12-01", "seconds": 3720})
        self.assertEqual(len(report["skipped"]), 1)
        self.assertIn("建議：聖誕節", report["new"][0])

    def test_occasions_line(self):
        d = desc("新歌", "C", "A New Song", "• 標籤：現代詩歌\n• 節期：待降節、母親節、敬拜讚美、不存在")
        text, report = add_videos(WORKS, [("EEE", video(d))])
        new = yaml.safe_load(text)[0]
        self.assertEqual(new["occasions"], ["advent", "parents", "praise"])
        self.assertEqual(new["source"], "Aegisulf©狼的格律")  # 節期 is a known field, not taken as the source
        self.assertEqual(len(report["check"]), 1)

    def test_transposed_without_amount_is_flagged(self):
        _, report = add_videos(WORKS, [("DDD", video(desc("感謝神", "(移調)A", "Thanks to God", "• 標籤：傳統詩歌")))])
        self.assertEqual(len(report["check"]), 1)


if __name__ == "__main__":
    unittest.main()
