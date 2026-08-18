# Hodnocení z Mapy.com — jak to funguje

Oficiální veřejné API (api.mapy.cz: geocode/suggest/routing/elevation) hodnocení
**neposkytuje** — ověřeno inspekcí všech polí odpovědi `/v1/suggest`.

`data/fetch_ratings.py` proto používá dva **neoficiální** endpointy webového
frontendu mapy.com (zjištěno inspekcí síťového provozu v prohlížeči):

1. `GET https://mapy.com/api/suggest/?phrase=…&lon=…&lat=…` — JSON vyhledávání
   míst s interním `source` + `id` (mapy.com čísluje vlastní databázi, ne OSM).
2. `POST https://mapy.com/api/poiagg` — binární protokol FRPC (Seznam FastRPC,
   magic `0xCA 0x11`), metoda `detail` vrací strukturu `review`
   (`review_rating_stars`, `total`, `use_rating`) a `gallery` s URL fotek.
   Skript obsahuje minimální FRPC kodek (encode/decode) v čistém Pythonu.

Oba endpointy fungují bez autentizace, stačí User-Agent. Párování OSM → mapy.com:
suggest s biasem na souřadnice, kandidáti do 150 m, fuzzy shoda jména (difflib,
práh 0,45). Bez shody nebo bez hodnocení (`use_rating=false`) se bod vynechává —
nic se nedopočítává.

## Pokrytí (běh 18. 8. 2026)

- 98 pojmenovaných POI (hospody, ubytování, přístřešky/chaty)
- 81 spárováno s mapy.com
- **27 s hodnocením** (vč. fotky ze Seznam CDN `sdn.cz`) → `data/ratings.json`
- zbytek: vesnické hospody a přístřešky bez recenzí na mapy.com

## Upozornění

Neoficiální endpointy se mohou kdykoli změnit nebo rozbít; jde o jednorázový
build-time fetch v malém objemu (~200 requestů s 0,3s rozestupy), ne o runtime
závislost aplikace. Při rozbití prostě zmizí hvězdičky, aplikace běží dál.
