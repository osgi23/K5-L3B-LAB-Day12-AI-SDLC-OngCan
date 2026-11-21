# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to Semantic Versioning.

## [Phase 3] - 2026-11-21
### Breaking Changes
- **Item-based Inventory**: Replaced counted inventory dictionary `{"items": {"kind": count}}` with individual item array `{"items": [{"id": "I1", "kind": "ca_linh", "fresh": 100}, ...]}`.
- Contract v1.2 strictly rejects counted inventory format with exit code 2 (`BadInput`).
- `customers[].reserved` in restaurant simulation converted from ingredient count dictionary to list of item IDs `["I1", "I3"]`.
- `cook_started.data.items` changed from array of kind strings to array of individual item objects sorted by `kind` then `id`.
- `lost` array in `monster_hit` and `faint` events changed from kind strings to individual item objects in LIFO order.

### Added
- **Freshness Lifecycle & Decay**:
  - Freshness `fresh` tracked on each item in range $[0, 100]$.
  - Gather hold decay rate: 0.5 per second ($-0.5 / 60$ per tick).
  - Restaurant stock decay rate: 0.25 per second ($-0.25 / 60$ per tick), including reserved stock.
  - Decay freezes when the game is paused. Cooked dishes and shop stock do not decay.
- **Spoiled Events**:
  - Threshold `fresh < 30`. Items with `fresh < 30` cannot be cooked.
  - Event `spoiled` emitted once when transitioning from $\ge 30$ to $< 30$: `{"item_id": id, "kind": kind, "location": "hold" | "stock"}`. Multiple spoiled items in the same tick are emitted sorted by `item_id`.
- **Re-reservation on Spoiling**:
  - If any reserved ingredient spoils while customer is waiting, releases all reserved items and attempts to re-reserve freshest available items once (processed in order of `order_tick` then `table_id`).
  - If re-reservation fails, sets `order_status = "unfulfillable"`.
- **Dynamic Pricing based on Freshness**:
  - At cooking start, base price is calculated dynamically as `floor(listed_price * avg_fresh / 100)`.
  - Tips ($20\%$) are calculated based on this dynamic base price.
- **HUD Freshness Display**:
  - Web client displays item freshness percentages and visual status tags for fresh vs spoiled ingredients.

## [Phase 2] - 2026-11-20
### Added
- Multi-day cycle (`DaySim`) supporting 1 to 5 days: DayIntro -> Gather -> Quan -> Shop.
- Upgrades system at end-of-day Shop for Oxygen and HP.
- Pause/resume mechanics with `paused` and `resumed` event emissions.
- Monster patrol, chase, and recoil behavior with LIFO item loss on hit.

## [Phase 1] - 2026-11-20
### Added
- Core 2D simulation for morning diving & gathering (`GatherSim`).
- Core 2D simulation for evening floating restaurant (`QuanSim`).
- Headless runner with deterministic event logging and snapshotting (`JsonlWriter`).
- Live browser server for interactive gameplay.
