# Přechod Bílých Karpat · Púchov → Vrbovce žel. st.

Interaktivní plánovač 4,5denního přechodu po červené hřebenovce (Cesta hrdinov SNP / E8),
st 19. 8. – ne 23. 8. 2026. Celkem **96,3 km**, ↑3491 m / ↓3341 m (pěší turistický profil Mapy.cz, vedeno po hřebeni).

## Spuštění
Aplikace je statická – stačí naservírovat adresář:
```
python3 -m http.server 8741 --directory .
```
a otevřít http://localhost:8741. (Otevření `index.html` přímo souborem funguje také,
jen některé prohlížeče blokují lokální `data.js` – server je spolehlivější.)

## Etapy
| Den | Úsek | km | ↑ / ↓ | Nocleh |
|---|---|---|---|---|
| St 19. 8. | Púchov žst → Vršatec | 19,3 | +1124/−655 | přístřešky u Vršatce (útulna „Domček“ km 16,4 jako alternativa) |
| Čt 20. 8. | Vršatec → útulna za Chladným vrchem (přes Vlárský průsmyk) | 25,8 | +614/−631 | útulna s ohništěm přímo na trase (km 45,1) |
| Pá 21. 8. | → Veľký Lopeník (Starý Hrozenkov: obchod; Mikulčin vrch: restaurace) | 21,7 | +849/−609 | přístřešek pod rozhlednou (km 66,8) |
| So 22. 8. | → přes Veľkou Javorinu (Holubyho chata) | 16,2 | +804/−735 | přístřešek na hřebeni (km 83,0) |
| Ne 23. 8. | → Vrbovce, žel. st. | 13,3 | +100/−711 | vlak (trať Veselí n. Mor. – Myjava) |

## Data a limity
- **Trasa**: Mapy.cz routing API, profil `foot_hiking` (preferuje značené trasy), vedená přes hřebenové body – v terénu se držte
  červené značky, routing se od ní může místy drobně lišit.
- **POI**: OpenStreetMap (Overpass), koridor ±1,2 km. Stav přístřešků a pitnost pramenů
  neověřena – berte jako pravděpodobná, ne garantovaná místa.
- **API klíč Mapy.cz** je v `index.html` (`MAPY_KEY`) – klientský klíč, limit 250k dlaždic/měsíc.
- **Fotky**: OSM tag `image`/`wikimedia_commons` + Wikimedia Commons geosearch (34 bodů).
- **Hodnocení hospod**: veřejné API Mapy.cz hodnocení neposkytuje – v detailu bodu je odkaz
  na Mapy.com, kde je hodnocení i fotky.
- `data/` obsahuje stahovací a build skripty (`fetch_route.py`, `fetch_pois.py`,
  `fetch_elev.py`, `fetch_photos.py`, `process.py`, `build_data.py`) – po úpravě trasy spusťte v tomto pořadí.

## Než vyrazíte
- Exportujte **GPX** tlačítkem v aplikaci a nahrajte do mobilu/hodinek.
- V mobilní aplikaci Mapy.cz si stáhněte **offline mapu** Bílých Karpat – na hřebeni je slabý signál.
- Ověřte jízdní řád vlaku z Vrbovců na nedělní odpoledne.
