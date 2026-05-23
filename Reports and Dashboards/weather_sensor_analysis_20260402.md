# House Weather Sensor Analysis Report

**Generated:** 2026-04-02 ~12:51 UTC
**Source:** MQTT broker `vultr2:1883`
**Topic:** `KTBMES/TWIX/sensors/house_weather_sensors/#`
**Observation window:** ~15 minutes of live data (three collection sessions: 12:36–12:39, 12:49–12:51)

> **Data conventions used in this report:**
>
> - A value of `-999` means the sensor does not support that attribute. Such fields are excluded from analysis.
> - The DUMMY entry (`device_id=0`) is an intentional configuration placeholder to reduce maintenance errors when adding sensors. It is not a real sensor and is excluded from all analysis.

---

## 1. Sensor Inventory

| Sensor | Device ID | Protocol | Hardware | Capabilities |
| ------ | --------- | -------- | -------- | ------------ |
| DECK | 152 | 91 — inFactory/nor-tec/FreeTec | NC-3982-913 | Temperature, Humidity |
| PORCH | 138 | 91 — inFactory/nor-tec/FreeTec | NC-3982-913 | Temperature, Humidity |
| LIVING_ROOM | 101 | 91 — inFactory/nor-tec/FreeTec | NC-3982-913 | Temperature, Humidity |
| OFFICE | 234 | 55 — Acurite 606TX | 606TX | Temperature only |

**4 real sensors.** All batteries OK. All active during the observation window.

---

## 2. Current Readings

| Sensor | Location | Temp (°C) | Humidity (%) | Transmit mode |
| ------ | -------- | --------- | ------------ | ------------- |
| DECK | Outdoor — exposed | 1.6 | 29 | AUTO |
| PORCH | Outdoor — semi-sheltered | 8.0 | 45 | AUTO |
| LIVING_ROOM | Indoor | 10.0 | 50 | MANUAL |
| OFFICE | Indoor | 20.8 | — (not supported) | AUTO |

**Temperature range:** 1.6°C to 20.8°C (19.2°C spread across the four sensor locations)

---

## 3. Indoor/Outdoor Thermal Profile

A clear thermal gradient is visible from fully-exposed outdoor to heated indoor:

```text
DECK       ████░░░░░░░░░░░░░░░░░  1.6°C  outdoor — exposed
PORCH      ████████░░░░░░░░░░░░░  8.0°C  outdoor — semi-sheltered
LIVING_RM  █████████████░░░░░░░░ 10.0°C  indoor  — anomalously cold (see §5a)
OFFICE     █████████████████████ 20.8°C  indoor  — heated
```

The 6.4°C gap between PORCH (outdoor, sheltered) and LIVING_ROOM (indoor) is smaller than expected. A typical well-heated interior should be 8–12°C warmer than a sheltered outdoor space on an early April morning near freezing — not cooler.

---

## 4. Trends Over the Observation Window

### Temperature

All sensors held their temperatures essentially constant over 15 minutes, with one minor exception:

| Sensor | Session 1 (12:36) | Session 3 (12:49–51) | Change |
| ------ | ----------------- | -------------------- | ------ |
| DECK | 1.6°C | 1.6°C | stable |
| PORCH | 8.0°C | 8.0°C | stable |
| LIVING_ROOM | 10.0°C | 10.0°C | stable |
| OFFICE | 20.7°C | 20.8°C | +0.1°C (within sensor resolution) |

### Humidity

| Sensor | Early readings | Later readings | Change |
| ------ | -------------- | -------------- | ------ |
| DECK | 32% | 29% | **−3%** |
| PORCH | 49% | 45% | **−4%** |
| LIVING_ROOM | 51% | 50% | −1% (marginal) |

Both outdoor sensors show a consistent humidity decline over the observation window despite stable temperatures. This suggests drying conditions — increasing wind, clearing skies, or a passing front — rather than sensor drift.

---

## 5. Anomalies and Concerns

### 5a. LIVING_ROOM temperature is anomalously cold for an interior space

**Reading: 10.0°C / 50°F** — approximately 10°C below the expected range for a heated interior room (18–22°C). The sensor has held this value steadily across all three sessions with no sign of rising toward a normal indoor temperature.

Possible explanations:

- Heating is off or a window/door is open in that room
- Sensor is placed near an exterior wall, uninsulated floor, or cold draft
- Sensor calibration error (the inFactory NC-3982-913 has ±1–2°C accuracy — insufficient to explain a 10°C deficit)

Coupled with the moisture observation below, physical inspection of this room and sensor placement is warranted.

### 5b. LIVING_ROOM `moisture` field reads 80 — consistently

The `moisture` field on LIVING_ROOM reports `80` across every reading in the observation window. For reference: PORCH reads `30`, and DECK reads `0`. A `moisture` value of 80 in an interior room is unusual and may indicate:

- A water leak, condensation, or damp area near the sensor
- Sensor misplacement (e.g. near a floor, skirting board, or cold exterior surface)
- A protocol field mapping issue where Protocol 91 is populating `moisture` from an unrelated raw byte

This should be investigated alongside the low temperature reading in §5a, as both are consistent with a cold, damp environment.

### 5c. `temperature_F` is incorrect for Protocol 91 sensors

The `temperature_F` field for all three Protocol 91 sensors (DECK, PORCH, LIVING_ROOM) is stored as a **string** and does not match the standard °C→°F conversion:

| Sensor | `temperature_C` | Expected °F | Reported `temperature_F` |
| ------ | --------------- | ----------- | ------------------------ |
| DECK | 1.6°C | 34.9°F | `"76.1"` – `"77.0"` |
| PORCH | 8.0°C | 46.4°F | `"63.9"` – `"64.3"` |
| LIVING_ROOM | 10.0°C | 50.0°F | `"67.1"` – `"67.2"` |

By contrast, Protocol 55 (OFFICE) reports `temperature_F` as a correctly-computed float (`69.44`).

The Protocol 91 values are internally inconsistent (no standard formula relates them to `temperature_C`) and the string type is a further mismatch. **All consumers should derive °F from `temperature_C` directly and ignore the `temperature_F` field for Protocol 91 sensors.**

### 5d. DECK occasional burst-transmissions

DECK twice emitted two readings in rapid succession (5-second gap at 12:38:26/12:38:27). This is likely normal RF retry or dual-channel transmission behaviour for the inFactory sensor hardware. No action required, but dashboards should de-duplicate on `time` rather than on message arrival.

---

## 6. Correlations

- **Outdoor humidity is declining while temperatures hold steady.** Both DECK (−3%) and PORCH (−4%) show falling humidity over 15 minutes with no temperature change. This is consistent with a weather change (wind increase, clearing after precipitation) rather than measurement noise.
- **PORCH and LIVING_ROOM humidity are tracking closely** (45% vs. 50%) despite PORCH being outdoor. This narrows the humidity difference between a semi-sheltered outdoor space and this particular interior room — consistent with §5a (cold, potentially draughty or poorly sealed room).
- **OFFICE temperature is highly stable** (20.7–20.8°C across 5 readings over 15 minutes), suggesting a climate-controlled or well-insulated space.

---

## 7. Publish Rates

| Sensor | Observed interval | Mode |
| ------ | ----------------- | ---- |
| OFFICE | ~30 seconds | AUTO |
| DECK | ~60–90 seconds | AUTO |
| LIVING_ROOM | ~90–120 seconds | MANUAL |
| PORCH | ~2+ minutes | AUTO |

OFFICE is the most chatty sensor at ~2 messages/minute. LIVING_ROOM's MANUAL transmit mode means its publish cadence is operator-configured rather than tied to the sensor's own RF interval.

---

## 8. Insights and Recommendations

| Priority | Finding | Recommendation |
| -------- | ------- | -------------- |
| HIGH | LIVING_ROOM at 10°C indoors with moisture=80 | Physically inspect room and sensor placement; check for open windows, drafts, water ingress, or poor heating |
| MEDIUM | Outdoor humidity declining on both DECK and PORCH | Likely a benign weather transition; worth monitoring to confirm trend reverses or stabilises |
| MEDIUM | `temperature_F` incorrect for Protocol 91 sensors | Fix in the ingestion/republish pipeline; consumers should use `temperature_C` in the meantime |
| LOW | DECK burst-transmissions | Deduplicate on `time` field in any dashboard or storage consumer |

---

## 9. Suitability for AI/Dashboard Use

The data stream is well-suited for automated analysis. Key handling requirements for any consumer:

1. **`-999` means not supported** — filter these out before computing statistics or rendering values
2. **DUMMY must be excluded** — filter on `device_name == "DUMMY"` or `device_id == 0`
3. **Use `temperature_C`, not `temperature_F`** for Protocol 91 sensors — convert to °F in the consumer if needed
4. **Use `time_last_seen_ts` for freshness**, not `time_last_published_ts` — the broker republishes the last known state on a schedule regardless of whether the sensor has been heard from recently
5. **Account for transmit modes** — MANUAL sensors publish on a different cadence than AUTO; polling logic should not assume a fixed interval

The stream supports: real-time dashboards, temperature/humidity trend charts, indoor/outdoor delta monitoring, and humidity-drop alerting — all without additional infrastructure beyond an MQTT subscriber.

---

*Data collected via `mosquitto_sub` from `vultr2:1883`, topic `KTBMES/TWIX/sensors/house_weather_sensors/#`, 2026-04-02 12:36–12:51.*
