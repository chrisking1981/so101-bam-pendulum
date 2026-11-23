# C044 horn-only matrix

12 of 20 combinations have complete traces. All use D=32. The compound sine uses 90% amplitude.

| Pattern | P=4 | P=8 | P=16 | P=32 |
|---|---|---|---|---|
| up_and_down | [Complete](20261123-114316-horn-lower-gains/p4-up_and_down.json) | [Complete](20261123-114316-horn-lower-gains/p8-up_and_down.json) | [Complete](20261123-114316-horn-lower-gains/p16-up_and_down.json) | [Complete](20261123-114225-horn-slow/p32-up_and_down.json) |
| lift_and_drop | [Complete](20261123-114316-horn-lower-gains/p4-lift_and_drop.json) | [Complete](20261123-114316-horn-lower-gains/p8-lift_and_drop.json) | [Complete](20261123-114316-horn-lower-gains/p16-lift_and_drop.json) | [Complete](20261123-114225-horn-slow/p32-lift_and_drop.json) |
| sin_sin-90pct | [Complete](20261123-114439-horn-compound/p4-sin_sin-90pct.json) | [Complete](20261123-114439-horn-compound/p8-sin_sin-90pct.json) | [Complete](20261123-114439-horn-compound/p16-sin_sin-90pct.json) | [Complete](20261123-114029-horn-matrix/p32-sin_sin-90pct.json) |
| sin_time_square | Pending | Pending | Pending | Pending |
| brutal | Pending | Pending | Pending | Pending |

The full-frequency sweep has stopped on 4.8 V at P=4 and P=32 with the current nominal 5 V supply. Partial curves do not count toward completion.

The abrupt step also stopped at P=4 on a 4.6 V / 162 raw current report. [Partial recording](20261123-114630-horn-step-sweep/README.md).

[Voltage, current and angle around the three stops](horn-supply-diagnostic.md).
