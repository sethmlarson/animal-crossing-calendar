import icalendar
from .models import Game, Region, Language
from .events import Event


GAMES_AND_REGIONS = {
    (Game.ANIMAL_FOREST, Region.NTSC_J),
    (Game.ANIMAL_FOREST_PLUS, Region.NTSC_J),
    (Game.ANIMAL_CROSSING, Region.NTSC),
    (Game.ANIMAL_CROSSING, Region.PAL),
    (Game.ANIMAL_FOREST_EPLUS, Region.NTSC_J),
}


class Calendar:
    """Top-level Calendar class"""

    def __init__(self, *, game: Game, region: Region, language: Language):
        if (game, region) not in GAMES_AND_REGIONS:
            raise ValueError("Game and region combination is not valid")
        self.game = game
        self.region = region
        self.language = language

    def events(self) -> list[Event]:
        return Event.load(game=self.game, region=self.region, language=self.language)

    def to_ics(self) -> icalendar.Calendar:
        ics_cal = icalendar.Calendar()
        ics_cal["PRODID"] = "-//Seth Larson//Animal Crossing Calendar//EN"
        ics_cal["VERSION"] = "2.0"
        ics_cal["CALSCALE"] = "GREGORIAN"
        ics_cal["X-WR-CALNAME"] = (
            f"{self.game.display_name(self.language)} ({self.region.value})"
        )

        for event in self.events():
            for ics_event in event.to_ics():
                ics_cal.add_component(ics_event)
        return ics_cal
