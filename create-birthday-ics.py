import re
import animal_crossing_calendar as ac

for game in ac.Game:
    for villager in ac.Villager.for_game(game):
        slug = re.sub(r"[.\s-]+", "", villager.name_slug).upper()
        birthday = villager.birthday_allow_unofficial()
        if birthday is None:
            continue
        filename = f"ics/BDAY-{slug}.ics"
        with open(filename, "w") as f:
            f.truncate()
            f.write(f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Seth Larson//Animal Crossing Calendar//EN
CALSCALE:GREGORIAN
X-WR-CALNAME:{villager.name_future}'s Birthday
BEGIN:VEVENT
DTSTART:2001{str(birthday[0]).zfill(2)}{str(birthday[1]).zfill(2)}
RRULE:FREQ=YEARLY
END:VEVENT""")
