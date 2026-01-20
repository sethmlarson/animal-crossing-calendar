# Animal Crossing Calendar

Calendar of holidays and villager birthdays for Dōbutsu no Mori,
Dōbutsu no Mori+, Animal Crossing, and Dōbutsu no Mori e+

Data sourced from the “[Data Megasheet for Animal Crossing (N64, GCN)](https://nookipedia.com/wiki/Community:ACGC_Spreadsheet)”
and the “[Animal Crossing Decompilation project](https://github.com/ACreTeam/ac-decomp/)”.

```python
import animal_crossing_calendar as ac

cal = ac.Calendar(
    game=ac.Game.ANIMAL_FOREST_EPLUS,
    region=ac.Region.JAPAN,
)
for event in cal.events():
    print(event.name_regional, end=" ")
    print(", ".join(dt.strftime("%Y年%m月%d日") for dt in event.occurs.dates_in_year(2026)))

# 初詣 2026-01-01
# グランドホッグデー 2026-02-02
# バレンタインデー 2026-02-14
# 春の運動会 2026-03-20
# エイプリルフール 2026-04-01
# お花見 2026-04-05, 2026-04-06, 2026-04-07
# ...
```