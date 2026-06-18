# Points vs. Intersection Exploration

This folder documents the investigation of differences between `cbsas`
(representative-point tract selection) and `old_cbsas` (polygon-intersection
tract selection, as was done originally).

The main question is what kinds of tracts are dropped when switching from area
intersection to representative points. Most dropped tracts have tiny overlaps
with their old metro areas, which is expected. A smaller set has substantial
area overlap, so this folder keeps the scripts, tables, and maps used to decide
whether those are true assignment failures or acceptable boundary-tolerance
cases.

The current outcome of the investigation is implemented in
`pipeline/overlaps.py`: assign tracts by their ordinary
`geometry.representative_point()`, but query CBSA boundaries with `contains` (later changed to `covers`
and applying a 75 meter boundary buffer, to account for borderline cases that arguably should be included: the buffer is intended to recover
tracts whose representative point falls just outside a metro polygon because of
small historical tract/CBSA boundary mismatches).

## Files

These are the lightweight analysis scripts and tables for the
`points-vs-intersection-analysis` branch:

- `README.md`: this guide to the folder.
- `plan.md`: a plan of the points-vs-intersection analysis, it outlines what should be compared and what changes to look at.
- `*.py`: scripts used to compare assignments, diagnose missing files, compute
  excluded-tract overlap areas, and generate figures.
- `march_2020_cbsa_1970_1980_coverage_report.md`: written summaries and comparison report. Look here for a summary of changes.
- `excluded_tract_overlap_areas.csv`: tract-level table of tracts excluded by
  the representative-point method, with their old metro overlap area and
  overlap percent.
- `excluded_tract_overlap_summary.csv`: summary of excluded tract overlap by
  year and metro.
- `high_overlap_failure_diagnostics.csv`: diagnostics for excluded tracts with
  substantial old-metro overlap, including representative-point distance to the
  CBSA boundary and geometry/component checks. This is helpful to see cases that were very close to be included by points but still were not included and inspect the reasons for that.
- `figures/high_overlap_case_maps/`: maps for the specific high-overlap cases
  inspected while deciding whether a distance rule should rescue them.
- `figures/high_overlap_75m_extra_maps/`: maps for the additional cases that a
  75 meter tolerance would include, plus a contact sheet and manifest.

