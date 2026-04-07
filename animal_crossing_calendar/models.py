import enum


class Game(str, enum.Enum):
    ANIMAL_FOREST = "AF"
    ANIMAL_FOREST_PLUS = "AF+"
    ANIMAL_CROSSING = "AC"
    ANIMAL_FOREST_EPLUS = "AFe+"

    # For villager birthdays only.
    ANIMAL_CROSSING_WILD_WORLD = "ACWW"
    ANIMAL_CROSSING_CITY_FOLK = "ACCF"
    ANIMAL_CROSSING_NEW_LEAF = "ACNL"
    ANIMAL_CROSSING_NEW_HORIZONS = "ACNH"

    def display_name(self, language: "Language"):
        if language == Language.ENGLISH:
            return {
                Game.ANIMAL_FOREST: "Animal Forest",
                Game.ANIMAL_FOREST_PLUS: "Animal Forest+",
                Game.ANIMAL_FOREST_EPLUS: "Animal Forest e+",
                Game.ANIMAL_CROSSING: "Animal Crossing",
            }[self]
        else:
            assert language == Language.JAPANESE
            return {
                Game.ANIMAL_FOREST: "どうぶつの森",
                Game.ANIMAL_FOREST_PLUS: "どうぶつの森+",
                Game.ANIMAL_FOREST_EPLUS: "どうぶつの森 e+",
            }[self]


class Region(str, enum.Enum):
    NORTH_AMERICA = "NTSC"
    JAPAN = "NTSC-J"
    PAL = "PAL"


class Language(str, enum.Enum):
    ENGLISH = "ENG"
    JAPANESE = "JPN"
