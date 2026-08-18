import json, math

legs = json.load(open("data/route_legs.json"))
pois = json.load(open("data/pois.json"))
eles = json.load(open("data/elevation.json"))
photos = json.load(open("data/photos.json"))
try:
    ratings = json.load(open("data/ratings.json"))
except Exception:
    ratings = {}

coords = []
for l in legs: coords += l["coords"]

def m_between(a, b):
    dx = (a[0]-b[0]) * 111320 * math.cos(math.radians((a[1]+b[1])/2))
    dy = (a[1]-b[1]) * 110540
    return math.hypot(dx, dy)

cum = [0.0]
for p, q in zip(coords, coords[1:]): cum.append(cum[-1] + m_between(p, q))
TOTAL = cum[-1]

# výškový profil (~250 m vzorky, musí sedět s fetch_elev)
samples, acc, km = [(coords[0][0], coords[0][1], 0.0)], 0.0, 0.0
for p, q in zip(coords, coords[1:]):
    d = m_between(p, q); km += d; acc += d
    if acc >= 250: samples.append((q[0], q[1], km)); acc = 0
samples.append((coords[-1][0], coords[-1][1], km))
assert len(samples) == len(eles), (len(samples), len(eles))
profile = [{"km": round(s[2]/1000,3), "ele": e["ele"], "lat": round(s[1],6), "lon": round(s[0],6)}
           for s, e in zip(samples, eles)]

up = sum(max(0, b["ele"]-a["ele"]) for a, b in zip(profile, profile[1:]))
dn = sum(max(0, a["ele"]-b["ele"]) for a, b in zip(profile, profile[1:]))

# bez itineráře: jeden souvislý úsek (slouží jen pro geometrii, součty a GPX)
days = [{
    "n": 1, "name": "Púchov → Myjava", "day": "", "desc": "", "sleep": "",
    "kmFrom": 0, "kmTo": round(TOTAL/1000, 1), "dist": round(TOTAL/1000, 1),
    "up": round(up), "down": round(dn), "hours": round(TOTAL/1000/3.7 + up/450, 1),
    "latlngs": [(round(c[1],6), round(c[0],6)) for c in coords],
}]

keep = [p for p in pois if p["off"] <= 1200 and p["cat"] != "?"]
for p in keep:
    t = p.pop("tags")
    p["sub"] = t.get("shelter_type") or t.get("tourism") or t.get("natural") or t.get("man_made") or t.get("shop") or t.get("amenity") or ""
    for k in ("opening_hours","description","note","phone","website","drinking_water","fee"):
        if t.get(k): p[k] = t[k]
    ph = photos.get(p["id"])
    if ph: p["photo"] = ph["thumb"]; p["photoPage"] = ph.get("page","")
    r = ratings.get(p["id"])
    if r:
        if r.get("rating") is not None: p["rating"] = r["rating"]
        if r.get("count") is not None: p["ratingCount"] = r["count"]
        if r.get("photo") and not p.get("photo"): p["photo"] = r["photo"]
        if r.get("hours") and not p.get("opening_hours"): p["opening_hours"] = r["hours"]

# jen start/cíl, žádné noclehy
DAYEND = [
    {"day": 1, "km": round(TOTAL/1000, 1),
     "lat": round(coords[-1][1], 6), "lon": round(coords[-1][0], 6),
     "name": "Cíl – Myjava, žel. st."},
]

out = {"total": round(TOTAL/1000,1), "days": days, "pois": keep, "profile": profile, "dayEnds": DAYEND}
with open("data.js","w") as f:
    f.write("const TREK = "); json.dump(out, f, ensure_ascii=False, separators=(",",":")); f.write(";\n")
import os
print(f"data.js: {os.path.getsize('data.js')//1024} KB | {TOTAL/1000:.1f} km | +{up:.0f}/-{dn:.0f} m | "
      f"{len(keep)} POIs | {sum(1 for p in keep if p.get('photo'))} photos | {sum(1 for p in keep if p.get('rating'))} rated")
