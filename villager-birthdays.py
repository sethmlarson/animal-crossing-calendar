import animal_crossing_calendar as ac
from animal_crossing_calendar import Game

villagers = {}

for game in ac.Game:
    for villager in ac.Villager.for_game(game):
        villagers.setdefault(villager.name_future or villager.name, set()).add(
            game.value
        )
c = 0
game_combo = {}
villagers_without_birthdays = set()
games_with_birthdays = {
    Game.ANIMAL_FOREST_EPLUS,
    Game.ANIMAL_CROSSING_WILD_WORLD,
    Game.ANIMAL_CROSSING_CITY_FOLK,
    Game.ANIMAL_CROSSING_NEW_HORIZONS,
    Game.ANIMAL_CROSSING_NEW_LEAF,
}
games_without_birthdays = [
    Game.ANIMAL_FOREST,
    Game.ANIMAL_FOREST_PLUS,
    Game.ANIMAL_CROSSING,
    Game.ANIMAL_FOREST_EPLUS,
]


villager_birthdays = {}

for game in games_with_birthdays:
    for villager in ac.Villager.for_game(game):
        key = villager.name_future or villager.name
        birthday = villager.birthday
        if birthday:
            villager_birthdays[key] = birthday

villagers_without_birthdays = {}
villagers_with_birthdays = {}
for game in games_without_birthdays:
    for villager in ac.Villager.for_game(game):
        key = villager.name_future or villager.name
        if key in villager_birthdays:
            if key not in villagers_with_birthdays:
                villagers_with_birthdays[key] = villager_birthdays[key]
        else:
            villagers_without_birthdays.setdefault(key, None)
            if villager.star_sign:
                villagers_without_birthdays[key] = villager.star_sign

print(f"## Villagers with birthdays ({len(villagers_with_birthdays)})")
for name, birthday in sorted(
    villagers_with_birthdays.items(), key=lambda x: (x[1], x[0])
):
    print(f"* {name} ({birthday})")

print(f"## Villagers without birthdays ({len(villagers_without_birthdays)})")
star_signs_unassigned = {}
for name, star_sign in sorted(villagers_without_birthdays.items()):
    print(f"* {name} ({star_sign or '???'})")
    star_signs_unassigned.setdefault(star_sign, 0)
    star_signs_unassigned[star_sign] += 1
print(star_signs_unassigned)
