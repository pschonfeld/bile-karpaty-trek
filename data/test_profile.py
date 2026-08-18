import json, urllib.request, urllib.parse
KEY = "R5Mv77riBsFzTqnOmEt6ay0pokzp4Pv2JwDm0ZEPCX8"
# does foot_hiking exist? test on short leg + geocode ridge peaks for via points
def route(rtype):
    p = {"apikey": KEY, "format": "geojson", "start": "18.1509,49.0660", "end": "18.0530,49.0331", "routeType": rtype}
    try:
        with urllib.request.urlopen("https://api.mapy.cz/v1/routing/route?" + urllib.parse.urlencode(p), timeout=30) as r:
            d = json.load(r); return f"OK {d['length']/1000:.1f} km"
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()[:300]}"
for rt in ("foot_hiking", "foot_fast"):
    print(rt, "->", route(rt))
def geo(q):
    p = {"query": q, "limit": 3, "apikey": KEY, "lang": "cs", "type": "poi"}
    with urllib.request.urlopen("https://api.mapy.cz/v1/geocode?" + urllib.parse.urlencode(p), timeout=20) as r:
        for it in json.load(r).get("items", []):
            print(f"  {it['position']['lat']:.5f} {it['position']['lon']:.5f} | {it.get('name')} | {it.get('location','')}")
for q in ["Chmeľová vrch Vršatské bradlá", "Kykula vrch Biele Karpaty", "Veľký Kaňúr", "Chladný vrch Biele Karpaty", "Lachovec Púchov", "Megovka vrch"]:
    print("===", q); geo(q)
