import json, math

legs = json.load(open("data/route_legs.json"))
els  = json.load(open("data/pois_raw.json"))

coords = []
for l in legs: coords += l["coords"]

def m_between(a, b):
    dx = (a[0]-b[0]) * 111320 * math.cos(math.radians((a[1]+b[1])/2))
    dy = (a[1]-b[1]) * 110540
    return math.hypot(dx, dy)

# cumulative km, downsampled index every ~100 m for POI matching
cum = [0.0]
for p, q in zip(coords, coords[1:]): cum.append(cum[-1] + m_between(p, q))
TOTAL = cum[-1]

idx = []  # (lon, lat, km)
last = -1e9
for c, k in zip(coords, cum):
    if k - last >= 100: idx.append((c[0], c[1], k)); last = k

def locate(lat, lon):
    best = min(idx, key=lambda t: m_between((t[0], t[1]), (lon, lat)))
    return best[2]/1000, m_between((best[0], best[1]), (lon, lat))

def cat(t):
    if t.get("amenity") == "shelter" or t.get("tourism") in ("wilderness_hut", "alpine_hut"):
        if (t.get("shelter_type") in ("basic_hut", "building")
                or t.get("tourism") in ("wilderness_hut", "alpine_hut")
                or t.get("walls") == "yes"):
            return "hut"       # útulna / chata (uzavíratelná)
        return "shelter"       # otevřený přístřešek
    if t.get("tourism") in ("hotel","guest_house","hostel","chalet","camp_site","motel"): return "lodging"
    if t.get("amenity") == "drinking_water" or t.get("natural") == "spring" or t.get("man_made") in ("water_well","water_tap"): return "water"
    if t.get("amenity") in ("pub","restaurant","cafe","fast_food","biergarten"): return "food"
    if t.get("shop"): return "shop"
    return "?"

pois = []
for e in els:
    t = e.get("tags", {})
    lat = e.get("lat") or e.get("center", {}).get("lat")
    lon = e.get("lon") or e.get("center", {}).get("lon")
    if lat is None: continue
    km, off = locate(lat, lon)
    pois.append({"id": f'{e["type"]}/{e["id"]}', "lat": round(lat,6), "lon": round(lon,6),
                 "cat": cat(t), "km": round(km,2), "off": round(off),
                 "name": t.get("name",""), "tags": t})
json.dump(pois, open("data/pois.json","w"), ensure_ascii=False)

print(f"TOTAL {TOTAL/1000:.1f} km\n--- SHELTERS by km (off<=1200m) ---")
for p in sorted(pois, key=lambda p: p["km"]):
    if p["cat"]=="shelter" and p["off"]<=1200:
        t=p["tags"]
        print(f'km {p["km"]:6.1f} +{p["off"]:4d}m | {p["name"] or "(bez názvu)"} | type={t.get("shelter_type","?")} walls={t.get("walls","?")} fp={t.get("fireplace","?")}')
print("--- LODGING ---")
for p in sorted(pois, key=lambda p: p["km"]):
    if p["cat"]=="lodging" and p["off"]<=1500:
        print(f'km {p["km"]:6.1f} +{p["off"]:4d}m | {p["name"]} | {p["tags"].get("tourism")}')
