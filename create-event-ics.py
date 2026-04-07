from pathlib import Path

import animal_crossing_calendar as ac

for game, region in ac.GAMES_AND_REGIONS:
    languages = [ac.Language.ENGLISH]
    if region == ac.Region.JAPAN:
        languages.append(ac.Language.JAPANESE)
    for language in languages:
        cal = ac.Calendar(
            game=game,
            region=region,
            language=language,
        )

        cal_ics_path = Path(f"ics/CAL-{game.value}-{region.value}-{language.value}.ics")
        cal_ics_path.parent.mkdir(parents=True, exist_ok=True)
        with cal_ics_path.open("wb") as f:
            f.write(cal.to_ics().to_ical())
