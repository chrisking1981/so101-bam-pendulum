# Register 41/85 tests, `brutal` kp 32, no load

The file name prefix gives the settings for each run:

| Prefix | Settings |
|---|---|
| `test__` | First replay (up_and_down kp 32) with 85 = 254, 41 = 0 |
| `acc254__` / `acc0__` | Only register 41 written (254, then 0), with 85 left at 254 |
| `r85_0_r41_0__` | 85 = 0, then 41 = 0 (profile off) |
| `r85_254_r41_254__` / `r85_254_r41_0__` | Profile on |

The timing table is in [../README.md](../README.md#finding-2-the-register-85-acceleration-profile-explains-it). After these tests the registers were set back to 85 = 254, 41 = 0.
