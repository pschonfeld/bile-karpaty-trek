import json, math, urllib.request, urllib.parse, sys

legs = json.load(open("data/route_legs.json"))
coords = []
for l in legs:
    coords += l["coords"]  # [lon, lat]

def dist(a, b):
    dx = (a[0]-b[0]) * 111320 * math.cos(math.radians(a[1]))
    dy = (a[1]-b[1]) * 110540
    return math.hypot(dx, dy)

# downsample to ~400 m spacing for the corridor query
ds, acc = [coords[0]], 0
for p, q in zip(coords, coords[1:]):
    acc += dist(p, q)
    if acc >= 400: ds.append(q); acc = 0
ds.append(coords[-1])
poly = ",".join(f"{lat:.4f},{lon:.4f}" for lon, lat in ds)
print(f"corridor points: {len(ds)}", file=sys.stderr)

q = f"""[out:json][timeout:120];
(
  nwr["amenity"="shelter"](around:1500,{poly});
  nwr["tourism"~"^(wilderness_hut|alpine_hut)$"](around:1500,{poly});
  nwr["tourism"~"^(hotel|guest_house|hostel|chalet|camp_site|motel)$"](around:1500,{poly});
  nwr["amenity"="drinking_water"](around:1500,{poly});
  nwr["natural"="spring"](around:1500,{poly});
  nwr["man_made"~"^(water_well|water_tap)$"](around:1500,{poly});
  nwr["amenity"~"^(pub|restaurant|cafe|fast_food|biergarten)$"](around:1500,{poly});
  nwr["shop"~"^(convenience|supermarket|general|bakery|greengrocer)$"](around:1500,{poly});
);
out center tags;"""

req = urllib.request.Request("https://overpass-api.de/api/interpreter",
                             data=urllib.parse.urlencode({"data": q}).encode(),
                             headers={"User-Agent": "trek-planner/1.0"})
with urllib.request.urlopen(req, timeout=180) as r:
    data = json.load(r)

els = data["elements"]
json.dump(els, open("data/pois_raw.json", "w"))
from collections import Counter
cats = Counter()
for e in els:
    t = e.get("tags", {})
    key = t.get("amenity") or t.get("tourism") or t.get("natural") or t.get("man_made") or ("shop:"+t.get("shop","") if t.get("shop") else "?")
    cats[key] += 1
print(len(els), "POIs:", dict(cats))
