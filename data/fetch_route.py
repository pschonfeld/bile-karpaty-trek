import json, urllib.request, urllib.parse, time, sys

KEY = "R5Mv77riBsFzTqnOmEt6ay0pokzp4Pv2JwDm0ZEPCX8"

# key waypoints along the ridge (lat, lon)
WPTS = [
    ("Púchov žst",          49.113163, 18.327635),
    ("Chmeľová",            49.073868, 18.154311),
    ("Vršatské Podhradie",  49.064913, 18.153845),
    ("Veľká Javorina",      48.8577,   17.6757),
    ("Myjava",              48.763770, 17.570920),
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
