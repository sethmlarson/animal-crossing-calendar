from .models import Game, Region
from .events import Event


GAME_REGION_COMBOS = {
    (Game.ANIMAL_FOREST, Region.JAPAN),
    (Game.ANIMAL_FOREST_PLUS, Region.JAPAN),
    (Game.ANIMAL_CROSSING, Region.NORTH_AMERICA),
    (Game.ANIMAL_CROSSING, Region.PAL),
    (Game.ANIMAL_FOREST_EPLUS, Region.JAPAN),
}


class Calendar:
    """Top-level Calendar class"""

    def __init__(self, *, game: Game, region: Region):
        if (game, region) not in GAME_REGION_COMBOS:
            raise ValueError("Game and region combination is not valid")
        self.game = game
        self.region = region

    def events(self) -> list[Event]:
        return Event.load(game=self.game, region=self.region)
