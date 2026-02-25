import icalendar
from .models import Game, Region
from .events import Event


GAMES_AND_REGIONS = {
    (Game.ANIMAL_FOREST, Region.JAPAN),
    (Game.ANIMAL_FOREST_PLUS, Region.JAPAN),
    (Game.ANIMAL_CROSSING, Region.NORTH_AMERICA),
    (Game.ANIMAL_CROSSING, Region.PAL),
    (Game.ANIMAL_FOREST_EPLUS, Region.JAPAN),
}


class Calendar:
    """Top-level Calendar class"""

    def __init__(self, *, game: Game, region: Region):
        if (game, region) not in GAMES_AND_REGIONS:
            raise ValueError("Game and region combination is not valid")
        self.game = game
        self.region = region

    def events(self) -> list[Event]:
        return Event.load(game=self.game, region=self.region)

    def to_ics(self) -> icalendar.Calendar:
        ics_cal = icalendar.Calendar()
        for event in self.events():
            if ics_component := event.to_ics():
                ics_cal.add_component(ics_component)
        return ics_cal
