# Points vs. Intersection: Comparisons and Figures

This note is being built section by section from the saved CSV summaries in
`points_vs_intersection_exploration/`. Figure outputs are written under
`points_vs_intersection_exploration/figures/`.

Generation command for the current figures:

```bash
python points_vs_intersection_exploration/generate_comparison_figures.py
```

## 1. Metro Area Counts and Chicago Example

### Metro Counts

These counts are filtered to the March 2020 CBSA definition vintage. In this
single-vintage view, shapefile output counts and unique `(year, cbsa_code)`
counts match: each CBSA appears once per year.

| Year | Old intersection method | Representative-point method |
| --- | ---: | ---: |
| 1970 | 341 | 271 |
| 1980 | 384 | 379 |
| 1990 | 384 | 384 |
| 2000 | 384 | 384 |
| 2010 | 392 | 392 |
| 2020 | 392 | 392 |

The representative-point outputs are a subset of the old any-intersection
outputs for the years where file presence differs. In the March 2020 vintage,
that means 70 old-only metro areas in 1970 and 5 in 1980. The older
all-vintage audit in `counts_by_year.csv` reports 420 old-only outputs in 1970
and 30 in 1980, which reflects the same gaps repeated across the six CBSA
definition vintages checked there.

![Metro counts by year](figures/metro_counts_by_year.png)

### Chicago Example

For Chicago-Naperville-Elgin, IL-IN-WI, CBSA `16980`, using the `march_2020`
definition, the representative-point rule removes boundary tracts in every
historical year before 2020. It adds no tracts in this example. By 2020, the two
assignment methods produce the same tract membership: 2,330 retained tracts, 0
removed tracts, and 0 added tracts.

The thin outline is the fixed March 2020 CBSA definition polygon from
`cbsas/defs/`; the grey retained tracts still come from each year's tract
geography.

![Chicago difference maps by year](figures/chicago_16980_march_2020_assignment_differences_by_year.png)

| Year | Old tracts | Point tracts | Delta | Removed by points | Added by points | Population delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1970 | 1,539 | 1,525 | -14 | 14 | 0 | -76,013 |
| 1980 | 1,697 | 1,671 | -26 | 26 | 0 | -120,713 |
| 1990 | 1,986 | 1,936 | -50 | 50 | 0 | -207,212 |
| 2000 | 2,093 | 2,052 | -41 | 41 | 0 | -195,708 |
| 2010 | 2,213 | 2,210 | -3 | 3 | 0 | -16,518 |
| 2020 | 2,330 | 2,330 | 0 | 0 | 0 | 0 |

## 2. Tract Count Distributions

The paired histograms below use only common `(year, stem)` outputs, so the old
and representative-point bars are comparing the same metro areas. Old-only
outputs are shown separately instead of being treated as zero-tract
representative-point metros.

![Tract count distributions](figures/tract_count_distributions.png)

Across the 2,202 common metro/year pairs, the representative-point method has a
lower tract count in 1,536 pairs, the same tract count in 666 pairs, and a
higher tract count in 0 pairs. The average paired tract count falls from 151.06
under the old intersection method to 141.92 under the representative-point
method.

| Method | Average tracts | Median tracts | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| Old intersection, common pairs | 151.06 | 57 | 3 | 4,942 |
| Representative points, common pairs | 141.92 | 49 | 2 | 4,942 |

| Tract-count direction | Common metro/year pairs |
| --- | ---: |
| No change | 666 |
| Fewer tracts with representative points | 1,536 |
| More tracts with representative points | 0 |

For paired outputs, `new_tract_count - old_tract_count` averages -9.14 tracts,
with a median of -6 and a range from -122 to 0. The 75 old-only outputs are
limited to 1970 and 1980: 70 old-only 1970 metros contain 290 total tracts, and
5 old-only 1980 metros contain 19 total tracts.

## 3. Total Population Changes

The population comparisons below also use only common `(year, stem)` outputs.
The old-only metro areas from 1970 and 1980 are described separately, not
treated as zero-population representative-point metros.

![Total population changes](figures/total_population_changes.png)

![Total population scatter by year](figures/total_population_scatter_by_year.png)

Across the 2,202 common metro/year pairs, the representative-point method has a
lower total population in 1,535 pairs, the same total population in 667 pairs,
and a higher total population in 0 pairs.

| Method | Average population | Median population | Min | Max |
| --- | ---: | ---: | ---: | ---: |
| Old intersection, common pairs | 639,381 | 231,214 | 17,522 | 20,140,470 |
| Representative points, common pairs | 600,306 | 199,818 | 8,273 | 20,140,470 |

For paired outputs, `new_total_population - old_total_population` averages
-39,075 people, with a median of -24,816 and a range from -386,348 to 0.

| Year | Common pairs | Old total population | Point total population | Population removed | Population added | Net change |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1970 | 271 | 153,990,409 | 146,728,493 | 7,261,916 | 0 | -7,261,916 |
| 1980 | 379 | 190,970,429 | 174,192,717 | 16,777,712 | 0 | -16,777,712 |
| 1990 | 384 | 237,905,943 | 207,755,075 | 30,150,868 | 0 | -30,150,868 |
| 2000 | 384 | 264,174,649 | 237,223,524 | 26,951,125 | 0 | -26,951,125 |
| 2010 | 392 | 271,595,498 | 266,693,557 | 4,901,941 | 0 | -4,901,941 |
| 2020 | 392 | 289,280,117 | 289,280,117 | 0 | 0 | 0 |

The old-only outputs add another 1,169,059 people in 1970 and 78,837 people in
1980 on the old-intersection side only.

Largest absolute paired population decreases:

| Year | CBSA | Metro area | Population delta | Percent delta |
| --- | ---: | --- | ---: | ---: |
| 1990 | 35620 | New York-Newark-Jersey City, NY-NJ-PA | -386,348 | -2.25% |
| 2000 | 14460 | Boston-Cambridge-Newton, MA-NH | -343,982 | -7.26% |
| 1990 | 14460 | Boston-Cambridge-Newton, MA-NH | -343,575 | -7.67% |
| 2000 | 35620 | New York-Newark-Jersey City, NY-NJ-PA | -332,246 | -1.78% |
| 1990 | 37980 | Philadelphia-Camden-Wilmington, PA-NJ-DE-MD | -332,147 | -5.76% |

Largest percent decreases among pairs with old-intersection population at least
10,000:

| Year | CBSA | Metro area | Population delta | Percent delta |
| --- | ---: | --- | ---: | ---: |
| 1980 | 39460 | Punta Gorda, FL | -31,742 | -79.33% |
| 1990 | 45540 | The Villages, FL | -120,248 | -79.20% |
| 1980 | 25940 | Hilton Head Island-Bluffton, SC | -21,370 | -71.37% |
| 1980 | 25220 | Hammond, LA | -30,377 | -66.98% |
| 1980 | 16540 | Chambersburg-Waynesboro, PA | -60,577 | -65.54% |

## 4. Population Change by Race

Race comparisons use the same common `(year, stem)` rows as the total
population section. `POC` is included as a derived summary and should not be
added to the individual race columns.

![Race population changes](figures/race_population_changes.png)

![Race removed percentages by year](figures/race_removed_percentages_by_year.png)

![Race population outliers](figures/race_population_outliers.png)

All common-pair race changes are removals under the representative-point rule;
there are no added race counts in the current comparison.

The removed percentages use each year's old-intersection race total as the
denominator. `Two or more` has a zero old-intersection total before 2000 in
these inputs, so those percentages are omitted.

| Year | White | Black | American Indian | Asian | Two or more | POC (derived) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1970 | 5.12% | 1.86% | 6.93% | 2.63% |  | 2.03% |
| 1980 | 9.43% | 5.17% | 10.69% | 2.93% |  | 5.07% |
| 1990 | 14.10% | 7.09% | 24.61% | 5.08% |  | 6.95% |
| 2000 | 11.84% | 5.49% | 18.97% | 4.14% | 5.95% | 5.40% |
| 2010 | 2.12% | 0.85% | 5.52% | 0.93% | 1.32% | 1.05% |
| 2020 | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% | 0.00% |

| Race column | Added by points | Removed by points | Net change | Old-only population |
| --- | ---: | ---: | ---: | ---: |
| White | 0 | 76,454,580 | -76,454,580 | 1,162,904 |
| Black | 0 | 5,701,580 | -5,701,580 | 72,653 |
| American Indian | 0 | 987,780 | -987,780 | 4,869 |
| Asian | 0 | 2,398,034 | -2,398,034 | 7,470 |
| Two or more | 0 | 501,588 | -501,588 | 0 |
| POC (derived) | 0 | 9,588,982 | -9,588,982 | 84,992 |

Largest absolute paired race-population decreases:

| Race column | Year | CBSA | Metro area | Population delta | Percent delta |
| --- | --- | ---: | --- | ---: | ---: |
| White | 1990 | 35620 | New York-Newark-Jersey City, NY-NJ-PA | -351,731 | -2.94% |
| Black | 1990 | 17900 | Columbia, SC | -64,261 | -26.83% |
| American Indian | 2000 | 22140 | Farmington, NM | -39,054 | -48.20% |
| Asian | 1990 | 41940 | San Jose-Sunnyvale-Santa Clara, CA | -56,960 | -12.19% |
| Two or more | 2000 | 31080 | Los Angeles-Long Beach-Anaheim, CA | -11,602 | -1.94% |
| POC (derived) | 2000 | 31080 | Los Angeles-Long Beach-Anaheim, CA | -81,784 | -1.37% |

Largest percent paired race-population decreases among rows where the old
race-column population is at least 10,000:

| Race column | Year | CBSA | Metro area | Population delta | Percent delta |
| --- | --- | ---: | --- | ---: | ---: |
| White | 1990 | 45540 | The Villages, FL | -110,208 | -80.86% |
| Black | 1990 | 45540 | The Villages, FL | -7,983 | -61.01% |
| American Indian | 1990 | 42140 | Santa Fe, NM | -10,354 | -78.58% |
| Asian | 1990 | 29740 | Las Cruces, NM | -12,572 | -58.56% |
| Two or more | 2000 | 22900 | Fort Smith, AR-OK | -4,596 | -36.02% |
| POC (derived) | 1980 | 42140 | Santa Fe, NM | -8,129 | -75.65% |
