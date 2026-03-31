# CLI Command Reference

All commands are run via `python3 src/kai-cli.py <command> [args]`.

---

## Global Options

These flags can be added to any command:

| Flag | Description |
|---|---|
| `--db PATH` | Override SQLite database path |
| `--profile PATH` | Override profile.json path |
| `--exercises PATH` | Override exercises.md path |

Example:
```bash
python3 src/kai-cli.py --db /custom/path.db quick-status
```

---

## Quick Reference by Workflow

### Daily Routine

| Time | Action | Command |
|---|---|---|
| Morning | Log last night's sleep | `log-sleep 2025-01-15 23:30 07:00 7.5 --quality good` |
| Morning | Log weight | `log-weight 71.2` |
| After meals | Log food | `log-food "Chicken breast and rice" 550 45 60 12` |
| Before workout | Get suggestion | `suggest-workout --duration 40` |
| During workout | Log each exercise | `log-exercise "Bench Press" "Chest" 135 3 10 --rpe 8` |
| After workout | Log the session | `log-workout "Home Gym" "Chest" 40 "Bench Press, Fly, Push-ups"` |
| Evening | Check daily totals | `daily-summary` |

### Weekly Review

| Action | Command |
|---|---|
| See 7-day nutrition + workouts | `weekly-summary` |
| Check workout coverage | `weekly-plan` |
| Review weight trend | `weight-trend` |
| Review sleep patterns | `sleep-trend` |
| Check strength progression | `strength-trend` |

### Getting Started (First Day)

```bash
# 1. Log your current weight
python3 src/kai-cli.py log-weight 70.0

# 2. Log your first meal
python3 src/kai-cli.py log-food "Breakfast oatmeal with banana" 350 12 55 8

# 3. Get a workout suggestion
python3 src/kai-cli.py suggest-workout

# 4. After working out, log the session
python3 src/kai-cli.py log-workout "Home Gym" "Chest" 35 "Push-ups 3x15, Dumbbell Press 3x10"

# 5. Log individual exercises for strength tracking
python3 src/kai-cli.py log-exercise "Dumbbell Press" "Chest" 40 3 10 --rpe 7

# 6. Check your status
python3 src/kai-cli.py quick-status
```

---

## Logging Commands

### `log-food`

Log a meal or food item.

```
log-food <description> <calories> <protein_g> <carbs_g> <fat_g> [--image PATH] [--notes TEXT]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `description` | string | Yes | Food description |
| `calories` | float | Yes | Calories (kcal) |
| `protein_g` | float | Yes | Protein in grams |
| `carbs_g` | float | Yes | Carbs in grams |
| `fat_g` | float | Yes | Fat in grams |
| `--image` | string | No | Path to food image |
| `--notes` | string | No | Additional notes |

**Example:**
```bash
python3 src/kai-cli.py log-food "Grilled chicken salad" 450 42 20 18 --notes "lunch"
```

**Example output:**
```
Logged food: Grilled chicken salad (450 kcal)

Today's totals (2025-01-15):
  Meals logged: 3
  Calories:     1240.0 kcal
  Protein:      98.0 g
  Carbs:        130.0 g
  Fat:          42.0 g
```

**Tips:**
- When using via WhatsApp, you can just describe the food naturally (e.g., "I had a grilled chicken salad for lunch") and Kai will estimate the macros for you
- For accuracy, include quantities: "200g chicken breast" is more precise than "some chicken"
- Log snacks and drinks too -- they add up

---

### `log-weight`

Log a body weight measurement.

```
log-weight <weight_kg>
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `weight_kg` | float | Yes | Weight in kilograms |

**Example:**
```bash
python3 src/kai-cli.py log-weight 71.2
```

**Example output:**
```
Logged weight: 71.2 kg

Recent weights:
  2025-01-15: 71.2 kg
  2025-01-14: 71.0 kg
  2025-01-12: 70.8 kg
```

**Tips:**
- Weigh yourself at the same time each day (ideally morning, after using the bathroom) for consistent tracking
- Small daily fluctuations (0.5-1 kg) are normal -- focus on the weekly trend

---

### `log-workout`

Log a completed workout session.

```
log-workout <location> <target_muscle> <duration_min> <exercises_json> [--notes TEXT]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `location` | string | Yes | Where (e.g. "Home Gym", "Planet Fitness") |
| `target_muscle` | string | Yes | Primary muscle group |
| `duration_min` | int | Yes | Duration in minutes |
| `exercises_json` | string | Yes | Exercises performed (text or JSON) |
| `--notes` | string | No | Additional notes |

**Valid muscle groups:** Chest, Back, Legs, Shoulders, Biceps, Triceps, Core

**Example:**
```bash
python3 src/kai-cli.py log-workout "Home Gym" "Chest" 35 "Bench Press 3x10, Push-ups 3x15"
```

**Example output:**
```
Logged workout: Chest at Home Gym, 35 min
```

**Tips:**
- Use the same location names consistently (e.g., always "Home Gym" not sometimes "Home" and sometimes "My Garage")
- The `exercises_json` field is free text -- you can write it however you like
- For combined sessions (e.g., Chest + Triceps), log them as separate entries or pick the primary group

---

### `log-sleep`

Log a sleep entry.

```
log-sleep <sleep_date> <bedtime> <wake_time> <duration_hours> [--quality good|ok|bad] [--notes TEXT]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `sleep_date` | string | Yes | Date (YYYY-MM-DD) |
| `bedtime` | string | Yes | Bedtime (e.g. "23:30") |
| `wake_time` | string | Yes | Wake time (e.g. "07:00") |
| `duration_hours` | float | Yes | Hours slept |
| `--quality` | choice | No | good, ok, or bad |
| `--notes` | string | No | Additional notes |

**Example:**
```bash
python3 src/kai-cli.py log-sleep 2025-01-15 23:30 07:00 7.5 --quality good
```

**Example output:**
```
Logged sleep: 2025-01-15 -- 23:30 to 07:00 (7.5h)
```

**Tips:**
- The `sleep_date` is the date you went to bed (even if you woke up the next day)
- Sleep data directly affects workout intensity suggestions -- log it consistently
- Quality ratings: `good` = feel rested, `ok` = decent but not great, `bad` = poor/interrupted sleep

---

### `log-exercise`

Log a single exercise for progressive overload tracking.

```
log-exercise <exercise_name> <muscle_group> <weight_lbs> <sets> <reps> [--rpe FLOAT] [--notes TEXT]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `exercise_name` | string | Yes | Exercise name (e.g. "Bench Press") |
| `muscle_group` | string | Yes | Muscle group (e.g. "Chest") |
| `weight_lbs` | float | Yes | Weight in pounds |
| `sets` | int | Yes | Number of sets |
| `reps` | int | Yes | Reps per set |
| `--rpe` | float | No | Rate of Perceived Exertion (1-10) |
| `--notes` | string | No | Additional notes |

**Example:**
```bash
python3 src/kai-cli.py log-exercise "Bench Press" "Chest" 135 3 10 --rpe 7.5
```

**Example output:**
```
Logged: Bench Press -- 135 lbs x 3 sets x 10 reps, RPE 7.5
```

**Tips:**
- Use consistent exercise names (always "Bench Press", not sometimes "Flat Bench" and sometimes "Bench Press")
- RPE scale: 1 = very easy, 5 = moderate, 7 = challenging, 8 = hard (1-2 reps left), 9 = very hard (1 rep left), 10 = max effort
- Log your working sets (skip warm-up sets unless you want to track them)

---

## Query Commands

### `quick-status`

Quick overview of current state. This is the most useful "at a glance" command.

```
quick-status
```

Shows: last workout, latest weight, last sleep, today's meals and calories.

**Example:**
```bash
python3 src/kai-cli.py quick-status
```

**Example output:**
```
Quick Status:
  Last workout: 2025-01-14 - Chest (40 min)
  Latest weight: 71.0 kg (2025-01-14)
  Last sleep: 2025-01-14 -- 23:30 to 07:00 (7.5h) (good)
  Today's meals: 2 meals, 890.0 kcal
```

**Example output (empty database):**
```
Quick Status:
  Last workout: None
  Latest weight: None
  Last sleep: None
  Today's meals: 0 meals, 0 kcal
```

---

### `daily-summary`

Show nutrition summary for a day.

```
daily-summary [date]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `date` | string | No | Date (YYYY-MM-DD), defaults to today |

**Example:**
```bash
python3 src/kai-cli.py daily-summary
python3 src/kai-cli.py daily-summary 2025-01-14
```

**Example output:**
```
Daily nutrition summary for 2025-01-15:
  Meals logged: 3
  Calories:     1650.0 kcal
  Protein:      118.0 g
  Carbs:        180.0 g
  Fat:          52.0 g

  Daily targets: ~2200 kcal / ~120g protein
  Remaining:    ~550 kcal / ~2g protein
```

**Example output (no food logged):**
```
No food logged for 2025-01-15.
```

---

### `weekly-summary`

Show the last 7 days of nutrition and workout data.

```
weekly-summary
```

**Example:**
```bash
python3 src/kai-cli.py weekly-summary
```

**Example output:**
```
Weekly nutrition summary (last 7 days):
--------------------------------------------------
  2025-01-15: 1650 kcal | P: 118g C: 180g F: 52g (3 meals)
  2025-01-14: 2100 kcal | P: 125g C: 230g F: 65g (4 meals)
  2025-01-13: 1900 kcal | P: 110g C: 200g F: 58g (3 meals)
  2025-01-12: 2250 kcal | P: 130g C: 240g F: 70g (4 meals)
  2025-01-11: (no data)
  2025-01-10: 1800 kcal | P: 105g C: 195g F: 55g (3 meals)
  2025-01-09: 2000 kcal | P: 115g C: 210g F: 62g (3 meals)

Weekly workouts:
  2025-01-14: Chest at Home Gym (40 min)
  2025-01-12: Back at Home Gym (35 min)
  2025-01-10: Legs at Home Gym (45 min)
  Total: 3 workouts this week
```

---

### `weight-trend`

Show weight history.

```
weight-trend [entries]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `entries` | int | No | Number of entries to show (default: 14) |

**Example:**
```bash
python3 src/kai-cli.py weight-trend
python3 src/kai-cli.py weight-trend 7
```

**Example output:**
```
Weight trend (last 14 entries):
  2025-01-15: 71.2 kg
  2025-01-14: 71.0 kg
  2025-01-12: 70.8 kg
  2025-01-10: 70.5 kg
  2025-01-08: 70.7 kg
  2025-01-06: 70.3 kg
  2025-01-04: 70.0 kg
```

---

### `sleep-trend`

Show sleep history and average.

```
sleep-trend [days]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `days` | int | No | Number of days to show (default: 7) |

**Example:**
```bash
python3 src/kai-cli.py sleep-trend
python3 src/kai-cli.py sleep-trend 14
```

**Example output:**
```
Sleep history (last 7 days):
  2025-01-15: 23:30 - 07:00 (7.5h) [good]
  2025-01-14: 00:00 - 06:30 (6.5h) [ok]
  2025-01-13: 23:00 - 07:00 (8.0h) [good]
  2025-01-12: 23:45 - 06:45 (7.0h) [ok]
  2025-01-11: 22:30 - 06:30 (8.0h) [good]

Average sleep: 7.4 hours (5 entries)
```

---

### `last-workout`

Show details of the most recent workout.

```
last-workout
```

**Example:**
```bash
python3 src/kai-cli.py last-workout
```

**Example output:**
```
Last workout:
  Date:     2025-01-14
  Location: Home Gym
  Target:   Chest
  Duration: 40 min
```

**Example output (no workouts logged):**
```
No workouts found.
```

---

## Smart Commands

### `suggest-workout`

Generate an intelligent workout suggestion based on your history, equipment, and sleep.

```
suggest-workout [--duration MINUTES] [--focus MUSCLE]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `--duration` | int | No | Workout duration in minutes (default: 40) |
| `--focus` | string | No | Muscle group focus (see table below) |

**Focus options:**

| Value | Maps to |
|---|---|
| `chest` | Chest |
| `back` | Back |
| `legs` | Legs |
| `shoulders` | Shoulders |
| `biceps` | Biceps |
| `triceps` | Triceps |
| `arms` | Biceps + Triceps |
| `core` / `abs` | Core |
| `upper` | Chest + Back + Shoulders |
| `lower` | Legs + Core |
| `push` | Chest + Shoulders + Triceps |
| `pull` | Back + Biceps |

**Example:**
```bash
python3 src/kai-cli.py suggest-workout --duration 30 --focus push
```

**Example output:**
```
Workout Suggestion (30 min)
Target: Push (Chest + Shoulders + Triceps)
Intensity: Standard (sleep avg: 7.4h -> 3-4 sets x 8-12 reps)

Warm-up (5 min):
  - Arm circles, band pull-aparts

Chest (12 min):
  - Barbell Bench Press: 3 sets x 10 reps
  - Dumbbell Fly: 3 sets x 12 reps

Shoulders (8 min):
  - Dumbbell Shoulder Press: 3 sets x 10 reps

Triceps (5 min):
  - Dips: 3 sets x max reps

Cool-down:
  - Stretch chest, shoulders, triceps
```

**Tips:**
- If you omit `--focus`, the engine auto-selects the most overdue muscle groups
- Use `--duration 20` for a quick session, `--duration 60` for a longer one
- The suggestion adapts to your sleep -- poor sleep means lower volume

---

### `weekly-plan`

Show weekly progress and catch-up suggestions.

```
weekly-plan
```

Shows:
- Workouts done this week vs target
- Muscle groups trained and not yet trained
- Days since each untrained group was last worked
- Suggestions for what to do next

**Example:**
```bash
python3 src/kai-cli.py weekly-plan
```

**Example output:**
```
Weekly Plan
===========
Week: 2025-01-13 to 2025-01-19
Workouts this week: 2 / 3-4 target

Trained this week:
  Chest:   1 session (40 min total)
  Back:    1 session (35 min total)

Not yet trained this week:
  Legs:      last trained 5 days ago  [OVERDUE]
  Shoulders: last trained 4 days ago
  Biceps:    last trained 6 days ago  [OVERDUE]
  Triceps:   last trained 3 days ago
  Core:      last trained 7 days ago  [OVERDUE]

Suggestion: Train Legs and Core next to catch up on overdue groups.
```

**Tips:**
- Run this at the start of each week (Monday) to plan your sessions
- The "OVERDUE" label appears when a muscle group has not been trained in 5+ days
- Use the output to decide which `suggest-workout --focus` to use next

---

### `strength-trend`

Show progressive overload trends.

```
strength-trend [exercise_name] [--limit N]
```

| Argument | Type | Required | Description |
|---|---|---|---|
| `exercise_name` | string | No | Specific exercise (omit for all) |
| `--limit` | int | No | Number of entries (default: 10) |

**Examples:**
```bash
# Summary of all exercises
python3 src/kai-cli.py strength-trend

# Detailed history for one exercise
python3 src/kai-cli.py strength-trend "Bench Press" --limit 20
```

**Example output (all exercises):**
```
Strength Trend Summary
======================
Chest:
  Bench Press:    135 lbs -> 155 lbs (+20 lbs) | 8 entries
  Dumbbell Fly:    25 lbs ->  30 lbs (+5 lbs)  | 5 entries

Back:
  Barbell Rows:   95 lbs -> 115 lbs (+20 lbs)  | 6 entries
  Pull-ups:        0 lbs ->   0 lbs (bodyweight)| 4 entries

Legs:
  Barbell Squats: 135 lbs -> 185 lbs (+50 lbs) | 10 entries
```

**Example output (single exercise):**
```
Bench Press -- Strength History (last 10 entries)
=================================================
  2025-01-14: 155 lbs x 3 sets x 10 reps (RPE 8)
  2025-01-10: 150 lbs x 3 sets x 10 reps (RPE 7.5)
  2025-01-07: 150 lbs x 3 sets x  8 reps (RPE 8)
  2025-01-03: 145 lbs x 3 sets x 10 reps (RPE 7)
  2024-12-30: 145 lbs x 3 sets x  8 reps (RPE 8)
  2024-12-27: 140 lbs x 3 sets x 10 reps (RPE 7)
  2024-12-23: 140 lbs x 3 sets x  8 reps (RPE 7.5)
  2024-12-20: 135 lbs x 3 sets x 10 reps (RPE 7)

Progress: 135 lbs -> 155 lbs (+20 lbs over 8 sessions)
```

**Tips:**
- Use consistent exercise names when logging so the trend lines are clean
- Progressive overload means gradually increasing weight, reps, or sets over time
- If you see a plateau (same weight for many sessions), try adding 1-2 reps before increasing weight
