import json, urllib.request, urllib.parse, time, sys

KEY = "R5Mv77riBsFzTqnOmEt6ay0pokzp4Pv2JwDm0ZEPCX8"

# key waypoints along the ridge (lat, lon)
WPTS = [
    ("Púchov žst",        49.1132, 18.3276),
    ("Vršatec",           49.0660, 18.1509),
    ("Vlárský průsmyk",   49.0331, 18.0530),
    ("Chladný vrch",      49.0225, 18.0117),
    ("Mikulčin vrch",     48.9452, 17.8087),
    ("Veľký Lopeník",     48.9167, 17.7827),
    ("Veľká Javorina",    48.8577, 17.6757),
    ("Vrbovce žst",       48.8244, 17.5163),
    ("Myjava, železničná stanica", 48.7615, 17.5714),
]

def route(a, b, rtype):
    params = {
        "apikey": KEY, "lang": "cs", "format": "geojson",
        "start": f"{a[2]},{a[1]}", "end": f"{b[2]},{b[1]}",
        "routeType": rtype, "avoidToll": "false",
    }
    url = "https://api.mapy.cz/v1/routing/route?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode()[:500]); return None

legs = []
for a, b in zip(WPTS, WPTS[1:]):
    d = route(a, b, "foot_hiking")
    if d is None: sys.exit(1)
    legs.append({"from": a[0], "to": b[0], "length_m": d["length"], "duration_s": d["duration"],
                 "coords": d["geometry"]["geometry"]["coordinates"]})
    print(f"{a[0]} -> {b[0]}: {d['length']/1000:.1f} km, {d['duration']/3600:.1f} h, pts={len(legs[-1]['coords'])}")
    time.sleep(0.5)

total = sum(l["length_m"] for l in legs)
print(f"TOTAL: {total/1000:.1f} km")
json.dump(legs, open("data/route_legs.json", "w"))
