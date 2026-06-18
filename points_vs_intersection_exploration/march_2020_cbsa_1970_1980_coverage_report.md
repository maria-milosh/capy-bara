# March 2020 Metro Coverage by 1970 and 1980 Tracts

Generated from the March 2020 CBSA definition shapefiles in `cbsas/defs/` and the tract geometry files in `processed/1970_tracts.shp` and `processed/1980_tracts.shp`.

Puerto Rico metros are included in this report. The comparison covers all 392 March 2020 metro areas in `cbsas/defs/`.

Coverage is measured as area coverage:

```text
area(march_2020 CBSA geometry intersect union(tract geometries)) / area(march_2020 CBSA geometry)
```

A metro can have nonzero coverage from tiny boundary slivers, and a tract is counted as a candidate if it intersects the CBSA geometry.

The coverage metric is metro-level. When this report says "0% coverage" or "below 90% coverage," it is counting metro areas, not individual tracts.

## Main numbers

Using a 90% area-coverage cutoff, only 29% of metro areas (according to the 2020 definition) are close to being fully covered in 1970. 13% of metro areas are not covered at all. I'm using a threshold of 90% coverage to account for small mismatches between tracts and metro areas that we've encountered while working with these data.

1980 tracts cover far more metro areas than 1970 tracts. The most important counts are:

| tract year | metros with 0% coverage | metros below 90% coverage | metros at least 90% covered |
|---:|---:|---:|---:|
| 1970 | 51 of 392 (13.0%) | 277 of 392 (70.7%) | 115 of 392 (29.3%) |
| 1980 | 8 of 392 (2.0%) | 159 of 392 (40.6%) | 233 of 392 (59.4%) |

With Puerto Rico included, 1970 has 51 metro areas with no tract coverage at all and 277 metro areas that do not clear the 90% threshold. By 1980, 8 metro areas still have exactly 0% coverage, all in Puerto Rico, and 159 metros still do not clear the 90% threshold.

| tract year | tract geometries loaded | metros checked | metros >=90% covered | metros <90% covered | metros with 0% coverage | median coverage | mean coverage | area-weighted coverage | population-weighted coverage |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1970 | 34,380 | 392 | 115 (29.3%) | 277 (70.7%) | 51 (13.0%) | 40.3% | 46.3% | 46.6% | 64.3% |
| 1980 | 46,187 | 392 | 233 (59.4%) | 159 (40.6%) | 8 (2.0%) | 99.9% | 75.0% | 71.0% | 84.0% |

The key change is that the median metro moves from only about 40% covered in 1970 to essentially fully covered in 1980. The mean remains lower than the median in 1980 because a smaller set of metros still have very poor coverage.

Population-weighted coverage is higher than the plain mean in both years. That means the largest metro areas tend to be better covered than the typical metro area, though there are important exceptions such as Chicago in both years.

## Coverage Bands

| coverage band | 1970 metro count | 1970 share | 1980 metro count | 1980 share |
|---|---:|---:|---:|---:|
| 0% | 51 | 13.0% | 8 | 2.0% |
| >0% and <50% | 167 | 42.6% | 86 | 21.9% |
| >=50% and <90% | 59 | 15.1% | 65 | 16.6% |
| >=90% | 115 | 29.3% | 233 | 59.4% |

In 1970, more than half of metros are below 50% covered. By 1980, most metros clear 90%, and the number with no coverage drops sharply.

## Threshold Comparison

| threshold | 1970 metros meeting threshold | 1980 metros meeting threshold |
|---:|---:|---:|
| >=50% | 174 (44.4%) | 298 (76.0%) |
| >=75% | 128 (32.7%) | 253 (64.5%) |
| >=90% | 115 (29.3%) | 233 (59.4%) |
| >=95% | 113 (28.8%) | 229 (58.4%) |
| >=99% | 108 (27.6%) | 226 (57.7%) |

The threshold table shows that the improvement is not just a small nudge around the 90% line. The number of metros that are at least 99% covered more than doubles from 1970 to 1980.

## Chicago and New York

| metro | 2020 population | 1970 coverage | 1980 coverage | change | interpretation |
|---|---:|---:|---:|---:|---|
| New York-Newark-Jersey City, NY-NJ-PA | 20,140,470 | 78.2% | 91.6% | +13.5 pts | Crosses the 90% coverage cutoff by 1980. |
| Chicago-Naperville-Elgin, IL-IN-WI | 9,618,502 | 67.7% | 72.8% | +5.0 pts | Improves, but remains well below the 90% cutoff. |

New York and Chicago behave very differently. New York is incomplete in 1970 but becomes mostly covered by 1980. Chicago is still substantially undercovered in 1980, so results using March 2020 Chicago boundaries should be interpreted carefully for both older tract years.

## Large Metro Comparison

Top March 2020 metros by population:

| metro | 2020 population | 1970 candidate tracts | 1980 candidate tracts | 1970 coverage | 1980 coverage | change |
|---|---:|---:|---:|---:|---:|---:|
| New York-Newark-Jersey City, NY-NJ-PA | 20,140,470 | 3,980 | 4,313 | 78.2% | 91.6% | +13.5 pts |
| Los Angeles-Long Beach-Anaheim, CA | 13,200,998 | 1,917 | 2,079 | 99.6% | 100.0% | +0.3 pts |
| Chicago-Naperville-Elgin, IL-IN-WI | 9,618,502 | 1,540 | 1,698 | 67.7% | 72.8% | +5.0 pts |
| Dallas-Fort Worth-Arlington, TX | 7,637,387 | 543 | 658 | 90.2% | 90.4% | +0.2 pts |
| Houston-The Woodlands-Sugar Land, TX | 7,122,240 | 401 | 721 | 92.2% | 100.0% | +7.8 pts |
| Washington-Arlington-Alexandria, DC-VA-MD-WV | 6,385,162 | 668 | 907 | 46.2% | 93.6% | +47.4 pts |
| Philadelphia-Camden-Wilmington, PA-NJ-DE-MD | 6,245,051 | 1,315 | 1,406 | 99.5% | 99.8% | +0.3 pts |
| Miami-Fort Lauderdale-Pompano Beach, FL | 6,138,333 | 418 | 542 | 85.2% | 99.9% | +14.7 pts |
| Atlanta-Sandy Springs-Alpharetta, GA | 6,089,815 | 257 | 453 | 27.0% | 100.0% | +73.0 pts |
| Boston-Cambridge-Newton, MA-NH | 4,941,632 | 717 | 905 | 52.3% | 100.0% | +47.6 pts |

Several large metros are already almost fully covered in 1970, especially Los Angeles, Philadelphia, San Francisco, Riverside, Detroit, Seattle, and San Diego. Others improve dramatically by 1980, especially Atlanta, Washington, Boston, Miami, and New York.

Chicago is the standout large metro that remains far below full coverage in both years.

## Remaining Problem Areas

In 1970, 51 metros have 0% coverage. These include Puerto Rico metros and a mix of mainland metros such as Cape Coral-Fort Myers, Clarksville, Barnstable Town, Bellingham, Burlington-South Burlington, Medford, Chico, Johnson City, Jacksonville NC, and St. Cloud.

In 1980, the 0% coverage cases are all Puerto Rico metros:

| CBSA code | metro |
|---:|---|
| 41980 | San Juan-Bayamón-Caguas, PR |
| 10380 | Aguadilla-Isabela, PR |
| 38660 | Ponce, PR |
| 11640 | Arecibo, PR |
| 41900 | San Germán, PR |
| 32420 | Mayagüez, PR |
| 49500 | Yauco, PR |
| 25020 | Guayama, PR |

The lowest nonzero 1980 coverage examples are still effectively uncovered for practical purposes: Homosassa Springs, FL at 0.0005%, California-Lexington Park, MD at 0.0012%, Barnstable Town, MA at 0.0033%, Sebring-Avon Park, FL at 0.0034%, and The Villages, FL at 0.0050%.

## Takeaways

1. 1970 coverage is not reliable nationally under March 2020 CBSA boundaries. Only 29.3% of metros clear the 90% area-coverage cutoff, and 51 metros have exactly 0% coverage.
2. 1980 is much better, but not complete. 59.4% of metros clear the 90% cutoff, 8 metros have exactly 0% coverage, and the median metro is nearly fully covered.
3. Large-metro results should not be assumed safe just because population-weighted coverage is high. Chicago remains undercovered in both 1970 and 1980.
4. Puerto Rico metros remain uncovered in both tract years in this processed tract set.
5. For older-year metric calculations, it may be useful to filter or flag metro-year pairs below a chosen coverage threshold before comparing segregation statistics across years.
