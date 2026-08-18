import json, urllib.request, urllib.parse, time

KEY = "R5Mv77riBsFzTqnOmEt6ay0pokzp4Pv2JwDm0ZEPCX8"

def mapy_geocode(q):
    url = "https://api.mapy.cz/v1/geocode?" + urllib.parse.urlencode({"query": q, "limit": 3, "apikey": KEY, "lang": "cs"})
    with urllib.request.urlopen(url, timeout=20) as r:
        return json.load(r)

for q in ["Vrbovce železniční stanice", "Vršatec", "Chmeľová vrch Bílé Karpaty", "Mikulčin vrch"]:
    print("===", q)
    try:
        d = mapy_geocode(q)
        for it in d.get("items", []):
            print(f"  {it['position']['lat']:.5f} {it['position']['lon']:.5f} | {it.get('name')} | {it.get('label')} | {it.get('location','')}")
    except Exception as e:
        print("  ERROR", e)
    time.sleep(0.5)
