#!/usr/bin/env python3
"""Print, as a JSON list, the Ceph versions to release.

Usage: ceph-versions.py < released-tags

Reads the vX.Y.Z tags of quay.io/ceph/ceph (no suffixes, major >= 19) and,
for every major, picks the newest one if it is newer than the newest
released tag of that major. A new major is picked up as well. Only the
newest version per major is picked, so the vX and vX.Y image tags move
forward only.
"""
import json
import re
import sys
import urllib.request

QUAY = "https://quay.io/api/v1/repository/ceph/ceph/tag/"
MIN_MAJOR = 19
VERSION = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")


def parse(tag):
    m = VERSION.match(tag)
    return tuple(map(int, m.groups())) if m else None


def quay_tags():
    page = 1
    while True:
        url = f"{QUAY}?onlyActiveTags=true&filter_tag_name=like:v&limit=100&page={page}"
        with urllib.request.urlopen(url, timeout=30) as r:
            data = json.load(r)
        yield from (t["name"] for t in data["tags"])
        if not data.get("has_additional"):
            return
        page += 1


def newest_per_major(tags):
    newest = {}
    for tag in tags:
        v = parse(tag)
        if v and v[0] >= MIN_MAJOR and v > newest.get(v[0], (0, 0, 0)):
            newest[v[0]] = v
    return newest


upstream = newest_per_major(quay_tags())
released = newest_per_major(sys.stdin.read().split())
versions = [
    "v%d.%d.%d" % v
    for major, v in sorted(upstream.items())
    if v > released.get(major, (0, 0, 0))
]
print(json.dumps(versions))
