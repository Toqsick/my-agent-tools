# Research-Table: Galaxy Watch 6 / Wear OS Sensor & Health API Boundaries

> Ursprungssession: 2026-07-19 · Quellenstand: Juli 2026

## SDK-by-SDK evidence table

| API / SDK | Data types accessible | Samsung account? | Samsung Health app? | Samsung proprietary component? | Hard limitations |
|---|---|---|---|---|---|
| **Wear Health Services / AHS** (`androidx.health.services`) | Guaranteed on all W3+: HR, Location, Steps, Distance, Speed, Pace, ElevationGain, TotalCalories. Optional: Swims/laps, Reps, SpO2, SkinTemp, Auto-pause, Sleep state, fall detection. | No | No | No (but optional data types depend on OEM extending them) | Mandatory on W3+. Foreground-only for MeasureClient; ForegroundService type=health for background (Android 14+). Location from watch's own GPS. Galaxy Watch 6 SpO2/SkinTemp via AHS only if Samsung implemented passive monitoring goals. |
| **Health Connect** (`androidx.health.connect`) on the WATCH | None on the watch. 50+ data types (Activity, Body Measurement, Cycle, Nutrition, Sleep, Vitals, Wellness) — **only on companion phone.** | N/A on watch | Required on phone as intermediary | N/A | Samsung FAQ: "Health Connect does not support Wear OS devices." Data flows: Watch → Samsung Health (phone) → Health Connect (phone). Background reads: `READ_HEALTH_DATA_IN_BACKGROUND`. >30-day reads: `READ_HEALTH_DATA_HISTORY`. |
| **Android SensorManager** (`Sensor.TYPE_*`) | TYPE_HEART_RATE, TYPE_HEART_BEAT, TYPE_STEP_COUNTER/DETECTOR, TYPE_ACCELEROMETER, TYPE_GYROSCOPE, TYPE_PRESSURE, TYPE_LOW_LATENCY_OFFBODY_DETECT, TYPE_MAGNETIC_FIELD, TYPE_LIGHT, TYPE_PROXIMITY, TYPE_LINEAR_ACCELERATION, TYPE_GRAVITY, TYPE_ROTATION_VECTOR, TYPE_RELATIVE_HUMIDITY | No | No | No | BODY_SENSORS for HR/beat. Must use wake-up variant (`getDefaultSensor(..., true)`) + ForegroundService + WakeLock for screen-off. HIGH_SAMPLING_RATE_SENSORS is normal protection. Does NOT expose raw ECG/PPG/BIA. |
| **Samsung Health Data SDK** (Android companion) | Aggregated historical data: steps, HR, sleep, exercise, calories, sleep stages, blood oxygen, skin temp, BMI, body composition | **Required** for partner registration (SHA-256). User Samsung account not needed for read. | **Required** — Samsung Health on phone needed | Yes — Health Platform on watch + Samsung Health on phone | Without partner registration: writes fail (SDK_POLICY_ERROR). Developer mode exists (Samsung Health → About → tap version 10× → toggle Data Read). Writes need access code. Deprecation: old Android SDK deprecated 2025-07-31. |
| **Samsung Health Sensor SDK** (Galaxy Watch) v1.4.1 | **Continuous:** Accel_raw@25Hz, PPG_raw@25Hz, HR_processed@1Hz with IBI, SkinTemp (Watch5+). **On-demand:** ECG_raw@500Hz, PPG_raw@100Hz, BIA, MF-BIA (Watch8+), SpO2, SkinTemp, SweatLoss. | **Yes** for partner registration (SHA-256 in Health Platform). User Samsung account not needed. | No (independent of Samsung Health app on phone) | **Yes — Health Platform** (`com.samsung.android.service.health`) is the gatekeeper | Partner registration required for distribution — otherwise `SDK_POLICY_ERROR`. Developer mode: Settings → Apps → Health Platform → title 10×. Watch-only, no emulator. On-demand: foreground only, one at a time, ≤30s. ECG/BIA/SpO2 need user-initiated measurement. |

## Permission landscape

| Permission | Protection | Target API | Notes |
|---|---|---|---|
| `BODY_SENSORS` | dangerous | Current (API 34-35) | Runtime request, user grants for HR/health sensors |
| `BODY_SENSORS_BACKGROUND` | dangerous | API 31+, current | Separate runtime request after foreground grant. On API 31+ "the system can restrict or stop sensor data delivery" without it |
| `FOREGROUND_SERVICE_TYPE_HEALTH` | — | API 29+, mandatory | Must be declared in manifest AND passed in startForeground() call. Crash without it |
| WakeLock | — | all | `PARTIAL_WAKE_LOCK` in ForegroundService `onStartCommand()` |
| Wake-up sensor | — | all | `sensorManager.getDefaultSensor(Sensor.TYPE_HEART_RATE, true)` — `true` arg is critical |
| `HIGH_SAMPLING_RATE_SENSORS` | normal | API 31+ | Needed only for >200 Hz sampling. Also needs BODY_SENSORS or ACTIVITY_RECOGNITION |
| Granular `android.permission.health.READ_*` | dangerous | API 36+ (future) | Replaces BODY_SENSORS. Per-type: READ_HEART_RATE, READ_SPO2, READ_SKIN_TEMPERATURE, READ_HEALTH_DATA_IN_BACKGROUND replaces BODY_SENSORS_BACKGROUND |

## Key sources

| Source | URL | Reliability |
|---|---|---|
| Android Health Services docs | https://developer.android.com/health-and-fitness/health-services | High — official Google |
| AHS Compatibility | https://developer.android.com/health-and-fitness/health-services/compatibility | High — official Google |
| Health Connect data types | https://developer.android.com/health-and-fitness/health-connect/data-types | High — official Google |
| Samsung Health Sensor SDK overview | https://developer.samsung.com/health/sensor/overview.html | High — official Samsung |
| Samsung data specs (sensor types) | https://developer.samsung.com/health/sensor/guide/data-specifications.html | High — official Samsung |
| Samsung Sensor SDK dev mode | https://developer.samsung.com/health/sensor/guide/developer-mode.html | High — official Samsung |
| Samsung Health Connect FAQ | https://developer.samsung.com/health/health-connect-faq.html | **Critical** — confirms Health Connect NOT on Wear OS |
| Samsung blog: continuous HR screen-off | https://developer.samsung.com/galaxy-watch/blog/en/2026/04/23/continuous-heart-rate-tracking-on-galaxy-watch-even-with-the-screen-off | High — official Samsung, from April 2026 |
| Android 16 behavior changes (permissions) | https://developer.android.com/about/versions/16/behavior-changes-16#health-fitness-permissions | High — official Google |
| Android Manifest.permission | https://developer.android.com/reference/android/Manifest.permission | High — official reference |
| Health & Fitness newsletter May 2025 | https://developer.android.com/health-and-fitness/community/newsletters/2025/05 | High — confirms BODY_SENSORS deprecation |
| Health Platform API (Samsung Google) | https://developer.android.com/health-and-fitness/health-services/health-platform | Medium — sparsely documented |
| Galaxy Watch 6 Wear OS 5 update | https://www.androidauthority.com/wear-os-5-galaxy-watch-6-3493724/ | Medium — press |
| Health Platform on Play Store | https://play.google.com/store/apps/details?id=com.samsung.android.service.health | Medium — user reviews show instability |

## Known wrinkles

- Galaxy Watch 6 launched on Wear OS 4; Wear OS 5/One UI 6 Watch rolled out Dec 2024. Wear OS 6 timeline unknown.
- Skin temperature on GW6 is "device-dependent" per AHS compatibility — Samsung docs say Watch5+ "series" which includes Watch6, but treat as verify-on-device.
- Samsung Data SDK is the replacement for the deprecated Android SDK (deprecated July 2025). Old docs at `/health/android/*` are dead.
- URLs in this table were verified 2026-07-19. Expect future rot.
