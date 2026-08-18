"""
Fetch pub/restaurant/lodging ratings, review counts and photos from mapy.com
(Seznam's Czech map portal) for the food/lodging POIs in data/pois.json.

The official public api.mapy.cz API (geocode/suggest/routing/elevation) does
NOT expose ratings or reviews -- verified by calling /v1/suggest and
inspecting every field it returns (only name/label/position/bbox/type/
location/regionalStructure/zip). See data/ratings_report.md for details.

This script instead uses two *unofficial*, undocumented endpoints of the
mapy.com web frontend (discovered by inspecting its network traffic in a
browser):

  1. GET https://mapy.com/api/suggest/?phrase=<name>&lon=<lon>&lat=<lat>&...
     Plain JSON. Location-biased place search. Each result carries a
     "source" (e.g. "osm", "firm") and an internal numeric "id" that
     identifies the place in mapy.com's own database (NOT the OSM node id
     -- mapy.com re-numbers imported OSM features internally).

  2. POST https://mapy.com/api/poiagg
     Body/response use "FRPC" (Fast RPC), Seznam's open binary RPC protocol
     (magic bytes 0xCA 0x11). We call the "detail" method with
     params ["<source>", <id>, {options}] to get the full POI detail,
     which includes a "review" struct (review_rating_stars, total,
     use_rating, use_total) and a "gallery" struct with photo URLs.

Both endpoints require no authentication or cookies -- plain unauthenticated
requests work fine with just a User-Agent header.

Matching strategy (since we only have OSM node ids + names + coordinates,
and mapy.com's ids don't correspond to OSM ids):
  - Query /api/suggest with the POI's name, biased to its coordinates.
  - Among results, keep only those within MATCH_RADIUS_M meters of the POI.
  - Score remaining candidates by fuzzy name similarity (difflib) and
    take the best one if it clears MIN_NAME_SIM.
  - POIs with an empty name, or with no matching candidate, are skipped.

Then for the matched (source, id): call the "detail" FRPC method.
  - If review.use_rating is false (no real rating on mapy.com), the POI is
    omitted from the output entirely -- no fabricated ratings.
  - Otherwise: rating = review.review_rating_stars, count = review.total.
  - photo: first gallery image's "default" (or "1x1") URL template, with
    the {width}/{height} placeholders filled in.

Output: data/ratings.json = {"<poi id>": {"rating": float, "count": int,
"photo": "<url>" (optional)}, ...}
"""
import json
import re
import struct
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from difflib import SequenceMatcher
from math import radians, sin, cos, asin, sqrt

UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
SLEEP_S = 0.3
MATCH_RADIUS_M = 150
MIN_NAME_SIM = 0.45
PHOTO_SIZE = 480


# ------------------------------------------------------------------------
# Minimal FRPC (Fast RPC, Seznam's binary RPC protocol) codec.
# Spec: https://github.com/seznam/fastrpc/wiki/FastRPC-binary-protocol-specification
# Reverse-verified against real mapy.com traffic (see ratings_report.md).
# ------------------------------------------------------------------------

class FRPCError(Exception):
    pass


def _parse_value(buf, pos):
    tag = buf[pos]
    pos += 1
    type_id = tag >> 3
    n = (tag & 0x07) + 1
    if type_id == 7:  # integer: n octets, little-endian
        val = int.from_bytes(buf[pos:pos + n], "little")
        pos += n
        return val, pos
    if type_id == 2:  # boolean: value is low bit of tag, no extra bytes
        return bool(tag & 0x01), pos
    if type_id == 3:  # double: fixed 8 octets
        val = struct.unpack("<d", buf[pos:pos + 8])[0]
        pos += 8
        return val, pos
    if type_id == 4:  # string: n-octet length prefix + utf-8 bytes
        ln = int.from_bytes(buf[pos:pos + n], "little")
        pos += n
        raw = buf[pos:pos + ln]
        pos += ln
        return raw.decode("utf-8", errors="replace"), pos
    if type_id == 6:  # binary
        ln = int.from_bytes(buf[pos:pos + n], "little")
        pos += n
        raw = buf[pos:pos + ln]
        pos += ln
        return raw, pos
    if type_id == 10:  # struct: n-octet member count, then (namelen-byte+name+value)*
        cnt = int.from_bytes(buf[pos:pos + n], "little")
        pos += n
        d = {}
        for _ in range(cnt):
            namelen = buf[pos]
            pos += 1
            name = buf[pos:pos + namelen].decode("utf-8", errors="replace")
            pos += namelen
            val, pos = _parse_value(buf, pos)
            d[name] = val
        return d, pos
    if type_id == 11:  # array: n-octet item count, then value*
        cnt = int.from_bytes(buf[pos:pos + n], "little")
        pos += n
        arr = []
        for _ in range(cnt):
            val, pos = _parse_value(buf, pos)
            arr.append(val)
        return arr, pos
    if type_id == 12:  # null
        return None, pos
    raise FRPCError(f"unknown FRPC type_id {type_id} (tag={tag:#x}) at byte {pos - 1}")


def frpc_parse_message(buf):
    if buf[0:2] != b"\xca\x11":
        raise FRPCError("bad FRPC magic")
    pos = 4  # skip magic + 2 version bytes
    tag = buf[pos]
    if tag == 0x68:  # method call
        pos += 1
        namelen = buf[pos]; pos += 1
        name = buf[pos:pos + namelen].decode(); pos += namelen
        params = []
        while pos < len(buf):
            val, pos = _parse_value(buf, pos)
            params.append(val)
        return {"type": "call", "method": name, "params": params}
    if tag == 0x70:  # response
        pos += 1
        val, pos = _parse_value(buf, pos)
        return {"type": "response", "value": val}
    if tag == 0x78:  # fault
        pos += 1
        code, pos = _parse_value(buf, pos)
        msg, pos = _parse_value(buf, pos)
        return {"type": "fault", "code": code, "message": msg}
    raise FRPCError(f"unknown top-level FRPC tag {tag:#x}")


def _len_bytes(n):
    if n == 0:
        return b"\x00"
    out = bytearray()
    while n > 0:
        out.append(n & 0xFF)
        n >>= 8
    return bytes(out)


def _encode_value(val):
    if isinstance(val, bool):
        return bytes([0x10 | (1 if val else 0)])
    if isinstance(val, int):
        lb = _len_bytes(val)
        return bytes([0x38 | (len(lb) - 1)]) + lb
    if isinstance(val, float):
        return bytes([0x18]) + struct.pack("<d", val)
    if isinstance(val, str):
        raw = val.encode("utf-8")
        lb = _len_bytes(len(raw))
        return bytes([0x20 | (len(lb) - 1)]) + lb + raw
    if val is None:
        return bytes([0x60])
    if isinstance(val, dict):
        lb = _len_bytes(len(val))
        out = bytearray([0x50 | (len(lb) - 1)]) + bytearray(lb)
        for k, v in val.items():
            kb = k.encode("utf-8")
            out += bytes([len(kb)]) + kb + _encode_value(v)
        return bytes(out)
    if isinstance(val, (list, tuple)):
        lb = _len_bytes(len(val))
        out = bytearray([0x58 | (len(lb) - 1)]) + bytearray(lb)
        for item in val:
            out += _encode_value(item)
        return bytes(out)
    raise FRPCError(f"cannot encode type {type(val)}")


def frpc_encode_call(method, params, version=(2, 1)):
    out = bytearray(b"\xca\x11" + bytes(version) + bytes([0x68]))
    mb = method.encode("utf-8")
    out += bytes([len(mb)]) + mb
    for p in params:
        out += _encode_value(p)
    return bytes(out)


# ------------------------------------------------------------------------
# mapy.com HTTP calls
# ------------------------------------------------------------------------

def http_get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def suggest(name, lat, lon):
    params = {
        "count": 8, "phrase": name, "lon": lon, "lat": lat, "zoom": 17,
        "enableCategories": 1, "lang": "en", "personalize": 0,
        "includeNonEntityTypes": 1,
    }
    url = "https://mapy.com/api/suggest/?" + urllib.parse.urlencode(params)
    try:
        return http_get_json(url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None


def poi_detail(source, place_id):
    body = frpc_encode_call("detail", [source, place_id, {
        "fetchPhoto": True, "ratios": ["default", "1x1", "16x9"],
        "wikimedia": True, "lang": ["en"],
    }])
    req = urllib.request.Request(
        "https://mapy.com/api/poiagg", data=body, method="POST",
        headers={**UA, "Content-Type": "application/x-frpc", "Accept": "application/x-frpc"},
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = r.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    try:
        msg = frpc_parse_message(resp)
    except FRPCError:
        return None
    if msg.get("type") != "response":
        return None
    return msg["value"].get("poi")


# ------------------------------------------------------------------------
# Matching helpers
# ------------------------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = radians(lat1), radians(lat2)
    dphi = radians(lat2 - lat1)
    dl = radians(lon2 - lon1)
    a = sin(dphi / 2) ** 2 + cos(p1) * cos(p2) * sin(dl / 2) ** 2
    return 2 * r * asin(sqrt(a))


def norm_name(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def name_sim(a, b):
    return SequenceMatcher(None, norm_name(a), norm_name(b)).ratio()


def best_match(poi):
    data = suggest(poi["name"], poi["lat"], poi["lon"])
    if not data:
        return None
    best = None
    best_score = 0.0
    for item in data.get("result", []):
        ud = item.get("userData", {})
        source, sid = ud.get("source"), ud.get("id")
        lat, lon = ud.get("latitude"), ud.get("longitude")
        if not source or sid is None or lat is None or lon is None:
            continue
        dist = haversine_m(poi["lat"], poi["lon"], lat, lon)
        if dist > MATCH_RADIUS_M:
            continue
        cand_name = ud.get("suggestFirstRow") or ""
        sim = name_sim(poi["name"], cand_name)
        if sim < MIN_NAME_SIM:
            continue
        # score: prioritise name similarity, then closeness
        score = sim - (dist / MATCH_RADIUS_M) * 0.1
        if score > best_score:
            best_score = score
            best = (source, sid, dist, sim, cand_name)
    return best


def photo_url(poi_detail_obj):
    gallery = poi_detail_obj.get("gallery") or []
    if not gallery:
        return None
    media = (gallery[0].get("media") or [{}])[0]
    urls = media.get("urls") or {}
    tmpl = urls.get("default") or urls.get("1x1") or urls.get("16x9")
    if not tmpl:
        return None
    return tmpl.replace("{width}", str(PHOTO_SIZE)).replace("{height}", str(PHOTO_SIZE))


# ------------------------------------------------------------------------
# Main
# ------------------------------------------------------------------------

def main():
    pois_path = "data/pois.json"
    pois = json.load(open(pois_path, encoding="utf-8"))
    targets = [p for p in pois if p.get("cat") in ("food", "lodging", "shelter") and p.get("name", "").strip()]
    print(f"{len(targets)} named food/lodging POIs to process", file=sys.stderr)

    ratings = {}
    matched = 0
    rated = 0
    for i, poi in enumerate(targets):
        m = best_match(poi)
        time.sleep(SLEEP_S)
        if m is None:
            print(f"[{i+1}/{len(targets)}] {poi['name']!r}: no match", file=sys.stderr)
            continue
        source, sid, dist, sim, cand_name = m
        matched += 1
        detail = poi_detail(source, sid)
        time.sleep(SLEEP_S)
        if detail is None:
            print(f"[{i+1}/{len(targets)}] {poi['name']!r} -> {cand_name!r} "
                  f"({dist:.0f}m, sim={sim:.2f}): detail fetch failed", file=sys.stderr)
            continue
        review = detail.get("review") or {}
        if not review.get("use_rating") or review.get("review_rating_stars") in (None, 0.0):
            print(f"[{i+1}/{len(targets)}] {poi['name']!r} -> {cand_name!r}: no rating on mapy.com", file=sys.stderr)
            continue
        entry = {
            "rating": round(float(review["review_rating_stars"]), 1),
            "count": int(review.get("total") or 0),
        }
        photo = photo_url(detail)
        if photo:
            entry["photo"] = photo
        ratings[poi["id"]] = entry
        rated += 1
        print(f"[{i+1}/{len(targets)}] {poi['name']!r} -> {cand_name!r} "
              f"({dist:.0f}m, sim={sim:.2f}): {entry['rating']}★ ({entry['count']} reviews)"
              f"{' +photo' if photo else ''}", file=sys.stderr)

    json.dump(ratings, open("data/ratings.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nDone. matched={matched}/{len(targets)} rated={rated}/{len(targets)}", file=sys.stderr)


if __name__ == "__main__":
    main()
