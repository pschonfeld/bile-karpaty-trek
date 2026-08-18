import json, math, urllib.request, urllib.parse, time

KEY = "R5Mv77riBsFzTqnOmEt6ay0pokzp4Pv2JwDm0ZEPCX8"
legs = json.load(open("data/route_legs.json"))
coords = []
for l in legs: coords += l["coords"]

def m_between(a, b):
    dx = (a[0]-b[0]) * 111320 * math.cos(math.radians((a[1]+b[1])/2))
    dy = (a[1]-b[1]) * 110540
    return math.hypot(dx, dy)

# sample every ~250 m
samples, acc = [(coords[0][0], coords[0][1], 0.0)], 0.0
km = 0.0
for p, q in zip(coords, coords[1:]):
    d = m_between(p, q); km += d; acc += d
    if acc >= 250: samples.append((q[0], q[1], km)); acc = 0
samples.append((coords[-1][0], coords[-1][1], km))
print(f"{len(samples)} elevation samples, {km/1000:.1f} km")

elevs = []
for i in range(0, len(samples), 150):
    chunk = samples[i:i+150]
    pos = ";".join(f"{lon:.6f},{lat:.6f}" for lon, lat, _ in chunk)
    url = "https://api.mapy.cz/v1/elevation?" + urllib.parse.urlencode({"positions": pos, "apikey": KEY})
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    elevs += [it["elevation"] for it in d["items"]]
    print(f"  chunk {i//150+1}: ok ({len(elevs)}/{len(samples)})")
    time.sleep(0.4)

profile = [{"km": round(s[2]/1000, 3), "ele": round(e, 1)} for s, e in zip(samples, elevs)]
json.dump(profile, open("data/elevation.json", "w"))

# ascent/descent per day boundaries
BOUNDS = [0, 18.8, 42.1, 63.4, 79.2, 999]
for i in range(5):
    seg = [p for p in profile if BOUNDS[i] <= p["km"] <= BOUNDS[i+1]]
    up = sum(max(0, b["ele"]-a["ele"]) for a, b in zip(seg, seg[1:]))
    dn = sum(max(0, a["ele"]-b["ele"]) for a, b in zip(seg, seg[1:]))
    print(f"Day {i+1}: {seg[0]['km']:.1f}-{seg[-1]['km']:.1f} km, +{up:.0f}m / -{dn:.0f}m, min {min(p['ele'] for p in seg):.0f} max {max(p['ele'] for p in seg):.0f}")
