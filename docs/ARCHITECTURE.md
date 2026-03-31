# Architecture

## System Overview

```
+------------------------------------------------------------------+
|                        AI Fitness Coach                           |
+------------------------------------------------------------------+
|                                                                   |
|  +-----------+     +-------------------+     +----------------+   |
|  |           |     |                   |     |                |   |
|  |  WhatsApp +---->+ Claude Code +     +---->+ kai-cli.py     |   |
|  |  (User)   |     | WhatsApp Plugin   |     | (CLI)          |   |
|  |           |     |                   |     |                |   |
|  +-----------+     +--------+----------+     +-------+--------+   |
|                             |                        |            |
|                             v                        v            |
|                    +--------+----------+     +-------+--------+   |
|                    |                   |     |                |   |
|                    | group-config.md   |     | db_manager.py  |   |
|                    | (Kai persona +    |     | (SQLite layer) |   |
|                    |  tool definitions)|     |                |   |
|                    +-------------------+     +-------+--------+   |
|                                                      |            |
|  +-----------+                               +-------+--------+   |
|  |           |                               |                |   |
|  |  Cron Job +----> workout-reminder.sh ---->+ kai_health.db  |   |
|  |  (daily)  |     (fetches status,          | (SQLite file)  |   |
|  |           |      sends via Claude)        |                |   |
|  +-----------+                               +----------------+   |
|                                                                   |
|  +-------------------+     +-------------------+                  |
|  |                   |     |                   |                  |
|  | profile.json      |     | exercises.md      |                  |
|  | (user config)     |     | (70+ exercises)   |                  |
|  +-------------------+     +-------------------+                  |
|                                                                   |
+------------------------------------------------------------------+
```

### Component Summary

| Component | File | Role |
|---|---|---|
| CLI Interface | `src/kai-cli.py` | Command-line tool for all data operations |
| Database Layer | `src/db_manager.py` | SQLite CRUD operations |
| Database | `data/kai_health.db` | Local SQLite database (all user data) |
| Exercise Database | `src/exercises.md` | 70+ exercises by muscle group and equipment |
| User Profile | `config/profile.json` | Goals, equipment, nutrition targets |
| Environment Config | `.env` | Paths, timezone, WhatsApp chat ID |
| Group Config | `config/group-config.example.md` | Kai's WhatsApp persona and tool definitions |
| Cron Reminder | `cron/workout-reminder.sh` | Automated WhatsApp reminder script |
| Cron Installer | `cron/install-cron.sh` | Installs cron entries for reminders |
| Setup Script | `setup.sh` | One-click project setup |

---

## Components (Detailed)

### 1. kai-cli.py (CLI Interface)

The main entry point. It provides a command-line interface for all health/fitness operations.

**Responsibilities:**
- Parse command-line arguments via `argparse` with subcommands
- Resolve configuration (CLI flags > env vars > .env file > defaults)
- Format and display output for both human reading and Claude consumption
- Implement smart features (workout suggestions, weekly planning)

**Key design decisions:**
- Uses `argparse` with subcommands for a clean CLI experience
- All path configuration is externalized (no hardcoded paths)
- Loads `.env` file from project root automatically on startup
- Each command function receives `args` and resolves its own DB/profile paths
- No external dependencies -- uses only Python standard library

**Command categories:**

```
kai-cli.py
  |
  +-- Logging Commands
  |     +-- log-food         (insert into food_logs)
  |     +-- log-weight       (insert into body_metrics)
  |     +-- log-workout      (insert into workout_logs)
  |     +-- log-sleep        (insert into sleep_logs)
  |     +-- log-exercise     (insert into exercise_logs)
  |
  +-- Query Commands
  |     +-- quick-status     (aggregates across all tables)
  |     +-- daily-summary    (reads food_logs for a day)
  |     +-- weekly-summary   (reads food_logs + workout_logs for 7 days)
  |     +-- weight-trend     (reads body_metrics history)
  |     +-- sleep-trend      (reads sleep_logs history)
  |     +-- last-workout     (reads latest workout_logs entry)
  |
  +-- Smart Commands
        +-- suggest-workout  (reads profile + workout_logs + sleep_logs + exercises.md)
        +-- weekly-plan      (reads profile + workout_logs + missed muscle groups)
        +-- strength-trend   (reads exercise_logs progression)
```

### 2. db_manager.py (Database Layer)

Standalone SQLite database module. All functions accept a `db_path` argument -- no global state.

**Design principles:**
- **Pure functions**: Each function opens and closes its own connection
- **No global state or singletons**: Every function takes `db_path` as a parameter
- **Returns Python dicts/lists**: Not raw database rows
- **Graceful error handling**: Returns `None` or empty lists on error (never raises)
- **Self-contained**: Can be used independently of `kai-cli.py`

**Function reference:**

| Function | Table | Operation | Returns |
|---|---|---|---|
| `init_health_db()` | body_metrics, food_logs, sleep_logs | CREATE TABLE | status string |
| `init_workout_db()` | workout_logs, exercise_logs | CREATE TABLE | status string |
| `insert_body_metrics()` | body_metrics | INSERT | status string |
| `get_latest_body_metrics()` | body_metrics | SELECT (latest) | dict or None |
| `get_body_metrics_history()` | body_metrics | SELECT (N entries) | list of tuples |
| `insert_food_log()` | food_logs | INSERT | status string |
| `get_daily_nutrition_summary()` | food_logs | SELECT + SUM | dict or None |
| `insert_sleep_log()` | sleep_logs | INSERT | status string |
| `get_sleep_history()` | sleep_logs | SELECT (N days) | list of dicts |
| `get_average_sleep()` | sleep_logs | SELECT + AVG | dict or None |
| `insert_workout_log()` | workout_logs | INSERT | status string |
| `get_recent_workouts()` | workout_logs | SELECT (N entries) | list of dicts |
| `get_last_workout_info()` | workout_logs | SELECT (latest) | dict or None |
| `get_weekly_workout_count()` | workout_logs | SELECT + COUNT | dict |
| `get_weekly_volume_by_muscle()` | workout_logs | SELECT + GROUP BY | list of dicts |
| `get_missed_muscle_groups()` | workout_logs | SELECT + compare | list of dicts |
| `insert_exercise_log()` | exercise_logs | INSERT | status string |
| `get_exercise_history()` | exercise_logs | SELECT (N entries) | list of dicts |
| `get_strength_summary()` | exercise_logs | SELECT (first vs latest) | list of dicts |
| `get_quick_status()` | all tables | SELECT (aggregated) | dict |

### 3. exercises.md (Exercise Database)

A Markdown file containing 70+ exercises organized by muscle group and equipment type.

**Format:**
```markdown
## Muscle Group
### Equipment: Type
- Exercise Name
```

This format is parsed by `_parse_exercises_md()` in kai-cli.py into a nested dictionary:
```python
{
  "Chest": {
    "Barbell": ["Barbell Bench Press", "Incline Barbell Press"],
    "Dumbbell": ["Dumbbell Bench Press", "Incline Dumbbell Press", "Dumbbell Fly"],
    "Cable": ["Cable Crossover"],
    "Machine": ["Chest Press Machine", "Pec Deck Fly Machine"],
    "Bodyweight": ["Push-ups", "Dips"]
  },
  "Back": { ... },
  "Shoulders": { ... },
  "Biceps": { ... },
  "Triceps": { ... },
  "Legs": { ... },
  "Core": { ... }
}
```

**Muscle groups covered**: Chest, Back, Shoulders, Biceps, Triceps, Legs, Core (7 groups)

**Equipment types**: Barbell, Dumbbell, Cable, Machine, Bodyweight (5 types)

### 4. profile.json (User Profile)

JSON file containing the user's fitness profile, goals, and equipment.

Used by:
- `suggest-workout` -- Equipment determines available exercises; goals affect set/rep schemes
- `weekly-plan` -- Frequency target and muscle rotation
- `daily-summary` -- Nutrition targets for remaining calorie calculations

### 5. Cron Reminders (workout-reminder.sh)

A shell script that:
1. Sources `.env` for configuration
2. Runs `kai-cli.py quick-status` to get current fitness state
3. Runs `kai-cli.py last-workout` to get last session details
4. Passes both outputs to Claude Code with a prompt defining Kai's reminder persona
5. Claude generates a context-aware, personalized message
6. Sends it to the WhatsApp group via the WhatsApp channel plugin

---

## Database Schema

All tables live in a single SQLite file: `data/kai_health.db`

### body_metrics

Stores weight and body composition measurements.

```sql
CREATE TABLE body_metrics (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         DATETIME DEFAULT CURRENT_TIMESTAMP,  -- when the entry was logged
    fetch_timestamp   DATETIME,          -- when the measurement was taken (if different)
    weight_kg         REAL,              -- body weight in kilograms
    body_fat          REAL,              -- body fat percentage
    bmi               REAL,              -- body mass index
    muscle_mass       REAL,              -- muscle mass (kg or percentage)
    water_percentage  REAL,              -- body water percentage
    bone_mass         REAL,              -- bone mass
    basal_metabolism  REAL,              -- basal metabolic rate (kcal)
    visceral_fat      REAL,              -- visceral fat level
    protein           REAL               -- protein percentage
);
```

> **Note**: Most users only use `weight_kg`. The other columns support smart scales that report full body composition. Unused columns are left NULL.

### food_logs

Stores individual meal/food entries with macronutrient breakdown.

```sql
CREATE TABLE food_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,  -- when logged
    food_description TEXT,              -- e.g., "Grilled chicken with rice"
    calories         REAL,              -- total calories (kcal)
    protein_g        REAL,              -- protein in grams
    carbs_g          REAL,              -- carbohydrates in grams
    fat_g            REAL,              -- fat in grams
    image_path       TEXT,              -- optional path to food photo
    notes            TEXT               -- optional notes
);
```

### sleep_logs

Stores daily sleep entries with duration and quality.

```sql
CREATE TABLE sleep_logs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp      DATETIME DEFAULT CURRENT_TIMESTAMP,  -- when logged
    sleep_date     TEXT,              -- date of sleep (YYYY-MM-DD)
    bedtime        TEXT,              -- time went to bed (e.g., "23:30")
    wake_time      TEXT,              -- time woke up (e.g., "07:00")
    duration_hours REAL,              -- total hours slept
    quality        TEXT,              -- "good", "ok", or "bad"
    notes          TEXT               -- optional notes
);
```

### workout_logs

Stores completed workout sessions.

```sql
CREATE TABLE workout_logs (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp        DATETIME DEFAULT CURRENT_TIMESTAMP,  -- when logged
    location         TEXT,              -- e.g., "Home Gym", "Planet Fitness"
    target_muscle    TEXT,              -- primary muscle group (e.g., "Chest")
    duration_minutes INTEGER,           -- session duration in minutes
    exercises_json   TEXT,              -- exercises performed (free text or JSON)
    notes            TEXT               -- optional notes
);
```

### exercise_logs

Stores individual exercise sets for progressive overload tracking.

```sql
CREATE TABLE exercise_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     DATETIME DEFAULT CURRENT_TIMESTAMP,  -- when logged
    exercise_name TEXT NOT NULL,       -- e.g., "Bench Press"
    muscle_group  TEXT,                -- e.g., "Chest"
    weight_lbs    REAL,                -- weight in pounds
    sets          INTEGER,             -- number of sets
    reps          INTEGER,             -- reps per set
    rpe           REAL,                -- Rate of Perceived Exertion (1-10)
    notes         TEXT                 -- optional notes
);
```

### Entity Relationship Diagram

```
+------------------+
| body_metrics     |
|------------------|         +------------------+
| id (PK)          |         | food_logs        |
| timestamp        |         |------------------|
| weight_kg        |         | id (PK)          |
| body_fat         |         | timestamp        |
| bmi              |         | food_description |
| muscle_mass      |         | calories         |
| water_percentage |         | protein_g        |
| bone_mass        |         | carbs_g          |
| basal_metabolism |         | fat_g            |
| visceral_fat     |         | image_path       |
| protein          |         | notes            |
+------------------+         +------------------+

+------------------+         +------------------+
| sleep_logs       |         | workout_logs     |
|------------------|         |------------------|
| id (PK)          |         | id (PK)          |
| timestamp        |         | timestamp        |
| sleep_date       |         | location         |
| bedtime          |         | target_muscle    |
| wake_time        |         | duration_minutes |
| duration_hours   |         | exercises_json   |
| quality          |         | notes            |
| notes            |         +------------------+
+------------------+
                             +------------------+
                             | exercise_logs    |
                             |------------------|
                             | id (PK)          |
                             | timestamp        |
                             | exercise_name    |
                             | muscle_group     |
                             | weight_lbs       |
                             | sets             |
                             | reps             |
                             | rpe              |
                             | notes            |
                             +------------------+
```

> **Note**: The tables are independent (no foreign keys between them). This is by design -- each table stores a different type of health data that can exist independently. The relationships are implicit:
> - `workout_logs.target_muscle` and `exercise_logs.muscle_group` use the same muscle group names (Chest, Back, Legs, etc.)
> - `body_metrics.timestamp` and `food_logs.timestamp` are used to correlate weight changes with nutrition
> - `sleep_logs.sleep_date` is used by `suggest-workout` to adjust intensity

---

## Data Flow (Detailed)

### Food Logging Flow

```
User message: "I ate chicken breast with rice for lunch"
    |
    v
Claude (Kai persona) receives message via WhatsApp plugin
    |
    v
Claude estimates macros from description:
  - Chicken breast (~200g): ~330 kcal, 31g protein, 0g carbs, 3.6g fat
  - Rice (~150g cooked): ~195 kcal, 4g protein, 43g carbs, 0.4g fat
  - Total estimate: ~525 kcal, 35g protein, 43g carbs, 4g fat
    |
    v
Claude runs: kai-cli.py log-food "Chicken breast with rice" 525 35 43 4
    |
    v
kai-cli.py -> db_manager.insert_food_log() -> SQLite INSERT into food_logs
    |
    v
kai-cli.py also calls get_daily_nutrition_summary() for today's totals
    |
    v
Output: "Logged food: Chicken breast with rice (525 kcal)
         Today's totals: 1,040 / 2,200 kcal | 78 / 120g protein"
    |
    v
Claude formats response in friendly Kai tone -> WhatsApp reply
```

### Workout Suggestion Flow

```
User: "What should I train today?"
    |
    v
Claude runs: kai-cli.py suggest-workout --duration 40
    |
    v
kai-cli.py executes the suggestion engine:
    |
    1. Load profile.json
    |   -> equipment categories: ["Barbell", "Dumbbell", "Bodyweight"]
    |   -> rotation: ["Chest", "Back", "Legs", "Shoulders", ...]
    |   -> goals: "Build muscle" -> affects set/rep scheme
    |
    2. Query recent workouts (get_recent_workouts)
    |   -> Last Chest: 2 days ago
    |   -> Last Back: 5 days ago  <-- overdue!
    |   -> Last Legs: 3 days ago
    |
    3. Query missed muscle groups (get_missed_muscle_groups)
    |   -> Back: 5 days (overdue, prioritize)
    |   -> Shoulders: 4 days
    |   -> Core: 6 days (overdue)
    |
    4. Query sleep data (get_average_sleep, last 3 days)
    |   -> Average: 7.2h -> "standard" intensity
    |   -> Prescription: 3-4 sets x 8-12 reps
    |
    5. Parse exercises.md -> filter by user's equipment categories
    |   -> Available Back exercises: Barbell Rows, Deadlift,
    |      Dumbbell Rows, Pull-ups, Chin-ups
    |
    6. Build workout plan:
    |   -> Target: Back + Shoulders (40 min)
    |   -> Warm-up: 5 min
    |   -> Back exercises: 3 exercises x 3-4 sets (20 min)
    |   -> Shoulders exercises: 2 exercises x 3 sets (10 min)
    |   -> Cool-down: 5 min
    |
    v
Output: Structured workout plan with exercise selection, sets, reps
    |
    v
Claude formats into a friendly WhatsApp message
```

### Weight Logging Flow

```
User: "I weigh 71.2 kg today"
    |
    v
Claude runs: kai-cli.py log-weight 71.2
    |
    v
kai-cli.py -> db_manager.insert_body_metrics({"weight_kg": 71.2})
    |         -> SQLite INSERT into body_metrics
    |
    +-> db_manager.get_body_metrics_history(limit=3)
    |   -> Returns last 3 weigh-ins for trend display
    |
    v
Output: "Logged weight: 71.2 kg
         Recent weights:
           2025-01-15: 71.2 kg
           2025-01-14: 71.0 kg
           2025-01-12: 70.8 kg"
```

### Sleep Logging Flow

```
User: "Slept from 11:30 PM to 7 AM last night, felt good"
    |
    v
Claude estimates: date=yesterday, bedtime=23:30, wake=07:00, duration=7.5h, quality=good
    |
    v
Claude runs: kai-cli.py log-sleep 2025-01-15 23:30 07:00 7.5 --quality good
    |
    v
kai-cli.py -> db_manager.insert_sleep_log() -> SQLite INSERT into sleep_logs
    |
    v
Output: "Logged sleep: 2025-01-15 -- 23:30 to 07:00 (7.5h)"
```

### Progressive Overload Logging Flow

```
User: "Just did bench press, 135 lbs, 3 sets of 10, felt like RPE 8"
    |
    v
Claude runs: kai-cli.py log-exercise "Bench Press" "Chest" 135 3 10 --rpe 8
    |
    v
kai-cli.py -> db_manager.insert_exercise_log() -> SQLite INSERT into exercise_logs
    |
    v
Output: "Logged: Bench Press -- 135 lbs x 3 sets x 10 reps, RPE 8"
```

### Reminder Flow (Cron)

```
Cron daemon triggers at 10:00 AM
    |
    v
workout-reminder.sh
    |
    +-> Sources .env (loads KAI_WHATSAPP_CHAT_ID, KAI_TIMEZONE, etc.)
    |
    +-> python3 kai-cli.py quick-status
    |     Output: "Last workout: 2025-01-14 - Chest (40 min)
    |              Last weight: 71.0 kg (2025-01-14)
    |              Today: 0 meals, 0 kcal
    |              Last sleep: 2025-01-14 -- 23:30 to 07:00 (7.5h) (good)"
    |
    +-> python3 kai-cli.py last-workout
    |     Output: "Date: 2025-01-14, Location: Home Gym,
    |              Target: Chest, Duration: 40 min"
    |
    +-> Passes both outputs to Claude Code with a reminder prompt:
    |     "You are Kai, a fitness coach... Here is the user's data...
    |      Send a personalized reminder to the workout group..."
    |
    v
Claude analyzes the data:
  - Last workout was yesterday (Chest) -> not overdue yet
  - 0 meals today -> remind about breakfast/nutrition
  - Sleep was good (7.5h) -> positive reinforcement
    |
    v
Claude generates message via WhatsApp plugin:
  "Good morning! You crushed that chest day yesterday.
   Don't forget to log your breakfast -- fueling up early
   helps with recovery. Maybe Back or Legs today?"
```

---

## Smart Features (Detailed)

### Workout Suggestion Engine

The `suggest-workout` command implements a multi-factor recommendation system:

#### 1. Muscle Rotation

Tracks how many days since each muscle group was last trained:
```
Chest:     2 days ago   (OK)
Back:      5 days ago   (OVERDUE - prioritize)
Legs:      3 days ago   (OK)
Shoulders: 4 days ago   (due soon)
Biceps:    1 day ago    (skip)
Triceps:   1 day ago    (skip)
Core:      6 days ago   (OVERDUE - prioritize)
```

The engine selects 1-2 muscle groups that are most overdue, favoring groups with 5+ days since last training.

#### 2. Overdue Detection

Flags muscle groups not trained in 5+ days as "overdue." These are prioritized in the suggestion regardless of the user's preferred rotation order.

#### 3. Sleep-Based Intensity Adjustment

Queries the last 3 days of sleep data and adjusts workout volume:

| Average Sleep | Intensity Level | Sets x Reps | Notes |
|---|---|---|---|
| < 6 hours | Recovery mode | 2-3 x 8-10 | Reduced volume, focus on form |
| 6-7 hours | Moderate | 3 x 10-12 | Standard moderate session |
| 7-8 hours | Standard | 3-4 x 8-12 | Full normal workout |
| 8+ hours | Push hard | 4 x 8-12 | Higher volume, can push intensity |

#### 4. Equipment Matching

Filters the exercise database (`exercises.md`) to only include exercises the user can perform with their available equipment:

```
User's equipment categories: ["Barbell", "Dumbbell", "Bodyweight"]

Available Chest exercises:
  - Barbell Bench Press        (Barbell)     --> included
  - Incline Barbell Press      (Barbell)     --> included
  - Dumbbell Bench Press       (Dumbbell)    --> included
  - Dumbbell Fly               (Dumbbell)    --> included
  - Cable Crossover            (Cable)       --> excluded (no cable)
  - Chest Press Machine        (Machine)     --> excluded (no machine)
  - Push-ups                   (Bodyweight)  --> included
  - Dips                       (Bodyweight)  --> included
```

#### 5. Duration Scaling

Adjusts the workout structure based on the requested duration:

| Duration | Muscle Groups | Exercises per Group | Structure |
|---|---|---|---|
| 20-25 min | 1 group | 3-4 exercises | Quick focused session |
| 30-40 min | 1-2 groups | 3-4 exercises | Standard session |
| 45-60 min | 2-3 groups | 3-4 exercises | Extended session |

### Weekly Planning

The `weekly-plan` command provides a comprehensive weekly view:

1. **Counts workouts** done this week (Monday through Sunday)
2. **Compares** against the target frequency from `profile.json` (e.g., "3-4" times per week)
3. **Lists muscle groups** trained this week with session count and total minutes
4. **Identifies untrained groups** and how many days since each was last worked
5. **Generates catch-up suggestions** if behind schedule, prioritizing the most overdue groups

### Progressive Overload Tracking

The `strength-trend` command tracks weight progression for each exercise:

- **All exercises summary**: Shows first recorded weight vs. latest weight, with total change
- **Single exercise detail**: Shows the full history of weight/sets/reps over time

This helps users see if they are progressing (increasing weight or reps) or plateauing.
