import csv
import re
import io
from csv import DictReader
import datetime
import pathlib
import typing
import hashlib

import icalendar

from .models import Region, Game, Language

DATA_PATH = pathlib.Path(__file__).parent / "data"
EQUINOX_DATA = list(
    csv.DictReader(io.StringIO((DATA_PATH / "equinoxes.csv").read_text()))
)
HARVEST_MOON_DATA = {}
for _game in (
    Game.ANIMAL_FOREST,
    Game.ANIMAL_FOREST_PLUS,
    Game.ANIMAL_CROSSING,
    Game.ANIMAL_FOREST_EPLUS,
):
    HARVEST_MOON_DATA[_game] = list(
        csv.DictReader(
            io.StringIO((DATA_PATH / f"harvest-moons-{_game.value}.csv").read_text())
        )
    )


def equinox_day(year: int, season: str) -> int:
    assert 2000 <= year <= 2099
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


def start_end_years(game: Game) -> tuple[int, int]:
    years = [int(row["Year"]) for row in HARVEST_MOON_DATA[game]]
    return min(years), max(years)


class EventOccurs:
    def dates_in_year(self, year: int) -> list[datetime.date]:
        raise NotImplementedError()


class StaticEvent(EventOccurs):
    """Event which occurs the same date every year."""

    def __init__(
        self,
        month: int,
        day: int,
    ):
        self.month = month
        self.day = day

    def __eq__(self, other):
        return (
            isinstance(other, StaticEvent)
            and self.month == other.month
            and self.day == other.day
        )

    def dates_in_year(self, year: int) -> list[datetime.date]:
        return [datetime.date(year, self.month, self.day)]


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
    def __init__(
        self,
        *,
        name: str,
        occurs: EventOccurs,
        times: tuple[int, int],
        game: Game,
        location: str | None = None,
    ):
        self.name: str = name
        self.occurs: EventOccurs = occurs
        self.times = times
        self.game = game
        self.location = location

    def to_ics(self) -> list[icalendar.Event]:
        ics_events = []
        ics_uid = hashlib.md5(self.name.encode()).hexdigest()[:16]
        is_recurrence = False
        is_tent_campers = self.name in ("Tent Campers", "キャンプ")
        if is_tent_campers:
            self.times = (9 * 3600, 15 * 3600)  # Note: 3PM the next day.
        start_year, end_year = start_end_years(self.game)
        for year in range(start_year, end_year + 1):
            for dt in self.occurs.dates_in_year(year):
                ics_event = icalendar.Event()
                ics_event["SUMMARY"] = self.name
                ics_event["RECURRENCE-ID" if is_recurrence else "UID"] = ics_uid
                if self.location is not None:
                    ics_event["LOCATION"] = self.location
                if self.times == (0, 0):
                    ics_event["DTSTART"] = dt.strftime("%Y%m%d")
                    ics_event["DTEND"] = (dt + datetime.timedelta(days=1)).strftime(
                        "%Y%m%d"
                    )
                else:
                    start_dt = datetime.datetime.combine(
                        dt,
                        datetime.time(
                            hour=self.times[0] // 3600,
                            minute=(self.times[0] % 3600) // 60,
                        ),
                    )
                    end_dt = datetime.datetime.combine(
                        dt,
                        datetime.time(
                            hour=self.times[1] // 3600,
                            minute=(self.times[1] % 3600) // 60,
                        ),
                    )
                    if self.times[1] < self.times[0] or is_tent_campers:
                        end_dt += datetime.timedelta(days=1)
                    ics_event["DTSTART"] = start_dt.strftime("%Y%m%dT%H%M%S")
                    ics_event["DTEND"] = end_dt.strftime("%Y%m%dT%H%M%S")
                is_recurrence = True
                ics_events.append(ics_event)
        return ics_events

    @classmethod
    def load(cls, *, game: Game, region: Region, language: Language) -> list["Event"]:
        rows = list(DictReader((DATA_PATH / "events.csv").open()))
        events = []
        for row in rows:
            games_in = {Game(g) for g in row["Games Appeared In"].split(", ")}
            if game not in games_in:
                continue

            # What is the event's name?
            if Game.ANIMAL_CROSSING in games_in:
                name_english = row["Event"].strip()
                name_japanese_afp = row["Name (AF+)"].strip()
                # Use the AFe+ name unless there's explicitly an AF+ name available.
                if Game.ANIMAL_FOREST_EPLUS == game or name_japanese_afp in ("", "-"):
                    name_japanese = row["Name (AFe+)"].strip()
                else:
                    name_japanese = name_japanese_afp
            else:  # Japanese-exclusive events.
                name_english = row["Name (JP Translation)"].strip()
                name_japanese = row["Event"].strip()

            if language == Language.ENGLISH:
                name = name_english
            else:
                assert language == Language.JAPANESE, language
                name = name_japanese

            # TODO: Remove this once all event
            # Japanese translations are available.
            # Specifically, 'Mushrooming Season'.
            if name in ("-", "") and name_english not in ("-", ""):
                name = name_english

            # When does the event occur?
            occurs_default = row["Date"].strip()  # AC/AFe+
            occurs_pal = row["Date (Europe)"].strip()
            occurs_afp = row["Date (AF+)"].strip()
            occurs_af = row["Date (AF)"].strip()
            if region == Region.PAL and occurs_pal not in ("-", ""):
                occurs = parse_event_occurs(game, occurs_pal)
            elif occurs_afp not in ("-", "") and game == Game.ANIMAL_FOREST_PLUS:
                occurs = parse_event_occurs(game, occurs_afp)
            elif occurs_af not in ("-", "") and game == Game.ANIMAL_FOREST:
                occurs = parse_event_occurs(game, occurs_af)
            else:
                occurs = parse_event_occurs(game, occurs_default)

            start_time = 0
            end_time = 0
            row_time = row["Time"].strip().lower()
            mat = re.search(
                r"([0-9]{,2})(am|pm) - ([0-9]{,2})(?::([0-9]{2}))?(am|pm)",
                row_time,
            )
            if mat is not None:
                start_hour, start_ampm, end_hour, end_minute, end_ampm = mat.groups()
                end_minute = int(end_minute or 0)
                start_time = (
                    int(start_hour) + (12 if start_ampm == "pm" else 0)
                ) * 3600
                end_time = (int(end_hour) + (12 if end_ampm == "pm" else 0)) * 3600
                end_time += end_minute * 60
            elif "tom nook" in row_time and "shop" in row_time:
                start_time = 3600 * 9
                end_time = 3600 * 22

            location = row["Location"].strip()
            if location in ("-", ""):
                location = None

            events.append(
                Event(
                    name=name,
                    occurs=occurs,
                    times=(start_time, end_time),
                    location=location,
                    game=game,
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
    elif "Day after Harvest Festival" in value:
        # Harvest Festival is 4th Thursday in November.
        return DayAfterNthWeekdayOfMonth(
            month=11,
            weekday=weekday_to_number("Thursday"),
            nth_weekday=4,
        )
    else:
        return Never()
