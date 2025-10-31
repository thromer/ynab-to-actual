_ZWJ = "\u200d"
_people = ["👨", "👩", "🧑", "👶", "👧", "👦"]
_professions = ["💻", "🍳", "🎨", "🔬", "🚒", "✈️", "🚀", "⚕️", "🎓", "🔧"]
_skin_tones = ["🏻", "🏼", "🏽", "🏾", "🏿"]

EMOJIS: list[str] = []

for person in _people:
    for tone in _skin_tones:
        for profession in _professions:
            EMOJIS.append(f"{person}{tone}{_ZWJ}{profession}")
