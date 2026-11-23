# C044 P4 abrupt step on the RD6006

Same horn-only profile as the [5 V attempt](../20261123-114630-horn-step-sweep/README.md), P=4, D=32. Physical clearance and bare horn confirmed by the onsite operator. RD6006 set to 7.40 V / 1.00 A.

The original 5 V attempt stopped on 4.6 V / raw current 162. The RD6006 attempt stopped at 1.630 s on a 9.3 V readback from the servo, above 8.4 V. Lowest servo readback before and including the stop: 5.6 V. The RD6006 USB samples during the same interval reported 7.31–7.38 V with sampled peak current 0.147 A. These are asynchronous readbacks and cannot rule out a shorter transient at the servo. No circuit-level cause is established.

P=32, D=32, I=0, lock=1 and torque off were verified at the end. The unpowered shaft coasted to 3041 ticks, 10 ticks beyond the configured powered ceiling of 3031. The highest commanded target was 2949 ticks. The recording is partial and must not count toward the 20-run matrix. Resolve the voltage excursion and verify safe stopping travel before repeating this abrupt profile.
