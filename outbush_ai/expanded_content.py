from __future__ import annotations

from typing import Any


def build_expanded_knowledge(source_cls: Any, item_cls: Any, retrieved_date: str) -> tuple[Any, ...]:
    sources = _sources(source_cls, retrieved_date)
    items: list[Any] = []
    items.extend(_park_items(item_cls, sources["parks"]))
    items.extend(_ranger_tip_items(item_cls, sources["nsw_ranger"]))
    items.extend(_species_items(item_cls, sources))
    items.extend(_cloud_items(item_cls, sources["bom_clouds"]))
    return tuple(items)


def _sources(source_cls: Any, retrieved_date: str) -> dict[str, Any]:
    return {
        "parks": source_cls(
            "Compiled official park and Tourism Australia visitor notes",
            "https://www.australia.com/en/things-to-do/nature-and-national-parks/national-parks-australia.html",
            retrieved_date,
            "Australia",
            "parks",
        ),
        "nsw_ranger": source_cls(
            "NSW National Parks - Ranger tips",
            "https://www.nationalparks.nsw.gov.au/get-inspired/categories/ranger-tips",
            retrieved_date,
            "NSW / Australia",
            "preparedness",
        ),
        "museum_danger": source_cls(
            "Australian Museum - Dangerous animals",
            "https://australian.museum/learn/animals/dangerous-animals/",
            retrieved_date,
            "Australia",
            "wildlife",
        ),
        "inat": source_cls(
            "iNaturalist licensed observation training pool",
            "https://www.inaturalist.org/",
            retrieved_date,
            "Australia",
            "wildlife",
        ),
        "healthdirect": source_cls(
            "Healthdirect - bites, stings, poisoning and first aid",
            "https://www.healthdirect.gov.au/",
            retrieved_date,
            "Australia",
            "first_aid",
        ),
        "bom_clouds": source_cls(
            "Bureau of Meteorology - Cloud types and weather",
            "https://www.bom.gov.au/weather-services/about/cloud/cloud-types.shtml",
            retrieved_date,
            "Australia",
            "weather",
        ),
        "bush_food": source_cls(
            "Australian bush food field safety notes",
            "https://www.anbg.gov.au/gardens/education/programs/pdfs/aboriginal_plant_use_and_technology.pdf",
            retrieved_date,
            "Australia",
            "bush_tucker",
        ),
        "fungi": source_cls(
            "NSW Health - wild mushroom safety",
            "https://www.health.nsw.gov.au/environment/factsheets/Pages/wild-mushroom-poisoning.aspx",
            retrieved_date,
            "Australia",
            "fungi",
        ),
    }


PARKS: tuple[dict[str, str], ...] = (
    {"name": "Uluru-Kata Tjuta National Park", "region": "Red Centre, NT", "landscape": "desert rock domes, exposed tracks and sacred Anangu cultural landscapes", "hazards": "heat, exposure, limited shade and long emergency response times"},
    {"name": "Kakadu National Park", "region": "Top End, NT", "landscape": "floodplains, billabongs, stone country, monsoon forest and rock art", "hazards": "crocodiles, heat, storms, seasonal flooding and road closures"},
    {"name": "Ikara-Flinders Ranges National Park", "region": "Flinders Ranges, SA", "landscape": "ancient ranges, gorges, pound country and arid woodland", "hazards": "heat, dehydration, rough rocky tracks and sudden cold nights"},
    {"name": "Daintree National Park", "region": "Wet Tropics, QLD", "landscape": "lowland rainforest, creek crossings, mangrove edges and cassowary habitat", "hazards": "crocodile country, stinging trees, leeches, heat and slippery roots"},
    {"name": "Blue Mountains National Park", "region": "Greater Sydney, NSW", "landscape": "sandstone cliffs, waterfalls, stairs, gullies and eucalyptus forest", "hazards": "cliff edges, cold changes, slippery tracks, creek rises and navigation traps"},
    {"name": "Cradle Mountain-Lake St Clair National Park", "region": "Tasmanian Wilderness, TAS", "landscape": "alpine lakes, button grass, rainforest pockets and exposed passes", "hazards": "hypothermia, snow, wind, whiteout, mud and long remote legs"},
    {"name": "Freycinet National Park", "region": "East Coast, TAS", "landscape": "granite peaks, beaches, dry forest and coastal heath", "hazards": "heat, limited water, cliff edges, snakes and exposed coastal weather"},
    {"name": "Purnululu National Park", "region": "Kimberley, WA", "landscape": "beehive sandstone domes, gorges and remote savanna", "hazards": "extreme heat, flash flooding, remote roads and limited water"},
    {"name": "Flinders Chase National Park", "region": "Kangaroo Island, SA", "landscape": "coastal cliffs, mallee, rocky headlands, seals and wind-shaped granite", "hazards": "cliff exposure, surf, bushfire weather and remote road access"},
    {"name": "Karijini National Park", "region": "Pilbara, WA", "landscape": "deep red gorges, waterfalls, pools and spinifex ranges", "hazards": "heat, flash flooding, gorge scrambling, slippery rock and remote help"},
    {"name": "Grampians (Gariwerd) National Park", "region": "Western Victoria, VIC", "landscape": "sandstone ranges, waterfalls, rock art and dry forest", "hazards": "cliffs, snakes, bushfire weather, storms and steep tracks"},
    {"name": "Royal National Park", "region": "Sydney, NSW", "landscape": "coastal cliffs, heath, beaches, rainforest gullies and sandstone tracks", "hazards": "surf, cliff edges, heat, track crowding and sudden southerly changes"},
    {"name": "Kosciuszko National Park", "region": "Snowy Mountains, NSW", "landscape": "alpine plains, snow gums, high peaks, rivers and subalpine huts", "hazards": "cold exposure, storms, snow, navigation issues and fast weather changes"},
    {"name": "Wilson's Promontory National Park", "region": "Gippsland, VIC", "landscape": "granite headlands, beaches, heath, forest and tidal flats", "hazards": "cold wind, surf, tides, snakes and long exposed walks"},
    {"name": "Noosa National Park", "region": "Sunshine Coast, QLD", "landscape": "coastal forest, rocky headlands, beaches and koala habitat", "hazards": "heat, surf, cliff edges, crowds and track erosion"},
    {"name": "Lamington National Park", "region": "Scenic Rim, QLD", "landscape": "subtropical rainforest, waterfalls, ridges and Antarctic beech", "hazards": "stinging trees, leeches, slippery roots, creek rises and poor visibility"},
    {"name": "Springbrook National Park", "region": "Gold Coast Hinterland, QLD", "landscape": "rainforest plateau, waterfalls, glowworm caves and escarpment lookouts", "hazards": "cliffs, wet rock, storms, leeches and sudden fog"},
    {"name": "Great Sandy National Park", "region": "K'gari and Cooloola, QLD", "landscape": "sand islands, lakes, dunes, beaches and coastal forest", "hazards": "dingoes, soft sand driving, surf, tides, heat and limited freshwater"},
    {"name": "Whitsunday Islands National Park", "region": "Central Queensland coast, QLD", "landscape": "islands, beaches, coral-fringed waters and dry tropical forest", "hazards": "marine stingers, sun exposure, tides, dehydration and boat weather"},
    {"name": "Kalbarri National Park", "region": "Mid West, WA", "landscape": "Murchison River gorges, coastal cliffs, wildflowers and red rock", "hazards": "heat, cliff edges, long exposed walks and flash flooding"},
    {"name": "Nambung National Park", "region": "Coral Coast, WA", "landscape": "Pinnacles limestone desert, coastal heath and dunes", "hazards": "heat, exposure, limited shade, snakes and remote roads"},
    {"name": "Cape Le Grand National Park", "region": "Esperance, WA", "landscape": "white beaches, granite peaks, heathland and turquoise bays", "hazards": "cold water, surf, wind, snakes and exposed granite"},
    {"name": "Stirling Range National Park", "region": "Great Southern, WA", "landscape": "rugged peaks, wildflowers and montane heath", "hazards": "rapid weather shifts, cold, steep rock, wind and poor visibility"},
    {"name": "Warrumbungle National Park", "region": "Central West, NSW", "landscape": "volcanic spires, dry woodland, observatory country and long ridges", "hazards": "heat, storms, steep tracks, loose rock and limited water"},
    {"name": "Wollemi National Park", "region": "Greater Blue Mountains, NSW", "landscape": "wild sandstone canyons, pagodas, forests and remote rivers", "hazards": "navigation difficulty, cliffs, canyon floods, cold water and remoteness"},
    {"name": "Budawang National Park", "region": "South Coast hinterland, NSW", "landscape": "remote sandstone plateaus, rainforest gullies and rugged peaks", "hazards": "navigation, exposure, cliffs, creek rises and slow rescue access"},
    {"name": "Kanangra-Boyd National Park", "region": "Central Tablelands, NSW", "landscape": "high plateaus, deep gorges, cliffs and wilderness routes", "hazards": "cliffs, cold, navigation, scrub, fires and remote walking"},
    {"name": "Ku-ring-gai Chase National Park", "region": "Northern Sydney, NSW", "landscape": "Hawkesbury sandstone, waterways, Aboriginal sites and dry forest", "hazards": "heat, cliffs, tides, snakes and navigation off track"},
    {"name": "Murramarang National Park", "region": "South Coast, NSW", "landscape": "spotted gum forest, beaches, headlands and kangaroo lawns", "hazards": "surf, tides, ticks, snakes and falling branches"},
    {"name": "Myall Lakes National Park", "region": "Mid North Coast, NSW", "landscape": "coastal lakes, dunes, beaches, paperbark and rainforest pockets", "hazards": "mosquitoes, water crossings, surf, storms and soft sand"},
    {"name": "Dorrigo National Park", "region": "Northern Tablelands, NSW", "landscape": "World Heritage rainforest, waterfalls and escarpment tracks", "hazards": "slippery roots, leeches, stinging plants, creek rises and fog"},
    {"name": "Booderee National Park", "region": "Jervis Bay Territory", "landscape": "white beaches, heath, botanic gardens and coastal forest", "hazards": "surf, sun, snakes, ticks and fragile cultural/natural sites"},
    {"name": "Mungo National Park", "region": "Willandra Lakes, NSW", "landscape": "lunette dunes, ancient lakebeds and arid cultural landscapes", "hazards": "heat, remoteness, dust, fragile heritage surfaces and limited water"},
    {"name": "Namadgi National Park", "region": "ACT high country", "landscape": "granite peaks, snow gum woodland, alpine bogs and heritage huts", "hazards": "cold, snow, bushfire weather, navigation and rapid fronts"},
    {"name": "Litchfield National Park", "region": "Top End, NT", "landscape": "waterfalls, monsoon forest, magnetic termite mounds and plunge pools", "hazards": "crocodiles in waterways, heat, storms, slippery rock and seasonal closures"},
    {"name": "Nitmiluk National Park", "region": "Katherine, NT", "landscape": "sandstone gorges, river country, waterfalls and escarpment walks", "hazards": "heat, crocodiles, flash floods, remote tracks and limited shade"},
    {"name": "Tjoritja / West MacDonnell National Park", "region": "Central Australia, NT", "landscape": "gorges, waterholes, ridges and desert ranges", "hazards": "heat, dehydration, flash flooding, cold nights and remote road legs"},
    {"name": "Munga-Thirri National Park", "region": "Simpson Desert, QLD", "landscape": "parallel dunes, salt pans and remote arid country", "hazards": "extreme heat, isolation, vehicle failure, no water and satellite-only comms"},
    {"name": "Carnarvon National Park", "region": "Central Queensland, QLD", "landscape": "sandstone gorge, palms, creek crossings and rock art", "hazards": "heat, creek rises, slippery rocks, snakes and remote access"},
    {"name": "Mount Barney National Park", "region": "Scenic Rim, QLD", "landscape": "steep volcanic peaks, rainforest gullies and remote ridges", "hazards": "falls, navigation, exposure, storms and difficult rescue"},
    {"name": "Conondale National Park", "region": "Sunshine Coast Hinterland, QLD", "landscape": "rainforest, waterfalls, creeks and wet sclerophyll forest", "hazards": "leeches, creek crossings, slippery roots, storms and track washouts"},
    {"name": "Girraween National Park", "region": "Granite Belt, QLD", "landscape": "granite domes, balancing rocks, wildflowers and open woodland", "hazards": "exposed rock, heat, storms, snakes and cold winter nights"},
    {"name": "Mount Field National Park", "region": "Derwent Valley, TAS", "landscape": "waterfalls, tall forest, alpine tarns and snow gums", "hazards": "cold, snow, wet tracks, tree fall and fast weather changes"},
    {"name": "Southwest National Park", "region": "Tasmanian Wilderness, TAS", "landscape": "remote mountains, buttongrass plains, rainforest and wild coast", "hazards": "hypothermia, navigation, river crossings, mud and severe remoteness"},
    {"name": "Walls of Jerusalem National Park", "region": "Tasmanian highlands, TAS", "landscape": "alpine lakes, dolerite peaks, pencil pine and pad routes", "hazards": "whiteout, cold, navigation, snow and fragile alpine vegetation"},
    {"name": "Narawntapu National Park", "region": "North Tasmania, TAS", "landscape": "coastal heath, lagoons, beaches and grasslands with wildlife", "hazards": "snakes, tides, cold water, wind and ticks"},
    {"name": "Port Campbell National Park", "region": "Great Ocean Road, VIC", "landscape": "limestone cliffs, sea stacks, arches and surf coast", "hazards": "cliff edges, unstable rock, surf, wind and sudden weather"},
    {"name": "Alpine National Park", "region": "Victorian High Country, VIC", "landscape": "high plains, snow gums, ridges, rivers and hut country", "hazards": "cold, snow, fire weather, navigation and long remote tracks"},
    {"name": "Croajingolong National Park", "region": "East Gippsland, VIC", "landscape": "coast, heath, rainforest gullies, inlets and remote beaches", "hazards": "tides, surf, creek crossings, ticks, snakes and fire weather"},
    {"name": "Murray-Sunset National Park", "region": "Mallee, VIC", "landscape": "salt lakes, mallee scrub, dunes and remote semi-arid tracks", "hazards": "heat, isolation, soft sand, limited water and navigation"},
)


RANGER_TIPS: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    ("Trip intentions", "Leave route, party, vehicle and return-time details with someone reliable; set a clear escalation time before reception drops.", ("ranger tips", "trip intentions", "emergency"), "high"),
    ("Multi-day pack weight", "For overnight walks, test pack weight on a shorter local walk and remove nice-to-have items before committing to remote terrain.", ("ranger tips", "multi-day", "gear"), "normal"),
    ("Boot and foot check", "Break in footwear, carry blister care, and stop early for hot spots; small foot problems become big route problems with a heavy pack.", ("ranger tips", "boots", "blisters"), "normal"),
    ("Layering plan", "Pack sun, rain and warm layers together even for mild starts; Australian fronts and tableland weather can flip quickly.", ("ranger tips", "layers", "weather"), "normal"),
    ("Water discipline", "Know water points before leaving service, carry treatment, and assume creeks may be dry unless recent reliable reports say otherwise.", ("ranger tips", "water", "planning"), "high"),
    ("Turnaround time", "Set a turnaround time before the walk starts; tired groups often keep going because the destination feels close.", ("ranger tips", "navigation", "fatigue"), "normal"),
    ("Visitor centre first stop", "For unfamiliar parks, check visitor centres or official pages for closures, track damage, pest notices and local hazard changes.", ("ranger tips", "visitor centre", "closures"), "normal"),
    ("Injured wildlife", "Do not handle injured wildlife unless directed by trained rescue staff; keep distance, note location and contact local wildlife rescue or rangers.", ("ranger tips", "wildlife", "rescue"), "high"),
    ("Cultural place names", "Place names can carry cultural and landscape knowledge; use official names respectfully and avoid disturbing cultural sites.", ("ranger tips", "culture", "place names"), "normal"),
    ("Magpie season", "If swooped, move calmly away, protect eyes, keep helmets or hats on where needed, and avoid re-entering a nesting zone.", ("ranger tips", "magpie", "wildlife"), "normal"),
    ("Track closure respect", "Closed tracks may hide fire damage, landslips, flood damage or cultural protection needs; do not bypass barriers.", ("ranger tips", "closures", "track"), "high"),
    ("Camp hygiene", "Store food sealed, keep camps clean and never feed wildlife; habituated animals become risky for people and unhealthy for themselves.", ("ranger tips", "camp", "wildlife"), "normal"),
    ("Creek crossing rule", "If a creek is rising, discoloured, fast or above knees, wait or turn back; upstream rain can arrive before local rain does.", ("ranger tips", "creek", "flood"), "high"),
    ("Storm timing", "On ridge, beach or escarpment walks, leave exposed places early if thunderheads build, wind shifts or thunder is heard.", ("ranger tips", "storm", "lightning"), "high"),
    ("Heat start time", "For hot regions, start early, rest in shade and avoid pushing through the middle of the day; heat illness can impair judgement.", ("ranger tips", "heat", "hydration"), "high"),
    ("Dog restrictions", "Check rules before bringing dogs; many national parks prohibit pets to protect wildlife and reduce disease or baiting risk.", ("ranger tips", "dogs", "park rules"), "normal"),
    ("Leave no trace", "Pack out rubbish, stay on hardened surfaces and avoid shortcutting switchbacks; fragile soils and alpine plants recover slowly.", ("ranger tips", "leave no trace", "tracks"), "normal"),
    ("Nightfall margin", "Carry a head torch even on day walks; stairs, creek crossings and indistinct tracks are much harder after sunset.", ("ranger tips", "head torch", "day walk"), "normal"),
    ("Phone battery", "Airplane mode, offline maps and a power bank extend phone usefulness; do not rely on coverage as the emergency plan.", ("ranger tips", "phone", "offline maps"), "normal"),
    ("PLB decision", "For remote or solo routes, carry a registered PLB or satellite messenger and know how to activate it.", ("ranger tips", "plb", "solo"), "high"),
    ("Group pacing", "Walk at the pace of the slowest person, regroup at junctions and never let someone drift off alone when tired.", ("ranger tips", "group", "fatigue"), "normal"),
    ("Rock shelf caution", "Keep well back from wet coastal rock shelves; waves can surge higher than the previous set.", ("ranger tips", "coast", "waves"), "high"),
    ("Cliff edge margin", "Treat cliff edges as unstable even behind photos; wind gusts, loose rock and distraction make edges unforgiving.", ("ranger tips", "cliffs", "lookout"), "high"),
    ("Snake encounter", "Stop, give the snake space and let it move away; most bites occur when people try to handle, kill or closely inspect snakes.", ("ranger tips", "snake", "wildlife"), "critical"),
    ("Tick check", "In humid forest or grassy camps, check clothing and skin after the walk and monitor allergic reactions or illness.", ("ranger tips", "ticks", "bites"), "normal"),
    ("Leech management", "Leeches are unpleasant but usually manageable; remove gently, clean the area and watch for infection or allergy.", ("ranger tips", "leeches", "rainforest"), "normal"),
    ("Fire danger", "Check fire danger and park fire bans before departure; offline tools cannot know fast-changing fire behaviour.", ("ranger tips", "fire", "closures"), "high"),
    ("Flooded roads", "Do not drive or walk through floodwater; depth, current and road damage are hard to judge.", ("ranger tips", "flood", "roads"), "critical"),
    ("Waterfall rocks", "Wet rock around waterfalls is often algae-slick; stay behind barriers and avoid climbing for photos.", ("ranger tips", "waterfall", "slip"), "high"),
    ("Rock art respect", "Do not touch, chalk, wet, climb on or photograph restricted cultural sites; follow local signs and guidance.", ("ranger tips", "culture", "rock art"), "normal"),
    ("Remote driving", "Tell someone road plans, fuel range and recovery gear; many park incidents begin before the walk starts.", ("ranger tips", "remote driving", "vehicle"), "high"),
    ("Food identification", "Treat bush tucker notes as cultural and ecological learning; do not harvest or eat without local permission and expert ID.", ("ranger tips", "bush tucker", "foraging"), "high"),
    ("Photo identification", "Use photo ID as a candidate hint, not proof of safety. If risk is possible, keep distance and choose the cautious pathway.", ("ranger tips", "photo", "identification"), "high"),
    ("Kids on track", "Put an adult at front and back, stop at every junction and keep children away from cliff, water and snake habitat edges.", ("ranger tips", "children", "group"), "normal"),
    ("Post-walk check-in", "Notify your contact when finished; otherwise they may raise an alarm on the agreed escalation time.", ("ranger tips", "check in", "emergency"), "normal"),
)


SNAKES = (
    "yellow-bellied sea snake", "red-bellied black snake", "eastern brown snake", "western brown snake", "tiger snake", "coastal taipan", "inland taipan", "mulga snake", "common death adder", "desert death adder", "northern death adder", "lowlands copperhead", "highlands copperhead", "small-eyed snake", "rough-scaled snake", "Stephen's banded snake", "dugite", "spotted black snake", "curl snake", "whip snake", "marsh snake", "golden-crowned snake", "carpet python", "black-headed python", "green tree snake", "olive python",
)

SPIDERS = (
    "Sydney funnel-web spider", "northern tree funnel-web spider", "mouse spider", "redback spider", "white-tailed spider", "huntsman spider", "wolf spider", "trapdoor spider", "garden orb-weaver", "St Andrew's cross spider",
)

MARINE = (
    "blue-ringed octopus", "reef stonefish", "bullrout", "box jellyfish", "Irukandji jellyfish", "bluebottle", "cone shell", "stingray", "yellow-bellied sea snake", "long-spined sea urchin",
)

PLANTS = (
    "gympie-gympie stinging tree", "giant stinging tree", "stinging nettle", "lawyer vine", "spinifex", "speargrass", "lantana", "oleander", "castor oil plant", "fireweed", "foxglove", "bracken fern", "black bean tree", "mangrove", "pigface", "banksia", "wattle", "eucalypt", "grass tree", "bunya pine",
)

BUSH_TUCKER = (
    "witchetty grub", "quandong", "finger lime", "lemon myrtle", "warrigal greens", "bunya nut", "macadamia", "native raspberry", "bush tomato", "Kakadu plum",
)

MUSHROOMS = (
    "death cap mushroom", "yellow-staining mushroom", "ghost fungus", "fly agaric", "green-spored parasol", "earthball fungus", "coral fungus", "puffball lookalikes", "saffron milk cap", "slippery jack",
)

CLOUDS = (
    ("cumulonimbus", "towering cloud with dark base and possible anvil; indicates thunderstorms, lightning, hail, heavy rain or flash flood potential"),
    ("cumulus congestus", "rapidly growing cauliflower towers; can become thunderstorms if lift and moisture continue"),
    ("anvil cloud", "flat spreading top from a mature storm; lightning and gust fronts may extend away from rain"),
    ("shelf cloud", "low wedge at storm front; can signal strong gusts and sudden wind shift"),
    ("mammatus", "pouch-like cloud under an anvil; often near severe thunderstorm environments"),
    ("wall cloud", "lowering under a storm base; a sign to leave exposed areas and monitor official warnings"),
    ("nimbostratus", "thick grey rain layer; expect persistent rain, poor visibility and creek-rise risk"),
    ("altostratus", "mid-level grey sheet; can precede widespread rain or frontal weather"),
    ("cirrus", "high wispy ice cloud; may mark approaching weather changes over the next day"),
    ("lenticular cloud", "lens-shaped cloud near ranges; can indicate strong winds and mountain wave conditions"),
    ("fog and low stratus", "ground-hugging cloud; causes navigation, road and cliff-edge visibility hazards"),
    ("virga", "rain streaks evaporating before the ground; can signal dry gust fronts and changing wind"),
)


def _park_items(item_cls: Any, source: Any) -> list[Any]:
    items: list[Any] = []
    for index, park in enumerate(PARKS, start=1):
        key = _slug(park["name"])
        tags = ("national park", "top 50 parks", park["region"].lower(), key.replace("_", " "))
        items.append(item_cls(
            f"park_{index:02d}_{key}_overview",
            f"{park['name']} field overview",
            f"{park['name']} in {park['region']} is known for {park['landscape']}. Use it as a regional context card for landscape, walking style and likely field questions.",
            source,
            tags + ("overview",),
            "normal",
        ))
        items.append(item_cls(
            f"park_{index:02d}_{key}_hazards",
            f"{park['name']} hazards",
            f"Key field hazards around {park['name']} include {park['hazards']}. Check official closures, forecast, fire danger and local signs before committing to a route.",
            source,
            tags + ("hazards", "safety"),
            "high" if any(word in park["hazards"] for word in ("heat", "cold", "crocodile", "flood", "remote", "cliff", "surf")) else "normal",
        ))
        items.append(item_cls(
            f"park_{index:02d}_{key}_planning",
            f"{park['name']} planning note",
            f"For {park['name']}, plan water, turnaround time, layers and communications for {park['region']}. Treat offline advice as a field prompt and confirm current track, road and weather status while online.",
            source,
            tags + ("planning", "offline"),
            "normal",
        ))
    return items


def _ranger_tip_items(item_cls: Any, source: Any) -> list[Any]:
    return [
        item_cls(
            f"ranger_tip_{index:02d}_{_slug(title)}",
            f"Ranger tip: {title}",
            text,
            source,
            tuple(tags),
            risk,
        )
        for index, (title, text, tags, risk) in enumerate(RANGER_TIPS, start=1)
    ]


def _species_items(item_cls: Any, sources: dict[str, Any]) -> list[Any]:
    items: list[Any] = []
    for name in SNAKES:
        items.append(item_cls(
            f"snake_{_slug(name)}",
            f"{name.title()} field cue",
            f"{name.title()} is included in the Australian snake awareness set. Do not handle or approach for a better photo; keep distance and use snake-bite first aid for any suspected bite.",
            sources["museum_danger"],
            ("snake", "venom", "photo id", name),
            "critical",
        ))
    for name in SPIDERS:
        risk = "critical" if "funnel" in name or "mouse" in name else "high"
        items.append(item_cls(
            f"spider_{_slug(name)}",
            f"{name.title()} field cue",
            f"{name.title()} is included in the spider awareness set. Avoid handling spiders and check shoes, tents and stored gear before use. Escalate severe bites or funnel-web-like bites urgently.",
            sources["museum_danger"],
            ("spider", "bite", "photo id", name),
            risk,
        ))
    for name in MARINE:
        items.append(item_cls(
            f"marine_{_slug(name)}",
            f"{name.title()} marine hazard",
            f"{name.title()} is included in the marine hazard set. Wear footwear around reefs or rock pools, avoid handling marine life, obey local stinger signs and seek urgent help for severe pain, collapse or breathing symptoms.",
            sources["healthdirect"],
            ("marine", "sting", "bite", "beach", name),
            "critical",
        ))
    for name in PLANTS:
        risk = "high" if any(word in name for word in ("stinging", "oleander", "castor", "fireweed", "foxglove", "lawyer")) else "normal"
        items.append(item_cls(
            f"plant_{_slug(name)}",
            f"{name.title()} plant note",
            f"{name.title()} is included in the plant awareness set. Observe plants without touching, eating or damaging them; many useful, irritating and toxic species can look different across seasons.",
            sources["inat"],
            ("plant", "flora", "photo id", name),
            risk,
        ))
    for name in BUSH_TUCKER:
        items.append(item_cls(
            f"bush_tucker_{_slug(name)}",
            f"{name.title()} bush tucker context",
            f"{name.title()} is included as bush tucker knowledge, not a permission to harvest or eat. Consumption needs expert local identification, cultural respect, legal access and seasonal certainty.",
            sources["bush_food"],
            ("bush tucker", "food", "foraging", name),
            "high",
        ))
    for name in MUSHROOMS:
        items.append(item_cls(
            f"mushroom_{_slug(name)}",
            f"{name.title()} mushroom caution",
            f"{name.title()} is included in the fungi awareness set. Do not eat wild mushrooms based on app or photo ID; dangerous lookalikes and regional variation make foraging unsafe without expert confirmation.",
            sources["fungi"],
            ("mushroom", "fungus", "foraging", "poison", name),
            "critical",
        ))
    return items


def _cloud_items(item_cls: Any, source: Any) -> list[Any]:
    items: list[Any] = []
    for name, cue in CLOUDS:
        items.append(item_cls(
            f"cloud_{_slug(name)}",
            f"{name.title()} cloud cue",
            f"{name.title()} is {cue}. Cloud reading is only a field observation; check official BoM forecasts and warnings before relying on a route decision.",
            source,
            ("cloud", "weather", "storm", name),
            "high" if any(word in cue for word in ("thunder", "lightning", "flood", "gust", "severe")) else "normal",
        ))
    return items


def _slug(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "_":
            cleaned.append("_")
    return "".join(cleaned).strip("_")
