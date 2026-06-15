# Snake Photo Assessment

- Endpoint: `http://192.168.86.76:7860`
- Run at: `2026-06-15T08:04:55.059829+00:00`
- Passed: `8/8`

| # | Expected | Backend | Risk | Candidate labels | Assessment | Source photo |
|---:|---|---|---|---|---|---|
| 1 | red-bellied black snake | llama.cpp mtmd | critical | vision candidate: snake or snake-like animal possible red-bellied black snake curl snake | exact | [iNaturalist](https://www.inaturalist.org/observations/258009187) |
| 2 | eastern brown snake | llama.cpp mtmd | critical | vision candidate: unknown snake unknown snake witchetty grub | hazard | [iNaturalist](https://www.inaturalist.org/observations/244568885) |
| 3 | western brown snake | llama.cpp mtmd | critical | vision candidate: unknown field subject possible snake or snake-like animal dugite | hazard | [iNaturalist](https://www.inaturalist.org/observations/109727189) |
| 4 | tiger snake | llama.cpp mtmd | critical | vision candidate: python-like snake python-like snake unknown snake rough-scaled snake | hazard | [iNaturalist](https://www.inaturalist.org/observations/62189468) |
| 5 | yellow-bellied sea snake | llama.cpp mtmd | critical | vision candidate: unknown snake possible marine hazard unknown snake mouse spider | hazard | [iNaturalist](http://www.inaturalist.org/observations/2212624) |
| 6 | coastal taipan | llama.cpp mtmd | critical | vision candidate: snake or snake-like animal mouse spider | hazard | [iNaturalist](https://www.inaturalist.org/observations/183968856) |
| 7 | common death adder | llama.cpp mtmd | critical | vision candidate: unknown snake unknown snake moray eel | hazard | [iNaturalist](https://www.inaturalist.org/observations/274166643) |
| 8 | carpet python | llama.cpp mtmd | critical | vision candidate: python-like snake python-like snake unknown snake moray eel | exact | [iNaturalist](https://www.inaturalist.org/observations/72514657) |

## Notes

### 1. red-bellied black snake

- Vision: `[]` confidence `low`
- Species classifier: `['curl snake']` confidence `low`
- Guardrail: `-`
- Attribution: (c) David Sinnott, some rights reserved (CC BY-NC)

### 2. eastern brown snake

- Vision: `['unknown snake']` confidence `high`
- Species classifier: `['witchetty grub']` confidence `low`
- Guardrail: `-`
- Attribution: (c) Ellura Sanctuary, some rights reserved (CC BY-NC)

### 3. western brown snake

- Vision: `[]` confidence `low`
- Species classifier: `['dugite']` confidence `low`
- Guardrail: `-`
- Attribution: (c) camille_caparros, some rights reserved (CC BY-NC)

### 4. tiger snake

- Vision: `['python-like snake', 'unknown snake']` confidence `high`
- Species classifier: `['rough-scaled snake']` confidence `low`
- Guardrail: `-`
- Attribution: (c) Dustyn and Catherine, some rights reserved (CC BY-NC)

### 5. yellow-bellied sea snake

- Vision: `['unknown snake']` confidence `low`
- Species classifier: `['mouse spider']` confidence `low`
- Guardrail: `-`
- Attribution: (c) NHMLA Community Science Program, some rights reserved (CC BY-NC)

### 6. coastal taipan

- Vision: `[]` confidence `low`
- Species classifier: `['mouse spider']` confidence `low`
- Guardrail: `-`
- Attribution: (c) grounding-in-nature, some rights reserved (CC BY-NC)

### 7. common death adder

- Vision: `['unknown snake']` confidence `high`
- Species classifier: `['moray eel']` confidence `low`
- Guardrail: `-`
- Attribution: (c) Aidan Jackson-Kightly, some rights reserved (CC BY-NC)

### 8. carpet python

- Vision: `['python-like snake', 'unknown snake']` confidence `medium`
- Species classifier: `['moray eel']` confidence `low`
- Guardrail: `-`
- Attribution: (c) Dion Maple, some rights reserved (CC BY-NC)
