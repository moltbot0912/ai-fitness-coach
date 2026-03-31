#!/usr/bin/env python3
"""
kai-cli.py -- AI Fitness Coach CLI tool.

Log and query health/fitness data from the command line.
Used by the WhatsApp channel agent (via Claude Code) or directly by the user.

Configuration (in order of precedence):
  1. Command-line flags: --config, --db, --profile, --exercises
  2. Environment variables: KAI_DB_PATH, KAI_PROFILE_PATH, KAI_EXERCISES_PATH, KAI_TIMEZONE
  3. .env file in the project root
  4. Sensible defaults (files in the same directory as this script)
"""

import sys
import os
import json
import re
import argparse
import random
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)  # one level up from src/

# Try to load .env file from project root
_env_file = os.path.join(PROJECT_DIR, ".env")
if os.path.isfile(_env_file):
    with open(_env_file) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _, _val = _line.partition("=")
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in os.environ:
                    os.environ[_key] = _val

# Resolve paths from env or defaults
DB_PATH = os.environ.get("KAI_DB_PATH", os.path.join(PROJECT_DIR, "data", "kai_health.db"))
PROFILE_PATH = os.environ.get("KAI_PROFILE_PATH", os.path.join(PROJECT_DIR, "config", "profile.json"))
EXERCISES_PATH = os.environ.get("KAI_EXERCISES_PATH", os.path.join(BASE_DIR, "exercises.md"))
TIMEZONE = os.environ.get("KAI_TIMEZONE", "")

# Import db_manager from the same directory
sys.path.insert(0, BASE_DIR)
from db_manager import (
    init_health_db,
    init_workout_db,
    insert_body_metrics,
    insert_food_log,
    insert_workout_log,
    insert_sleep_log,
    get_daily_nutrition_summary,
    get_latest_body_metrics,
    get_body_metrics_history,
    get_quick_status,
    get_recent_workouts,
    get_last_workout_info,
    get_sleep_history,
    get_average_sleep,
    get_weekly_workout_count,
    get_weekly_volume_by_muscle,
    get_missed_muscle_groups,
    insert_exercise_log,
    get_exercise_history,
    get_strength_summary,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_db(args):
    """Return the DB path, preferring the CLI flag over the global default."""
    return getattr(args, "db", None) or DB_PATH


def _resolve_profile(args):
    """Return the profile path, preferring the CLI flag over the global default."""
    return getattr(args, "profile", None) or PROFILE_PATH


def _resolve_exercises(args):
    """Return the exercises.md path, preferring the CLI flag over the global default."""
    return getattr(args, "exercises", None) or EXERCISES_PATH


def ensure_db(args):
    """Auto-initialise all DB tables if they don't exist."""
    db = _resolve_db(args)
    os.makedirs(os.path.dirname(db), exist_ok=True)
    init_health_db(db)
    init_workout_db(db)
    return db


def load_profile(args):
    """Load the user profile JSON."""
    path = _resolve_profile(args)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_log_food(args):
    db = ensure_db(args)
    result = insert_food_log(
        db,
        args.description,
        args.calories,
        protein=args.protein_g,
        carbs=args.carbs_g,
        fat=args.fat_g,
        image_path=args.image,
        notes=args.notes,
    )
    print(result)

    summary = get_daily_nutrition_summary(db)
    if summary:
        print(f"\nToday's totals ({summary['date']}):")
        print(f"  Meals logged: {summary['meal_count']}")
        print(f"  Calories:     {summary['calories']} kcal")
        print(f"  Protein:      {summary['protein']} g")
        print(f"  Carbs:        {summary['carbs']} g")
        print(f"  Fat:          {summary['fat']} g")


def cmd_log_weight(args):
    db = ensure_db(args)
    insert_body_metrics(db, {"weight_kg": args.weight_kg})
    print(f"Logged weight: {args.weight_kg} kg")

    history = get_body_metrics_history(db, limit=3)
    if len(history) > 1:
        print("\nRecent weights:")
        for date, weight in history:
            print(f"  {date}: {weight} kg")


def cmd_log_workout(args):
    db = ensure_db(args)
    insert_workout_log(
        db,
        args.location,
        args.target_muscle,
        args.duration_min,
        args.exercises_json,
        notes=args.notes or "",
    )
    print(f"Logged workout: {args.target_muscle} at {args.location}, {args.duration_min} min")
    if args.notes:
        print(f"  Notes: {args.notes}")


def cmd_daily_summary(args):
    db = ensure_db(args)
    profile = load_profile(args)
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")

    summary = get_daily_nutrition_summary(db, date_str)
    if summary:
        print(f"Daily nutrition summary for {summary['date']}:")
        print(f"  Meals logged: {summary['meal_count']}")
        print(f"  Calories:     {summary['calories']} kcal")
        print(f"  Protein:      {summary['protein']} g")
        print(f"  Carbs:        {summary['carbs']} g")
        print(f"  Fat:          {summary['fat']} g")

        # Show targets from profile if available
        goals = profile.get("nutrition_targets", {})
        cal_target = goals.get("calories_per_day", 2200)
        pro_target = goals.get("protein_g_per_day", 120)
        print(f"\n  Daily targets: ~{cal_target} kcal / ~{pro_target}g protein")
        remaining_cal = cal_target - summary['calories']
        remaining_pro = pro_target - summary['protein']
        if remaining_cal > 0:
            print(f"  Remaining:    ~{remaining_cal:.0f} kcal / ~{remaining_pro:.0f}g protein")
        else:
            print(f"  Target reached!")
    else:
        print(f"No food logged for {date_str}.")


def cmd_weekly_summary(args):
    db = ensure_db(args)
    print("Weekly nutrition summary (last 7 days):")
    print("-" * 50)

    today = datetime.now()
    total_cal = 0
    total_pro = 0
    days_with_data = 0

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        label = day.strftime("%a %m/%d")
        summary = get_daily_nutrition_summary(db, day_str)
        if summary and summary['meal_count'] > 0:
            days_with_data += 1
            total_cal += summary['calories']
            total_pro += summary['protein']
            print(
                f"  {label}: {summary['calories']:>7.0f} kcal | "
                f"P: {summary['protein']:>5.0f}g | "
                f"C: {summary['carbs']:>5.0f}g | "
                f"F: {summary['fat']:>5.0f}g  "
                f"({summary['meal_count']} meals)"
            )
        else:
            print(f"  {label}:       -- no data --")

    if days_with_data > 0:
        print("-" * 50)
        print(
            f"  Average:  {total_cal / days_with_data:>7.0f} kcal/day | "
            f"Protein: {total_pro / days_with_data:>5.0f}g/day"
        )
        print(f"  Days tracked: {days_with_data}/7")

    workouts = get_recent_workouts(db, limit=7)
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    week_workouts = [w for w in workouts if w['date'] and w['date'] >= week_ago]
    if week_workouts:
        print(f"\n  Workouts this week: {len(week_workouts)}")
        for w in week_workouts:
            print(f"    {w['date']}: {w['target_muscle']} at {w['location']} ({w['duration_minutes']} min)")
    else:
        print(f"\n  Workouts this week: 0")


def cmd_weight_trend(args):
    db = ensure_db(args)
    history = get_body_metrics_history(db, limit=args.days)

    if not history:
        print("No weight data recorded yet.")
        return

    print(f"Weight trend (last {len(history)} entries):")
    print("-" * 30)
    for date, weight in reversed(history):
        print(f"  {date}: {weight} kg")

    if len(history) >= 2:
        newest = history[0][1]
        oldest = history[-1][1]
        diff = newest - oldest
        direction = "+" if diff >= 0 else ""
        print("-" * 30)
        print(f"  Change: {direction}{diff:.1f} kg")
        print(f"  Latest: {newest} kg")


def cmd_log_sleep(args):
    db = ensure_db(args)
    result = insert_sleep_log(
        db,
        args.sleep_date,
        args.bedtime,
        args.wake_time,
        args.duration_hours,
        quality=args.quality,
        notes=args.notes,
    )
    print(result)

    avg = get_average_sleep(db, days=7)
    if avg:
        print(f"\n  7-day average: {avg['average_hours']}h ({avg['entries']} entries)")


def cmd_sleep_trend(args):
    db = ensure_db(args)
    history = get_sleep_history(db, days=args.days)

    if not history:
        print("No sleep data recorded yet.")
        return

    print(f"Sleep history (last {args.days} days):")
    print("-" * 55)
    for entry in reversed(history):
        quality_str = f"  [{entry['quality']}]" if entry.get('quality') else ""
        print(
            f"  {entry['sleep_date']}: {entry['bedtime']} -> {entry['wake_time']}  "
            f"({entry['duration_hours']}h){quality_str}"
        )

    print("-" * 55)
    avg = get_average_sleep(db, days=args.days)
    if avg:
        print(f"  Average: {avg['average_hours']}h/night ({avg['entries']} entries)")


def cmd_quick_status(args):
    db = ensure_db(args)
    status = get_quick_status(db)

    print("Quick status:")
    print(f"  Last workout:    {status['last_workout'] or 'No workouts recorded'}")
    print(f"  Latest weight:   {status['last_weight'] or 'No weight recorded'}")
    print(f"  Last sleep:      {status['last_sleep'] or 'No sleep recorded'}")
    print(f"  Today's meals:   {status['today_meals']}")
    print(f"  Today's calories: {status['today_calories']} kcal")


def cmd_last_workout(args):
    db = ensure_db(args)
    info = get_last_workout_info(db)

    if info:
        print(f"Last workout:")
        print(f"  Date:     {info['date']}")
        print(f"  Location: {info['location']}")
        print(f"  Target:   {info['target_muscle']}")
        print(f"  Duration: {info['duration']} min")

        try:
            last_date = datetime.strptime(info['date'], "%Y-%m-%d")
            days_ago = (datetime.now() - last_date).days
            if days_ago == 0:
                print(f"  (Today!)")
            elif days_ago == 1:
                print(f"  (Yesterday)")
            else:
                print(f"  ({days_ago} days ago)")
        except (ValueError, TypeError):
            pass
    else:
        print("No workouts recorded yet.")


# ---------------------------------------------------------------------------
# weekly-plan: smart rescheduling
# ---------------------------------------------------------------------------

def cmd_weekly_plan(args):
    db = ensure_db(args)
    profile = load_profile(args)

    today = datetime.now().date()
    day_of_week = today.weekday()
    days_left = 6 - day_of_week
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    today_name = day_names[day_of_week]

    prefs = profile.get("workout_preferences", {})
    freq_str = prefs.get("frequency_per_week", "3-4")
    freq_nums = re.findall(r'\d+', freq_str)
    target_low = int(freq_nums[0]) if freq_nums else 3
    target_high = int(freq_nums[1]) if len(freq_nums) > 1 else target_low

    wk = get_weekly_workout_count(db, weeks=1)
    volume = get_weekly_volume_by_muscle(db, weeks=1)
    missed = get_missed_muscle_groups(db, days=7)

    workouts_done = wk["count"]
    workouts_remaining = max(0, target_low - workouts_done)

    rotation = prefs.get(
        "preferred_muscle_group_rotation",
        ["Chest", "Back", "Legs", "Shoulders", "Biceps", "Triceps", "Core"],
    )

    trained_muscles = {v["target_muscle"] for v in volume}
    untrained_muscles = [mg for mg in rotation if mg not in trained_muscles]

    output = []
    output.append(f"Weekly Plan  --  {today.strftime('%Y-%m-%d')} ({today_name})")
    output.append("=" * 55)
    output.append(f"Workouts done this week:  {workouts_done}")
    output.append(f"Target frequency:         {target_low}-{target_high}x / week")
    output.append(f"Days remaining (incl today): {days_left + 1}")
    output.append("")

    if volume:
        output.append("Muscle groups trained this week:")
        for v in volume:
            output.append(f"  {v['target_muscle']:12s}  {v['sessions']} session(s), {v['total_minutes']} min total")
    else:
        output.append("Muscle groups trained this week: (none)")
    output.append("")

    if untrained_muscles:
        output.append("Not yet trained this week:")
        for mg in untrained_muscles:
            days_info = next((m for m in missed if m["muscle_group"] == mg), None)
            if days_info and days_info["days_since"] < 999:
                output.append(f"  {mg:12s}  (last trained {days_info['days_since']} days ago)")
            else:
                output.append(f"  {mg:12s}  (no recent record)")
    else:
        output.append("All muscle groups hit this week!")
    output.append("")

    output.append("Suggestions:")
    if workouts_done >= target_high:
        output.append(f"  You've already hit your target of {target_high}x this week. Nice work!")
        if untrained_muscles:
            output.append(f"  Optional: add a session for {', '.join(untrained_muscles[:2])} to stay balanced.")
    elif workouts_remaining <= days_left + 1:
        output.append(f"  {workouts_remaining} more workout(s) needed to hit your minimum of {target_low}x.")
        if untrained_muscles:
            overdue = [mg for mg in untrained_muscles if any(
                m["muscle_group"] == mg and m["days_since"] >= 5 for m in missed
            )]
            if overdue:
                output.append(f"  Priority (5+ days overdue): {', '.join(overdue)}")
            else:
                output.append(f"  Suggested focus: {', '.join(untrained_muscles[:workouts_remaining * 2])}")
    else:
        output.append(f"  Behind schedule: {workouts_remaining} workout(s) needed but only {days_left + 1} day(s) left.")
        if days_left >= 1 and workouts_remaining >= 2:
            output.append(f"  Consider doubling up: train today AND tomorrow to catch up.")
        overdue = [m for m in missed if m["days_since"] >= 5]
        if overdue:
            overdue_names = [m["muscle_group"] for m in overdue[:3]]
            output.append(f"  Most overdue: {', '.join(overdue_names)}")
        if untrained_muscles:
            output.append(f"  Combine groups to cover more ground: e.g. {' + '.join(untrained_muscles[:2])}")

    print("\n".join(output))


# ---------------------------------------------------------------------------
# suggest-workout: intelligent workout suggestion
# ---------------------------------------------------------------------------

ALL_MUSCLE_GROUPS = ["Chest", "Back", "Legs", "Shoulders", "Biceps", "Triceps", "Core"]

FOCUS_ALIAS = {
    "chest": "Chest",
    "back": "Back",
    "legs": "Legs",
    "shoulders": "Shoulders",
    "biceps": "Biceps",
    "triceps": "Triceps",
    "arms": "Biceps+Triceps",
    "core": "Core",
    "abs": "Core",
    "upper": "Chest+Back+Shoulders",
    "lower": "Legs+Core",
    "push": "Chest+Shoulders+Triceps",
    "pull": "Back+Biceps",
}


def _parse_exercises_md(filepath):
    """Parse exercises.md into {muscle_group: {equipment_type: [exercise_names]}}."""
    exercises = {}
    current_muscle = None
    current_equip = None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("## "):
                    current_muscle = line[3:].strip()
                    exercises[current_muscle] = {}
                elif line.startswith("### Equipment: "):
                    current_equip = line[len("### Equipment: "):].strip()
                    if current_muscle:
                        exercises[current_muscle][current_equip] = []
                elif line.startswith("- ") and current_muscle and current_equip:
                    exercises[current_muscle][current_equip].append(line[2:].strip())
    except Exception:
        return {}
    return exercises


def _pick_exercises(muscle_group, equipment_categories, exercises_db, count=3):
    """Pick up to *count* random exercises for a muscle group from available equipment."""
    available = []
    if muscle_group not in exercises_db:
        return available
    for cat in equipment_categories:
        for ex in exercises_db[muscle_group].get(cat, []):
            available.append((ex, cat))
    random.shuffle(available)
    return available[:count]


def cmd_suggest_workout(args):
    db = ensure_db(args)
    profile = load_profile(args)
    exercises_path = _resolve_exercises(args)

    prefs = profile.get("workout_preferences", {})
    gym_locations = prefs.get("gym_locations", {})
    rotation = prefs.get("preferred_muscle_group_rotation", ALL_MUSCLE_GROUPS)
    primary_goal = profile.get("fitness_goals", {}).get("primary_goal", "")

    # Determine equipment from first gym location
    location_name = None
    equipment_list = []
    equipment_categories = []
    for loc_name, loc_data in gym_locations.items():
        location_name = loc_name
        if isinstance(loc_data, dict):
            equipment_list = loc_data.get("equipment", [])
            equipment_categories = loc_data.get("categories", ["Bodyweight"])
        elif isinstance(loc_data, list):
            equipment_categories = loc_data
        break
    if not equipment_categories:
        equipment_categories = ["Bodyweight"]
    if not location_name:
        location_name = "Home"

    # Query recent workouts
    recent = get_recent_workouts(db, limit=14)
    today = datetime.now().date()
    muscle_last_trained = {}
    for w in recent:
        muscle = w.get("target_muscle", "")
        wdate_str = w.get("date")
        if not wdate_str or not muscle:
            continue
        try:
            wdate = datetime.strptime(wdate_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
        days_ago = (today - wdate).days
        if muscle not in muscle_last_trained or days_ago < muscle_last_trained[muscle]:
            muscle_last_trained[muscle] = days_ago

    # Check overdue muscle groups
    overdue_groups = get_missed_muscle_groups(db, days=7)
    overdue_warnings = [og for og in overdue_groups if 5 <= og["days_since"] < 999]

    # Decide target muscles
    duration = args.duration or 40

    if args.focus:
        focus_key = args.focus.lower()
        mapped = FOCUS_ALIAS.get(focus_key, args.focus)
        target_muscles = [m.strip() for m in mapped.split("+")]
    else:
        scored = []
        overdue_names = {og["muscle_group"] for og in overdue_warnings}
        for mg in rotation:
            days = muscle_last_trained.get(mg, 999)
            boost = 100 if mg in overdue_names else 0
            scored.append((days + boost, mg))
        scored.sort(key=lambda x: -x[0])
        if duration <= 25:
            n_groups = 1
        elif duration <= 45:
            n_groups = 2
        else:
            n_groups = 3
        target_muscles = [mg for _, mg in scored[:n_groups]]

    # Load exercise database
    exercises_db = _parse_exercises_md(exercises_path)
    if not exercises_db:
        print("Error: could not parse exercises.md")
        return

    # Check sleep data for intensity adjustment
    sleep_avg = get_average_sleep(db, days=3)
    sleep_note = None
    sets_reps_override = None
    if sleep_avg:
        avg_hrs = sleep_avg["average_hours"]
        if avg_hrs < 6:
            sets_reps_override = "2-3 sets x 8-10 reps"
            sleep_note = "Low sleep -- lighter recovery session today"
        elif avg_hrs < 7:
            sets_reps_override = "3 sets x 10-12 reps"
        elif avg_hrs <= 8:
            sets_reps_override = "3-4 sets x 8-12 reps"
        else:
            sets_reps_override = "4 sets x 8-12 reps"
            sleep_note = "Great sleep -- push yourself today"

    # Build the workout plan
    exercises_per_group = max(2, min(4, (duration - 8) // (len(target_muscles) * 5)))

    output = []
    output.append(f"Workout suggestion  --  {duration} min @ {location_name}")
    output.append("=" * 55)

    if recent:
        last = recent[0]
        last_muscle = last.get("target_muscle", "?")
        last_days = muscle_last_trained.get(last_muscle, "?")
        output.append(f"Last workout: {last_muscle} ({last_days} day(s) ago)")
    else:
        output.append("No recent workouts found -- fresh start!")

    if sleep_avg:
        output.append(f"Sleep (3-day avg): {sleep_avg['average_hours']}h ({sleep_avg['entries']} entries)")
    if sleep_note:
        output.append(f"Note: {sleep_note}")

    output.append(f"Focus: {', '.join(target_muscles)}")
    output.append("")
    output.append("WARM-UP (5 min)")
    output.append("  - Light cardio or dynamic stretching")
    output.append("")
    output.append("MAIN WORKOUT")

    exercise_num = 0
    for mg in target_muscles:
        output.append(f"  [{mg}]")
        picked = _pick_exercises(mg, equipment_categories, exercises_db, count=exercises_per_group)
        if not picked:
            picked = _pick_exercises(mg, ["Bodyweight"], exercises_db, count=exercises_per_group)
        if not picked:
            output.append("    (no matching exercises found)")
            continue
        for ex_name, eq_type in picked:
            exercise_num += 1
            if sets_reps_override:
                sets_reps = sets_reps_override
            elif "muscle" in primary_goal.lower() or "strength" in primary_goal.lower():
                sets_reps = "3-4 sets x 8-12 reps"
            else:
                sets_reps = "3 sets x 10-15 reps"
            output.append(f"    {exercise_num}. {ex_name}  [{eq_type}]")
            output.append(f"       {sets_reps}")
        output.append("")

    output.append("COOL-DOWN (3 min)")
    output.append("  - Static stretching for worked muscle groups")
    output.append("")

    if equipment_list:
        output.append("Available equipment at " + location_name + ":")
        for eq in equipment_list:
            output.append(f"  - {eq}")
        output.append("")

    never_trained = [mg for mg in rotation if mg not in muscle_last_trained]
    stale = [mg for mg in rotation if muscle_last_trained.get(mg, 0) >= 5 and mg not in target_muscles]
    if never_trained:
        output.append(f"Never trained recently: {', '.join(never_trained)}")
    if stale:
        output.append(f"5+ days since last session: {', '.join(stale)}")

    not_in_plan = [og for og in overdue_warnings if og["muscle_group"] not in target_muscles]
    if not_in_plan:
        output.append("")
        output.append("RESCHEDULING ALERTS:")
        for og in not_in_plan:
            output.append(
                f"  ! {og['muscle_group']} hasn't been trained in "
                f"{og['days_since']} days -- consider including it soon"
            )

    print("\n".join(output))


# ---------------------------------------------------------------------------
# log-exercise / strength-trend
# ---------------------------------------------------------------------------

def cmd_log_exercise(args):
    db = ensure_db(args)
    result = insert_exercise_log(
        db,
        args.exercise_name,
        args.muscle_group,
        args.weight_lbs,
        args.sets,
        args.reps,
        rpe=args.rpe,
        notes=args.notes,
    )
    print(result)

    history = get_exercise_history(db, args.exercise_name, limit=3)
    if len(history) > 1:
        print(f"\nRecent history for {args.exercise_name}:")
        for entry in history:
            rpe_str = f"  RPE {entry['rpe']}" if entry.get('rpe') else ""
            print(f"  {entry['date']}: {entry['weight_lbs']} lbs x {entry['sets']}x{entry['reps']}{rpe_str}")


def cmd_strength_trend(args):
    db = ensure_db(args)
    exercise_name = args.exercise_name

    if exercise_name:
        history = get_exercise_history(db, exercise_name, limit=args.limit)
        if not history:
            print(f"No records found for '{exercise_name}'.")
            return

        print(f"Strength trend: {exercise_name}")
        print(f"  Muscle group: {history[0].get('muscle_group', '?')}")
        print("-" * 55)
        for entry in reversed(history):
            rpe_str = f"  RPE {entry['rpe']}" if entry.get('rpe') else ""
            notes_str = f"  ({entry['notes']})" if entry.get('notes') else ""
            print(
                f"  {entry['date']}: {entry['weight_lbs']:>6.1f} lbs x "
                f"{entry['sets']}x{entry['reps']}{rpe_str}{notes_str}"
            )
        print("-" * 55)
        if len(history) >= 2:
            first_weight = history[-1]['weight_lbs']
            latest_weight = history[0]['weight_lbs']
            diff = latest_weight - first_weight
            direction = "+" if diff >= 0 else ""
            print(f"  First recorded: {first_weight} lbs ({history[-1]['date']})")
            print(f"  Latest:         {latest_weight} lbs ({history[0]['date']})")
            print(f"  Change:         {direction}{diff:.1f} lbs")
        print(f"  Total entries:  {len(history)}")
    else:
        summary = get_strength_summary(db)
        if not summary:
            print("No exercise data recorded yet.")
            return

        print("Strength Summary -- All Exercises")
        print("=" * 65)

        current_group = None
        for s in summary:
            if s['muscle_group'] != current_group:
                current_group = s['muscle_group']
                print(f"\n  [{current_group or 'Other'}]")

            diff = s['weight_change']
            direction = "+" if diff >= 0 else ""
            entries_str = f"({s['total_entries']} entries)"

            if s['total_entries'] > 1:
                print(
                    f"    {s['exercise_name']:30s}  "
                    f"{s['first_weight']:>6.1f} -> {s['latest_weight']:>6.1f} lbs  "
                    f"({direction}{diff:.1f})  {entries_str}"
                )
            else:
                print(f"    {s['exercise_name']:30s}  {s['latest_weight']:>6.1f} lbs  {entries_str}")
        print("")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="AI Fitness Coach CLI -- log and query workout/nutrition data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Global options
    parser.add_argument("--db", default=None, help="Path to SQLite database (overrides KAI_DB_PATH)")
    parser.add_argument("--profile", default=None, help="Path to profile.json (overrides KAI_PROFILE_PATH)")
    parser.add_argument("--exercises", default=None, help="Path to exercises.md (overrides KAI_EXERCISES_PATH)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # log-food
    p_food = subparsers.add_parser("log-food", help="Log a food/meal entry")
    p_food.add_argument("description", help="Food description")
    p_food.add_argument("calories", type=float, help="Calories (kcal)")
    p_food.add_argument("protein_g", type=float, help="Protein in grams")
    p_food.add_argument("carbs_g", type=float, help="Carbs in grams")
    p_food.add_argument("fat_g", type=float, help="Fat in grams")
    p_food.add_argument("--image", default=None, help="Path to food image")
    p_food.add_argument("--notes", default=None, help="Additional notes")
    p_food.set_defaults(func=cmd_log_food)

    # log-weight
    p_weight = subparsers.add_parser("log-weight", help="Log a weight measurement")
    p_weight.add_argument("weight_kg", type=float, help="Weight in kg")
    p_weight.set_defaults(func=cmd_log_weight)

    # log-workout
    p_workout = subparsers.add_parser("log-workout", help="Log a completed workout")
    p_workout.add_argument("location", help="Workout location (e.g. gym, home)")
    p_workout.add_argument("target_muscle", help="Target muscle group")
    p_workout.add_argument("duration_min", type=int, help="Duration in minutes")
    p_workout.add_argument("exercises_json", help="Exercises performed (JSON string or text)")
    p_workout.add_argument("--notes", default=None, help="Additional notes")
    p_workout.set_defaults(func=cmd_log_workout)

    # log-sleep
    p_sleep = subparsers.add_parser("log-sleep", help="Log a sleep entry")
    p_sleep.add_argument("sleep_date", help="Date of sleep (YYYY-MM-DD)")
    p_sleep.add_argument("bedtime", help="Bedtime (e.g. 23:30)")
    p_sleep.add_argument("wake_time", help="Wake time (e.g. 07:00)")
    p_sleep.add_argument("duration_hours", type=float, help="Sleep duration in hours")
    p_sleep.add_argument("--quality", default=None, choices=["good", "ok", "bad"], help="Sleep quality")
    p_sleep.add_argument("--notes", default=None, help="Additional notes")
    p_sleep.set_defaults(func=cmd_log_sleep)

    # log-exercise
    p_exercise = subparsers.add_parser("log-exercise", help="Log an exercise with weight for progressive overload")
    p_exercise.add_argument("exercise_name", help="Exercise name (e.g. 'Bench Press')")
    p_exercise.add_argument("muscle_group", help="Muscle group (e.g. Chest, Back, Legs)")
    p_exercise.add_argument("weight_lbs", type=float, help="Weight used in lbs")
    p_exercise.add_argument("sets", type=int, help="Number of sets")
    p_exercise.add_argument("reps", type=int, help="Number of reps per set")
    p_exercise.add_argument("--rpe", type=float, default=None, help="Rate of Perceived Exertion (1-10)")
    p_exercise.add_argument("--notes", default=None, help="Additional notes")
    p_exercise.set_defaults(func=cmd_log_exercise)

    # daily-summary
    p_daily = subparsers.add_parser("daily-summary", help="Show daily nutrition summary")
    p_daily.add_argument("date", nargs="?", default=None, help="Date (YYYY-MM-DD), defaults to today")
    p_daily.set_defaults(func=cmd_daily_summary)

    # weekly-summary
    p_weekly = subparsers.add_parser("weekly-summary", help="Show last 7 days overview")
    p_weekly.set_defaults(func=cmd_weekly_summary)

    # weight-trend
    p_trend = subparsers.add_parser("weight-trend", help="Show weight history")
    p_trend.add_argument("days", nargs="?", type=int, default=14, help="Number of entries (default: 14)")
    p_trend.set_defaults(func=cmd_weight_trend)

    # sleep-trend
    p_sleeptrend = subparsers.add_parser("sleep-trend", help="Show sleep history and average")
    p_sleeptrend.add_argument("days", nargs="?", type=int, default=7, help="Number of days (default: 7)")
    p_sleeptrend.set_defaults(func=cmd_sleep_trend)

    # quick-status
    p_status = subparsers.add_parser("quick-status", help="Quick overview of current state")
    p_status.set_defaults(func=cmd_quick_status)

    # last-workout
    p_last = subparsers.add_parser("last-workout", help="Details of the most recent workout")
    p_last.set_defaults(func=cmd_last_workout)

    # suggest-workout
    p_suggest = subparsers.add_parser("suggest-workout", help="Generate a smart workout suggestion")
    p_suggest.add_argument("--duration", type=int, default=None, help="Duration in minutes (default: 40)")
    p_suggest.add_argument("--focus", default=None, help="Muscle focus (chest, back, legs, push, pull, upper, lower, arms)")
    p_suggest.set_defaults(func=cmd_suggest_workout)

    # strength-trend
    p_strength = subparsers.add_parser("strength-trend", help="Show progressive overload / strength trends")
    p_strength.add_argument("exercise_name", nargs="?", default=None, help="Exercise name (omit for all)")
    p_strength.add_argument("--limit", type=int, default=10, help="Number of entries (default: 10)")
    p_strength.set_defaults(func=cmd_strength_trend)

    # weekly-plan
    p_wplan = subparsers.add_parser("weekly-plan", help="Smart weekly plan with catch-up suggestions")
    p_wplan.set_defaults(func=cmd_weekly_plan)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
