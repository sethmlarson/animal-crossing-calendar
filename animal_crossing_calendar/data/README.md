Files within this directory are exports
from the “[Data Megasheet for Animal Crossing (N64, GCN)](https://docs.google.com/spreadsheets/d/13sRAcj9YbP9_i-u0Kg6S7ycHbaOQx1jFG4lYLm2DJ4c/edit?gid=1178972323#gid=1178972323)” project.
Credit to Cuyler, Phil_Macrocheira, AlexBot2004, Chubby_Bub, and Soleil.

Equinoxes (`equinoxes.csv`) was generated from
running the following C program, extracted from
the [Animal Crossing Decomp project](https://github.com/ACreTeam/ac-decomp) (CC0-1.0).

```c
#include <stdio.h>
#include <errno.h>   // for errno
#include <limits.h>  // for INT_MAX, INT_MIN
#include <stdlib.h>  // for strtol

// Fall equinox
// Sept XX with:
int lbRk_AutumnalEquinoxDay(int year) {
  year -= 1980;
  return (int)(23.2488f + (0.242194f * (float)year)) - (year / 4);
}

// Spring Equinox:
// March XX with:
int lbRk_VernalEquinoxDay(int year) {
  year -= 1980;
  return (int)(20.8431f + (0.242194f * (float)year)) - (year / 4);
}

int main(int argc, char* argv[]) {
  printf("Year,Spring,Autumn\n");
  for(int year=2001; year<2100; year++) {
    printf("%d,%d,%d\n", year, lbRk_VernalEquinoxDay(year), lbRk_AutumnalEquinoxDay(year));
  }
  return 0;
}
```