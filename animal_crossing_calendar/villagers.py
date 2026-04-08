import re
import csv
import pathlib
import datetime
from dataclasses import dataclass
from animal_crossing_calendar import Game


_DATA_PATH = pathlib.Path(__file__).parent / "data"
_VILLAGERS = {}

_STAR_SIGN_DATES = {
    "Aries": ((3, 21), (4, 19)),
    "Taurus": ((4, 20), (5, 20)),
    "Gemini": ((5, 21), (6, 21)),
    "Cancer": ((6, 22), (7, 22)),
    "Leo": ((7, 23), (8, 22)),
    "Virgo": ((8, 23), (9, 22)),
    "Libra": ((9, 23), (10, 23)),
    "Scorpio": ((10, 24), (11, 22)),
    "Sagittarius": ((11, 23), (12, 21)),
    "Capricorn": ((12, 22), (12, 31)),
    "Capricorn2": ((1, 1), (1, 19)),
    "Aquarius": ((1, 20), (2, 18)),
    "Pisces": ((2, 19), (3, 20)),
}


def date_to_star_sign(date: tuple[int, int]):
    for star_sign, (start_date, end_date) in _STAR_SIGN_DATES.items():
        if start_date <= date <= end_date:
            return star_sign.replace("2", "")
    raise ValueError(f"Invalid date? {date}")


@dataclass(eq=True, frozen=True)
class Villager:
    name: str
    name_future: str
    star_sign: str | None
    birthday: tuple[int, int] | None
    game: Game

    @staticmethod
    def for_game(game: Game) -> set["Villager"]:
        return set(_VILLAGERS[game].values())

    @staticmethod
    def all_games() -> set["Villager"]:
        villagers = {}
        for game in (
            Game.ANIMAL_CROSSING_NEW_HORIZONS,
            Game.ANIMAL_CROSSING_NEW_LEAF,
            Game.ANIMAL_CROSSING_CITY_FOLK,
            Game.ANIMAL_CROSSING_WILD_WORLD,
            Game.ANIMAL_FOREST_EPLUS,
            Game.ANIMAL_CROSSING,
            Game.ANIMAL_FOREST_PLUS,
            Game.ANIMAL_FOREST,
        ):
            for villager in Villager.for_game(game):
                villagers.setdefault(villager.name_future, villager)
        return set(villagers.values())


def _load_villagers(game: Game) -> set[Villager]:
    rows = []
    for prefix, suffix in (
        ("islanders-", ""),
        ("villagers-", ""),
        ("villagers-", "-special"),
    ):
        try:
            with (_DATA_PATH / f"{prefix}{game.value}{suffix}.csv").open() as f:
                for row in csv.DictReader(f):
                    rows.append(row)
        except FileNotFoundError:
            continue

    villagers = set()
    star_sign_re = re.compile(
        r"(Aries|Taurus|Gemini|Cancer|Leo|Virgo|Libra|Scorpio|Sagittarius|Capricorn|Aquarius|Pisces)"
    )
    for row in rows:
        name = row["Name"]
        name_future = None
        star_sign = None
        birthday = None
        for key in row.keys():
            if key in (
                "Name (AC)",
                "Name (Future Games)",
                "Name (Future Games English)",
            ):
                name_future = row[key].strip()
                if name_future == "-":
                    name_future = None
            elif "GBA Constellation" in key:
                star_sign = star_sign_re.search(row[key]).group(1)
            elif key == "Birthday":
                birthday_str = row[key].strip()
                if birthday_str in ("", "0/0"):
                    continue
                birthday_str = f"2024 {birthday_str}"  # Leap year
                if "/" in birthday_str:
                    birthday_dt = datetime.datetime.strptime(birthday_str, "%Y %m/%d")
                else:
                    birthday_dt = datetime.datetime.strptime(birthday_str, "%Y %B %d")
                birthday = (birthday_dt.month, birthday_dt.day)

        # Nindori's birthday is printed on his e-Reader card.
        # The only villager in the GCN era with a known birthday.
        if birthday is None and name == "ニンドリ" and game == Game.ANIMAL_FOREST_EPLUS:
            birthday = (9, 14)

        name = name.rstrip(".")
        name_future = name_future.rstrip(".") if name_future else None

        if name_future is None:
            name_future = name

        # Calculate star sign based on birthday.
        if birthday is not None and star_sign is None:
            star_sign = date_to_star_sign(birthday)

        villagers.add(
            Villager(
                game=game,
                name=name,
                name_future=name_future,
                star_sign=star_sign,
                birthday=birthday,
            )
        )
    return villagers


for _game in Game:
    for villager in _load_villagers(_game):
        _VILLAGERS.setdefault(_game, {})[villager.name] = villager
