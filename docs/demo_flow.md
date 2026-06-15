# Outbush AI Demo Flow

## 1. Why Outbush AI?

Australia is enormous, and mobile coverage drops away quickly once you head out bush. Outbush AI is a portable field assistant that runs on a Raspberry Pi, so a phone can connect to the Pi and ask questions or check photos without a data connection.

The point is not to replace judgement, emergency services, or official warnings. The point is to carry a small model stack plus Australian hiking, wildlife, weather, and first-aid context into places where normal apps stop working.

## 2. Walk Through The Features

Start on the phone-friendly app home screen.

- Ask: local llama.cpp answers grounded in the Australian RAG pack.
- Photo: MiniCPM-V plus a field-tuned species classifier for candidate wildlife/plant/fungus triage.
- First Aid: structured quick flows for snake bite, spider bite, poisoning, marine stings, heat, cold, and exposure.
- Encyclopedia: local searchable field pack with dangerous animals, plants, parks, ranger tips, and survival notes.
- Weather: cached or live 10-day weather pack for common Australian places, national parks, and walking regions.
- Checklist: copyable pre-walk checklist for offline prep.

## 3. Ask A Relevant Question

Use:

> We lost the track in the Blue Mountains and the group is getting tired. What should we do now?

Expected story beat: the answer should say to stop early, keep the group together, avoid pushing deeper into uncertain terrain, conserve phone battery, stay visible/shelter, and escalate if the group cannot safely relocate the route.

## 4. Upload A Photo That Works Properly

Use a clear red-bellied black snake field photo.

Expected story beat: the app should return a snake candidate with critical risk, keep-clear guidance, and snake-bite first-aid escalation. It should not claim certainty or encourage approaching for a better photo.

## 5. Check Weather For Kosciuszko

Use the Weather tab and type:

> Kosciusko

The typeahead should offer `Kosciuszko National Park`; both common spellings should resolve there. Sync the 10-day pack and explain that the app separates live/cached modelled weather from official BoM warnings and park closures.

## Closing Line

Outbush AI is a small-model, offline-first pattern: the regional knowledge pack can be swapped for another country, climate, or risk profile, while the Pi keeps the assistant portable and usable away from reception.
