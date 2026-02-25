import csv
import re
import io
from csv import DictReader
import datetime
import pathlib
import typing

import icalendar

from .models import Region, Game

DATA_PATH = pathlib.Path(__file__).parent / "data"
EQUINOX_DATA = list(
    csv.DictReader(io.StringIO((DATA_PATH / "equinoxes.csv").read_text()))
)
HARVEST_MOON_DATA = {}
for _game in Game:
    HARVEST_MOON_DATA[_game] = list(
        csv.DictReader(
            io.StringIO((DATA_PATH / f"harvest-moons-{_game.value}.csv").read_text())
        )
    )


def equinox_day(year: int, season: str) -> int:
    assert 2001 <= year <= 2099
    return int(EQUINOX_DATA[year - 2001][season])


def harvest_moon_date(game: Game, year: int) -> tuple[int, int] | tuple[None, None]:
    harvest_moon_dates = HARVEST_MOON_DATA[game]
    first_year = int(harvest_moon_dates[0]["Year"])
    last_year = int(harvest_moon_dates[-1]["Year"])
    if first_year <= year <= last_year:
        row = harvest_moon_dates[year - first_year]
        return int(row["Month"]), int(row["Day"])
    else:
        return None, None


class EventOccurs:
    def dates_in_year(self, year: int) -> list[datetime.date]:
        raise NotImplementedError()

    def to_ics(self) -> list[tuple[str, typing.Any]]:
        return [
            (("dtstart" if i == 0 else "rdate"), dt)
            for i, dt in enumerate(sorted(self.dates_in_year()))
        ]


class StaticEvent(EventOccurs):
    """Event which occurs the same date every year."""

    def __init__(self, month: int, day: int):
        self._month_day = (month, day)

    def __eq__(self, other):
        return isinstance(other, StaticEvent) and self._month_day == other._month_day

    def dates_in_year(self, year: int) -> list[datetime.date]:
        return [datetime.date(year, *self._month_day)]


class RangeEvent(EventOccurs):
    def __init__(
        self, month: int, start_day: int, end_day: int, end_month: int | None = None
    ):
        self._month = month
        self._start_day = start_day
        self._end_day = end_day
        self._end_month = end_month or month

    def __eq__(self, other):
        return (
            isinstance(other, RangeEvent)
            and self._month == other._month
            and self._start_day == other._start_day
            and self._end_month == other._end_month
            and self._end_day == other._end_day
        )

    def dates_in_year(self, year: int) -> list[datetime.date]:
        dates = []
        day = datetime.date(year=year, month=self._month, day=self._start_day)
        end_day = datetime.date(year=year, month=self._end_month, day=self._end_day)
        while day <= end_day:
            dates.append(day)
            day += datetime.timedelta(days=1)
        return dates


class NthWeekdayOfMonth(EventOccurs):
    """Event occurring once on the Nth weekday of a month."""

    def __init__(self, month: int, nth_weekday: int, weekday: int):
        self._month = month
        self._nth_weekday = nth_weekday
        self._weekday = weekday  # Monday=0

    def __eq__(self, other):
        return (
            type(other) == NthWeekdayOfMonth
            and self._month == other._month
            and self._nth_weekday == other._nth_weekday
            and self._weekday == other._weekday
        )

    def dates_in_year(self, year: int) -> list[datetime.date]:
        first_of_month = datetime.date(year=year, month=self._month, day=1)
        day = (
            1
            + ((self._nth_weekday - first_of_month.weekday() + 7) % 7)
            + (7 * (self._nth_weekday - 1))
        )
        return [datetime.date(year=year, month=self._month, day=day)]


class DayAfterNthWeekdayOfMonth(NthWeekdayOfMonth):
    def __init__(self, month: int, nth_weekday: int, weekday: int):
        super().__init__(month=month, nth_weekday=nth_weekday, weekday=weekday)

    def __eq__(self, other):
        return (
            type(other) == DayAfterNthWeekdayOfMonth
            and self._month == other._month
            and self._nth_weekday == other._nth_weekday
            and self._weekday == other._weekday
        )

    def dates_in_year(self, year: int) -> list[datetime.date]:
        return [super().dates_in_year(year)[0] + datetime.timedelta(days=1)]


class EveryWeekdayOfMonth(EventOccurs):
    """Event occurring every weekday of a month."""

    def __init__(self, month: int, weekday: int):
        self._weekday = weekday
        self._month = month

    def __eq__(self, other):
        return (
            type(other) == EveryWeekdayOfMonth
            and self._weekday == other._weekday
            and self._month == other._month
        )

    def dates_in_year(self, year: int) -> list[datetime.date]:
        maybe_day = datetime.date(year=year, month=self._month, day=1)
        maybe_day += datetime.timedelta(
            days=((self._weekday - maybe_day.weekday() + 7) % 7)
        )
        dates = []
        while maybe_day.month == self._month:
            dates.append(maybe_day)
            maybe_day += datetime.timedelta(days=7)
        return dates


class LastDayOfEveryMonth(EventOccurs):
    def dates_in_year(self, year: int) -> list[datetime.date]:
        firsts_of_months = []
        for month in range(2, 13):
            firsts_of_months.append(datetime.date(year=year, month=month, day=1))
        firsts_of_months.append(datetime.date(year=year + 1, month=1, day=1))
        return [date - datetime.timedelta(days=1) for date in firsts_of_months]


class SpringEquinox(EventOccurs):
    def dates_in_year(self, year: int) -> list[datetime.date]:
        day = equinox_day(year, "Spring")
        return [datetime.date(year=year, month=3, day=day)]


class AutumnEquinox(EventOccurs):
    def dates_in_year(self, year: int) -> list[datetime.date]:
        day = equinox_day(year, "Autumn")
        return [datetime.date(year=year, month=9, day=day)]


class HarvestMoon(EventOccurs):
    def __init__(self, game: Game):
        self.game = game

    def dates_in_year(self, year: int) -> list[datetime.date]:
        month, day = harvest_moon_date(self.game, year)
        if month is None:
            return []
        return [datetime.date(year=year, month=month, day=day)]


class TentCamperSaturdays(EventOccurs):
    def dates_in_year(self, year: int) -> list[datetime.date]:
        dates = []
        date = datetime.date(year=year, month=6, day=1)
        end_date = datetime.date(year=year, month=8, day=31)

        # Campers can spawn on May 26th
        # only if June 1st is a Saturday.
        if date.weekday() == 5:
            dates.append(datetime.date(year=year, month=5, day=26))

        while date <= end_date:
            # July 4th is Fireworks and August 12th is the Meteor Shower.
            # No campers on these days.
            if (date.month, date.day) not in ((7, 4), (8, 12)) and date.weekday() in (
                5,
                6,
            ):
                dates.append(date)
            date = date + datetime.timedelta(days=1)
        return dates


class Never(EventOccurs):
    def dates_in_year(self, year: int) -> list[datetime.date]:
        return []


class Event:
    def __init__(self, *, name_regional: str, name_english: str, occurs: EventOccurs):
        self.name_regional: str = name_regional
        self.name_english: str = name_english
        self.occurs: EventOccurs = occurs

    def to_ics(self) -> icalendar.Event:
        ics_event = icalendar.Event()
        ics_event["summary"] = self.name_regional
        first_occurrence = True
        dts = []
        for year in range(2001, 2031):
            for dt in self.occurs.dates_in_year(year):
                dts.append(dt)
        if not dts:
            return None
        ics_event.add("dtstart", dts[0])
        if len(dts) > 1:
            ics_event.add("RDATE", dts[1:])
        return ics_event

    @classmethod
    def load(cls, *, game: Game, region: Region) -> list["Event"]:
        rows = list(DictReader((DATA_PATH / "events.csv").open()))
        events = []
        for row in rows:
            games_in = {Game(g) for g in row["Games Appeared In"].split(", ")}
            if game not in games_in:
                continue

            # What is the event's name?
            if Game.ANIMAL_CROSSING in games_in:
                name_english = row["Event"].strip()
                if Game.ANIMAL_FOREST_EPLUS == game:
                    name_japanese = row["Name (AFe+)"].strip()
                else:
                    name_japanese = row["Name (AF+)"].strip()
            else:
                name_english = row["Name (JP Translation)"].strip()
                name_japanese = row["Event"].strip()
            if region in (Region.NORTH_AMERICA, Region.PAL):
                name_regional = name_english
            else:
                assert region == Region.JAPAN
                name_regional = name_japanese

            # TODO: Remove this once all event
            # Japanese translations are available.
            # Specifically, 'Mushrooming Season'.
            if name_regional == "-" and name_english != "-":
                name_regional = name_english

            # When does the event occur?
            occurs_default = row["Date"]  # AC/AFe+
            occurs_pal = row["Date (Europe)"]
            occurs_afp = row["Date (AF+)"]
            occurs_af = row["Date (AF)"]
            if region == Region.PAL and occurs_pal != "-":
                occurs = parse_event_occurs(game, occurs_pal)
            elif occurs_afp != "-" and game == Game.ANIMAL_FOREST_PLUS:
                occurs = parse_event_occurs(game, occurs_afp)
            elif occurs_af != "-" and game == Game.ANIMAL_FOREST:
                occurs = parse_event_occurs(game, occurs_af)
            else:
                occurs = parse_event_occurs(game, occurs_default)

            events.append(
                Event(
                    name_regional=name_regional,
                    name_english=name_english,
                    occurs=occurs,
                )
            )

        return events


def month_to_number(month: str) -> int:
    return [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ].index(month) + 1


def weekday_to_number(weekday: str) -> int:
    return [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ].index(weekday)


def parse_event_occurs(game: Game, value: str) -> EventOccurs:
    """Parse the Megasheet 'Date' logic into an 'EventOccurs' object"""
    value = value.strip()
    month_pat = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    date_pat = month_pat + r" ([0-9]{1,2})"
    single_day_pat = r"\A" + date_pat + r"\Z"
    range_pat = r"\A" + month_pat + r" ([0-9]{1,2})-([0-9]{1,2})\Z"
    multi_month_range_pat = (
        r"\AEvery day "
        + month_pat
        + r" ([0-9]{1,2}) - "
        + month_pat
        + r" ([0-9]{1,2})\Z"
    )
    weekday_pat = r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
    ordinal_pat = r"(Every|([0-4])(?:st|nd|rd|th))"
    nth_weekday_pat = (
        r"\A" + ordinal_pat + " " + weekday_pat + " in " + month_pat + r"\Z"
    )
    day_after_nth_weekday_pat = (
        r"\ADay after " + ordinal_pat + " " + weekday_pat + " in " + month_pat + r"\Z"
    )

    if match := re.search(single_day_pat, value):
        month, day = match.groups()
        return StaticEvent(
            month=month_to_number(month),
            day=int(day),
        )
    elif match := re.search(range_pat, value):
        month, start_day, end_day = match.groups()
        return RangeEvent(
            month=month_to_number(month),
            start_day=int(start_day),
            end_day=int(end_day),
        )
    elif match := re.search(multi_month_range_pat, value):
        start_month, start_day, end_month, end_day = match.groups()
        return RangeEvent(
            month=month_to_number(start_month),
            start_day=int(start_day),
            end_month=month_to_number(end_month),
            end_day=int(end_day),
        )
    elif match := re.search(nth_weekday_pat, value):
        nth_weekday, nth_weekday_number, weekday, month = match.groups()
        if nth_weekday == "Every":
            return EveryWeekdayOfMonth(
                month=month_to_number(month), weekday=weekday_to_number(weekday)
            )
        else:
            return NthWeekdayOfMonth(
                month=month_to_number(month),
                weekday=weekday_to_number(weekday),
                nth_weekday=int(nth_weekday_number),
            )
    elif match := re.search(day_after_nth_weekday_pat, value):
        nth_weekday, nth_weekday_number, weekday, month = match.groups()
        return DayAfterNthWeekdayOfMonth(
            month=month_to_number(month),
            weekday=weekday_to_number(weekday),
            nth_weekday=int(nth_weekday_number),
        )
    elif value == "Last Day of every Month":
        return LastDayOfEveryMonth()
    elif "Spring Equinox" in value:
        return SpringEquinox()
    elif "Varies between September" in value:
        return HarvestMoon(game)
    elif "Autumn Equinox" in value:
        return AutumnEquinox()
    elif value == "Every weekend in Summer":
        return TentCamperSaturdays()
    else:
        return Never()
