import re
import csv
import pathlib
import datetime
from dataclasses import dataclass
from animal_crossing_calendar import Game


DATA_PATH = pathlib.Path(__file__).parent / "data"
VILLAGERS = {}


@dataclass(eq=True, frozen=True)
class Villager:
    name: str
    name_future: str
    star_sign: str | None
    birthday: tuple[int, int] | None


def load_villagers(game: Game) -> set[Villager]:
    rows = []
    for prefix, suffix in (
        ("islanders-", ""),
        ("villagers-", ""),
        ("villagers-", "-special"),
    ):
        try:
            with (DATA_PATH / f"{prefix}{game.value}{suffix}.csv").open() as f:
                rows.extend(list(csv.DictReader(f)))
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

        villagers.add(
            Villager(
                name=name,
                name_future=name_future,
                star_sign=star_sign,
                birthday=birthday,
            )
        )
    return villagers


for _game in Game:
    for villager in load_villagers(_game):
        VILLAGERS.setdefault(_game, {})[villager.name] = villager
