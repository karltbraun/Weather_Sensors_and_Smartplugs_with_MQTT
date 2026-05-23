# Shelly Smart Plug Analysis Report

**Generated:** 2026-04-02 ~13:10 UTC
**Source:** MQTT broker `vultr2:1883`
**Topic:** `KTBMES/TWIX/+/smartplugs/#`
**Observation window:** ~4 minutes of live data (two collection sessions: 13:07–13:08, 13:09–13:11)

---

## 1. Device Inventory

| Plug | Location | MAC Address | State | Load |
| ---- | -------- | ----------- | ----- | ---- |
| Shelly_Prod | office | shellyplugus-a0a3b3b8e8e0 | ON | Active (~80W) |
| Shelly_Lab_01 | office | shellyplugus-d4d4da090a3c | ON | Active (~37W) |
| Shelly_EV | garage | shellyplugus-d48afc781010 | OFF | Idle (0W) |

**3 smart plugs registered.** 2 are actively carrying load; 1 is switched off.

The topic structure is `KTBMES/TWIX/{location}/smartplugs/{name}/...` — data is published as a flat tree of individual MQTT topics rather than a single JSON payload. Each `NotifyStatus` RPC event fans out across ~15 sub-topics.

---

## 2. Current Power Readings

| Plug | Power (W) | Voltage (V) | Current (A) | Device Temp |
| ---- | --------- | ----------- | ----------- | ----------- |
| Shelly_Prod | 72.6 – 101.8 (avg ~83W) | 124.5 – 124.8 | 0.756 – 1.049 | 49.8 – 50.3°C / 121.6 – 122.5°F |
| Shelly_Lab_01 | 35.5 – 38.8 (avg ~37W) | 124.1 – 124.3 | 0.422 – 0.443 | 42.9 – 43.3°C / 109.2 – 110.0°F |
| Shelly_EV | 0.0 | 123.8 – 124.0 | 0.0 | 38.4 – 38.6°C / 101.1 – 101.5°F |

All three plugs are on a standard US 120V circuit. Voltage readings are consistent and stable across all devices (~124V is normal for a 120V nominal supply).

---

## 3. Lifetime Energy Totals

| Plug | Lifetime Total | Equivalent |
| ---- | -------------- | ---------- |
| Shelly_EV | **1,426,554.9 Wh = 1,426.6 kWh** | Dominant consumer by a wide margin |
| Shelly_Prod | 352,280 Wh = 352.3 kWh | |
| Shelly_Lab_01 | 343,386 Wh = 343.4 kWh | |

The EV charger has consumed more than **four times** the energy of either office plug over its lifetime — consistent with electric vehicle charging being a high-energy, periodic load. The office plugs are closely matched, suggesting similar operational history (likely deployed around the same time).

---

## 4. Load Characterisation

### Shelly_Prod — variable load, ~80W

Power fluctuated between 72.6W and 101.8W across the observation window with no stable baseline. The `by_minute` energy accumulation confirms the same pattern: the two most recently completed minutes consumed approximately **1,430–1,465 mWh** each (87–88W average). The load source is reported as `button`, meaning state changes are driven by the physical button or its default mode.

This variability profile is consistent with an active computing load — a desktop PC, monitor, or similar device whose power draw cycles with processor or display activity.

### Shelly_Lab_01 — stable load, ~37W

Power held tightly in the 35.5–38.8W range throughout the observation window. The `by_minute` history confirms ~600 mWh/minute (~36W) for completed minutes. This is the signature of a device in steady state — a router, NAS, lab instrument, or similar always-on equipment running at a fixed operating point.

### Shelly_EV — off, no charging in progress

Output is `False` and power is 0.0W. The plug is still reporting voltage (~124V), confirming it is powered but switched off. The `by_minute` array is `[0.0, 0.0, 0.0]`, confirming no charging has occurred in at least the last three minutes. The EV is either fully charged, disconnected, or charging is intentionally paused.

---

## 5. Trends Over the Observation Window

### Power (Shelly_Prod)

The load showed a notable dip mid-session:

```text
13:07  ~86W   ████████████████████
13:08  ~75W   ████████████████░░░░  ← dip (CPU idle? screen off?)
13:09  ~83W   ████████████████████
13:10  ~76W   ████████████████░░░░  ← second dip
```

The pattern suggests a device cycling between active and idle states on roughly a 1-2 minute cadence. No load shedding or fault events were observed.

### Device Temperature

All three plug temperatures were stable throughout the window:

- Shelly_Prod: 49.9 ± 0.2°C (highest, proportional to load)
- Shelly_Lab_01: 43.1 ± 0.2°C (moderate, stable load)
- Shelly_EV: 38.5 ± 0.1°C (lowest, no load — ambient warmth only)

The temperature ordering directly tracks load: higher power = higher plug temperature, as expected.

### Total energy accumulation rate

Shelly_Prod accumulated approximately **2.6 Wh** over the 2-minute second session (352279.85 → 352282.45). At that rate, projected hourly consumption is ~78 Wh/hr, or about 1.9 kWh/day if running continuously.

Shelly_Lab_01 accumulated approximately **1.0 Wh** over the same window, consistent with its ~37W average. Projected: ~37 Wh/hr, ~0.9 kWh/day.

---

## 6. Anomalies and Concerns

### 6a. Shelly_Lab_01 source is persistently `overvoltage_clear` (MEDIUM)

Every single status event from Shelly_Lab_01 carries `switch:0/source = overvoltage_clear`. This indicates the plug has experienced an overvoltage protection trip and has entered a recovery/cleared state — and is reporting it as the trigger for every subsequent status update.

The measured line voltage (~124.2V) is within the normal 120V US supply range, so the overvoltage event was likely a transient spike rather than a sustained condition. However, the persistence of this source label across all events (rather than reverting to `button` or `timer`) suggests the device has not fully reset its event state since the trip occurred. This is worth monitoring — a sustained or recurring overvoltage condition could damage connected equipment.

### 6b. Shelly_Prod power variability is high relative to average

The range of 72.6W to 101.8W (a 40% swing around the mean) in under 2 minutes is notable. While consistent with a computing load, if Shelly_Prod is powering sensitive or production equipment (the name "Prod" suggests this), unexpected load spikes could indicate thermal issues or software activity worth correlating with system logs.

### 6c. Shelly_EV publish rate is very low

Only 2 event messages were received from Shelly_EV across the entire observation window. This is expected behaviour when the switch output is `False` — the device has less to report. However, it means the data stream provides limited visibility into the EV plug's state. If the EV begins charging, event frequency should increase.

---

## 7. Correlations

- **Device temperature correlates with load** across all three plugs. The rank order (EV < Lab_01 < Prod) exactly mirrors the power rank order. No plug shows anomalous self-heating beyond what the load would predict.
- **Voltage is consistent across locations.** The garage plug (Shelly_EV, 123.9V) reads very slightly lower than the office plugs (~124.6V), which is consistent with a longer or heavier-gauge circuit run to the garage. The difference (~0.7V, 0.6%) is negligible and within normal variation.
- **Shelly_Lab_01 and Shelly_Prod lifetime totals are close** (343 vs 352 kWh), suggesting they have been running under similar conditions for a similar duration. Their current loads are very different, suggesting they power different types of equipment.

---

## 8. Publish Rate and Data Structure

| Plug | Approx. Interval | Trigger |
| ---- | ---------------- | ------- |
| Shelly_Prod | ~2 seconds | Power change events (`button` mode) |
| Shelly_Lab_01 | ~8 seconds | Post-overvoltage periodic updates |
| Shelly_EV | Infrequent | Loopback/scheduled only (no load changes) |

Each status event publishes ~15 individual MQTT sub-topics under the plug's path. Consumers that want a consistent snapshot must correlate by `rpc/ts` to group the sub-topics belonging to a single event. The `rpc/` and `switch:0/` subtrees often duplicate fields (`apower`, `current`, `total`, `by_minute`) — the `switch:0/` subtree is the authoritative source for switch state.

### `by_minute` array interpretation

The `by_minute` field is a 3-element array: `[current_minute_accumulating, prev_complete_minute, prev_prev_complete_minute]` in **milliwatt-hours (mWh)**. To derive average wattage for a completed minute: divide by 1000 to get Wh, then multiply by 60 (since it represents one minute). For example, 1464 mWh ÷ 1000 × 60 = **87.8W average** for that minute.

---

## 9. Insights and Recommendations

| Priority | Finding | Recommendation |
| -------- | ------- | -------------- |
| MEDIUM | Shelly_Lab_01 persistently shows `overvoltage_clear` as event source | Investigate whether an overvoltage event occurred; consider power-cycling the plug to reset event state; monitor for recurrence |
| MEDIUM | Shelly_Prod load cycles significantly (~30W swing) | If powering production equipment, correlate power spikes with system activity logs to confirm the pattern is benign |
| LOW | Shelly_EV infrequent publishing | Expected for an off/idle plug; dashboards should not rely on frequent updates from this device |
| LOW | Sub-topic fan-out creates ~15 messages per event | Consumers should group by `rpc/ts` to reconstruct a coherent snapshot; prefer `switch:0/` subtree over `rpc/` for switch metrics |
| INFO | EV lifetime energy (1,426 kWh) dwarfs office plugs | Useful baseline for understanding EV energy cost; at ~0.15 USD/kWh, this represents roughly $214 in charging costs over the meter's lifetime |

---

## 10. Suitability for AI/Dashboard Use

The Shelly data stream is well-suited for automated analysis with the following notes:

1. **No sentinel values** — unlike the weather sensors, all fields carry real data; `-999` was not observed in this stream
2. **Sub-topic structure requires join logic** — group messages by `rpc/ts` to reconstruct a single event snapshot
3. **`switch:0/` is the authoritative subtree** for switch state; `rpc/`-level fields are secondary/summary
4. **`total` is a cumulative Wh counter** — compute deltas between readings to get interval consumption; do not use raw values as an instantaneous metric
5. **`by_minute[0]` is a partial accumulator** — only the second and third elements represent complete minutes and are safe for power-averaging
6. **The `source` field carries diagnostic value** — `overvoltage_clear`, `button`, and `loopback` reveal the reason for each status update and can surface fault conditions

The stream supports: real-time power dashboards, energy consumption trending, overvoltage/fault alerting, EV charge-start/stop detection, and per-minute energy accounting.

---

*Data collected via `mosquitto_sub` from `vultr2:1883`, topic `KTBMES/TWIX/+/smartplugs/#`, 2026-04-02 13:07–13:11.*
