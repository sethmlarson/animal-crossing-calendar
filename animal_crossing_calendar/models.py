import enum


class Game(str, enum.Enum):
    ANIMAL_FOREST = "AF"
    ANIMAL_FOREST_PLUS = "AF+"
    ANIMAL_CROSSING = "AC"
    ANIMAL_FOREST_EPLUS = "AFe+"


class Region(str, enum.Enum):
    NORTH_AMERICA = "NTSC-M"
    JAPAN = "NTSC-J"
    PAL = "PAL"


class Language(str, enum.Enum):
    ENGLISH = "ENG"
    JAPANESE = "JPN"
