"""
db_manager.py - AI Fitness Coach SQLite database manager.

Standalone module for all health/fitness data operations:
  - Body metrics (weight, body fat, etc.)
  - Food/nutrition logs
  - Workout session logs
  - Sleep tracking
  - Individual exercise logs (progressive overload)

All functions accept a `db_path` argument pointing to the SQLite database file.
"""

import sqlite3
import os
from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Database initialization
# ---------------------------------------------------------------------------

def init_health_db(db_path):
    """Create core health tables: body_metrics, food_logs, sleep_logs."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS body_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                fetch_timestamp DATETIME,
                weight_kg REAL,
                body_fat REAL,
                bmi REAL,
                muscle_mass REAL,
                water_percentage REAL,
                bone_mass REAL,
                basal_metabolism REAL,
                visceral_fat REAL,
                protein REAL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS food_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                food_description TEXT,
                calories REAL,
                protein_g REAL,
                carbs_g REAL,
                fat_g REAL,
                image_path TEXT,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sleep_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sleep_date TEXT,
                bedtime TEXT,
                wake_time TEXT,
                duration_hours REAL,
                quality TEXT,
                notes TEXT
            )
        ''')

        conn.commit()
        return "Database initialized successfully."
    except sqlite3.Error as e:
        return f"Error: database initialization failed - {e}"
    finally:
        if conn:
            conn.close()


def init_workout_db(db_path):
    """Create workout tables: workout_logs, exercise_logs."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS workout_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                location TEXT,
                target_muscle TEXT,
                duration_minutes INTEGER,
                exercises_json TEXT,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercise_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                exercise_name TEXT NOT NULL,
                muscle_group TEXT,
                weight_lbs REAL,
                sets INTEGER,
                reps INTEGER,
                rpe REAL,
                notes TEXT
            )
        ''')

        conn.commit()
        return "Workout tables initialized successfully."
    except sqlite3.Error as e:
        return f"Error: workout table initialization failed - {e}"
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Body metrics
# ---------------------------------------------------------------------------

def insert_body_metrics(db_path, metrics):
    """Insert a body metrics entry (weight, body fat, etc.)."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO body_metrics (
                fetch_timestamp, weight_kg, body_fat, bmi,
                muscle_mass, water_percentage, bone_mass,
                basal_metabolism, visceral_fat, protein
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.get("fetch_timestamp", datetime.now().isoformat()),
            metrics.get("weight_kg"),
            metrics.get("body_fat"),
            metrics.get("bmi"),
            metrics.get("muscle_mass"),
            metrics.get("water_percentage"),
            metrics.get("bone_mass"),
            metrics.get("basal_metabolism"),
            metrics.get("visceral_fat"),
            metrics.get("protein"),
        ))

        conn.commit()
        return "Body metrics saved successfully."
    except sqlite3.Error as e:
        return f"Error: failed to save body metrics - {e}"
    finally:
        if conn:
            conn.close()


def get_latest_body_metrics(db_path):
    """Retrieve the most recent body metrics entry."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM body_metrics ORDER BY timestamp DESC LIMIT 1')
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        return None
    finally:
        if conn:
            conn.close()


def get_body_metrics_history(db_path, limit=7):
    """Retrieve weight history as a list of (date, weight_kg) tuples."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT date(timestamp, 'localtime'), weight_kg "
            "FROM body_metrics WHERE weight_kg IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return cursor.fetchall()
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Food logs
# ---------------------------------------------------------------------------

def insert_food_log(db_path, food_desc, calories, protein=0, carbs=0, fat=0, image_path=None, notes=None):
    """Insert a food/meal log entry."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO food_logs (
                food_description, calories, protein_g, carbs_g, fat_g, image_path, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (food_desc, calories, protein, carbs, fat, image_path, notes))

        conn.commit()
        return f"Logged food: {food_desc} ({calories} kcal)"
    except sqlite3.Error as e:
        return f"Error: failed to save food log - {e}"
    finally:
        if conn:
            conn.close()


def get_daily_nutrition_summary(db_path, target_date_str=None):
    """Get total calories and macros for a specific day (default: today)."""
    if target_date_str is None:
        target_date_str = datetime.now().strftime('%Y-%m-%d')

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT
                SUM(calories) as total_cal,
                SUM(protein_g) as total_pro,
                SUM(carbs_g) as total_carb,
                SUM(fat_g) as total_fat,
                COUNT(id) as meal_count
            FROM food_logs
            WHERE date(timestamp, 'localtime') = ?
        ''', (target_date_str,))

        row = cursor.fetchone()
        if row and row['meal_count'] > 0:
            return {
                "date": target_date_str,
                "meal_count": row['meal_count'],
                "calories": round(row['total_cal'] or 0, 1),
                "protein": round(row['total_pro'] or 0, 1),
                "carbs": round(row['total_carb'] or 0, 1),
                "fat": round(row['total_fat'] or 0, 1),
            }
        return None
    except sqlite3.Error as e:
        return None
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Sleep logs
# ---------------------------------------------------------------------------

def insert_sleep_log(db_path, sleep_date, bedtime, wake_time, duration_hours, quality=None, notes=None):
    """Insert a sleep log entry."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO sleep_logs (
                sleep_date, bedtime, wake_time, duration_hours, quality, notes
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (sleep_date, bedtime, wake_time, duration_hours, quality, notes))

        conn.commit()
        return f"Logged sleep: {sleep_date} -- {bedtime} to {wake_time} ({duration_hours}h)"
    except sqlite3.Error as e:
        return f"Error: failed to save sleep log - {e}"
    finally:
        if conn:
            conn.close()


def get_sleep_history(db_path, days=7):
    """Return recent sleep entries within the given number of days."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT sleep_date, bedtime, wake_time, duration_hours, quality, notes
            FROM sleep_logs
            WHERE sleep_date >= ?
            ORDER BY sleep_date DESC
        ''', (cutoff,))
        return [dict(r) for r in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_average_sleep(db_path, days=7):
    """Return average sleep duration over the given number of days."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT AVG(duration_hours), COUNT(*)
            FROM sleep_logs
            WHERE sleep_date >= ?
        ''', (cutoff,))
        row = cursor.fetchone()
        if row and row[1] > 0:
            return {"average_hours": round(row[0], 1), "entries": row[1]}
        return None
    except sqlite3.Error:
        return None
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Workout logs
# ---------------------------------------------------------------------------

def insert_workout_log(db_path, location, target_muscle, duration, exercises_text, notes=""):
    """Insert a workout session log."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO workout_logs (location, target_muscle, duration_minutes, exercises_json, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (location, target_muscle, duration, exercises_text, notes))

        conn.commit()
        return "Workout log saved successfully."
    except sqlite3.Error as e:
        return f"Error: failed to save workout log - {e}"
    finally:
        if conn:
            conn.close()


def get_recent_workouts(db_path, limit=5):
    """Return the most recent workout sessions."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT date(timestamp, 'localtime') as date, location, target_muscle, duration_minutes "
            "FROM workout_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_last_workout_info(db_path):
    """Return info about the most recent workout."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT date(timestamp, 'localtime') as date, location, target_muscle, duration_minutes
            FROM workout_logs
            ORDER BY timestamp DESC LIMIT 1
        """)
        row = cursor.fetchone()
        if row:
            return {
                "date": row['date'],
                "location": row['location'],
                "target_muscle": row['target_muscle'],
                "duration": row['duration_minutes'],
            }
        return None
    except Exception:
        return None
    finally:
        if conn:
            conn.close()


def get_weekly_workout_count(db_path, weeks=1):
    """Count workouts from the start of the current week (Monday)."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        if weeks > 1:
            week_start = week_start - timedelta(weeks=weeks - 1)
        week_start_str = week_start.strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT COUNT(*) FROM workout_logs
            WHERE date(timestamp, 'localtime') >= ?
        ''', (week_start_str,))
        count = cursor.fetchone()[0]
        return {
            "count": count,
            "week_start": week_start_str,
            "week_end": (week_start + timedelta(days=6 * weeks)).strftime('%Y-%m-%d'),
        }
    except sqlite3.Error:
        return {"count": 0, "week_start": "", "week_end": ""}
    finally:
        if conn:
            conn.close()


def get_weekly_volume_by_muscle(db_path, weeks=1):
    """Total workout sessions per muscle group this week."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())
        if weeks > 1:
            week_start = week_start - timedelta(weeks=weeks - 1)
        week_start_str = week_start.strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT target_muscle, COUNT(*) as sessions,
                   SUM(duration_minutes) as total_minutes
            FROM workout_logs
            WHERE date(timestamp, 'localtime') >= ?
            GROUP BY target_muscle
            ORDER BY sessions DESC
        ''', (week_start_str,))
        return [dict(r) for r in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_missed_muscle_groups(db_path, days=7):
    """Return muscle groups not trained in the last N days, with days since last session."""
    all_groups = ["Chest", "Back", "Legs", "Shoulders", "Biceps", "Triceps", "Core"]
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        cursor.execute('''
            SELECT DISTINCT target_muscle FROM workout_logs
            WHERE date(timestamp, 'localtime') >= ?
        ''', (cutoff,))
        trained = {row['target_muscle'] for row in cursor.fetchall()}

        missed = []
        for mg in all_groups:
            if mg not in trained:
                cursor.execute('''
                    SELECT date(timestamp, 'localtime') as last_date
                    FROM workout_logs
                    WHERE target_muscle = ?
                    ORDER BY timestamp DESC LIMIT 1
                ''', (mg,))
                row = cursor.fetchone()
                if row and row['last_date']:
                    last_date = datetime.strptime(row['last_date'], '%Y-%m-%d').date()
                    days_since = (datetime.now().date() - last_date).days
                else:
                    days_since = 999  # Never trained
                missed.append({"muscle_group": mg, "days_since": days_since})

        missed.sort(key=lambda x: -x['days_since'])
        return missed
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


# ---------------------------------------------------------------------------
# Exercise logs (progressive overload tracking)
# ---------------------------------------------------------------------------

def insert_exercise_log(db_path, exercise_name, muscle_group, weight_lbs, sets, reps, rpe=None, notes=None):
    """Insert an exercise log entry for progressive overload tracking."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO exercise_logs (
                exercise_name, muscle_group, weight_lbs, sets, reps, rpe, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (exercise_name, muscle_group, weight_lbs, sets, reps, rpe, notes))

        conn.commit()
        rpe_str = f", RPE {rpe}" if rpe else ""
        return f"Logged: {exercise_name} -- {weight_lbs} lbs x {sets} sets x {reps} reps{rpe_str}"
    except sqlite3.Error as e:
        return f"Error: failed to save exercise log - {e}"
    finally:
        if conn:
            conn.close()


def get_exercise_history(db_path, exercise_name, limit=10):
    """Return weight progression history for a specific exercise."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT date(timestamp, 'localtime') as date, exercise_name, muscle_group,
                   weight_lbs, sets, reps, rpe, notes
            FROM exercise_logs
            WHERE exercise_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (exercise_name, limit))
        return [dict(r) for r in cursor.fetchall()]
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_strength_summary(db_path):
    """Show latest weight vs first recorded weight for each exercise."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT DISTINCT exercise_name, muscle_group FROM exercise_logs
            ORDER BY muscle_group, exercise_name
        ''')
        exercises = cursor.fetchall()

        results = []
        for ex in exercises:
            name = ex['exercise_name']

            cursor.execute('''
                SELECT weight_lbs, sets, reps, date(timestamp, 'localtime') as date
                FROM exercise_logs
                WHERE exercise_name = ?
                ORDER BY timestamp ASC LIMIT 1
            ''', (name,))
            first = cursor.fetchone()

            cursor.execute('''
                SELECT weight_lbs, sets, reps, date(timestamp, 'localtime') as date
                FROM exercise_logs
                WHERE exercise_name = ?
                ORDER BY timestamp DESC LIMIT 1
            ''', (name,))
            latest = cursor.fetchone()

            cursor.execute('SELECT COUNT(*) FROM exercise_logs WHERE exercise_name = ?', (name,))
            count = cursor.fetchone()[0]

            if first and latest:
                results.append({
                    "exercise_name": name,
                    "muscle_group": ex['muscle_group'],
                    "first_weight": first['weight_lbs'],
                    "first_date": first['date'],
                    "latest_weight": latest['weight_lbs'],
                    "latest_date": latest['date'],
                    "latest_sets": latest['sets'],
                    "latest_reps": latest['reps'],
                    "total_entries": count,
                    "weight_change": round(latest['weight_lbs'] - first['weight_lbs'], 1),
                })

        return results
    except sqlite3.Error:
        return []
    finally:
        if conn:
            conn.close()


def get_quick_status(db_path):
    """Return a quick status summary: last workout, weight, sleep, today's intake."""
    status = {
        "last_workout": None,
        "last_weight": None,
        "today_meals": 0,
        "today_calories": 0,
        "last_sleep": None,
    }

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Last workout
        cursor.execute(
            "SELECT date(timestamp, 'localtime'), target_muscle, duration_minutes "
            "FROM workout_logs ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            status["last_workout"] = f"{row[0]} - {row[1]} ({row[2]} min)"

        # Last weight
        cursor.execute(
            "SELECT date(timestamp, 'localtime'), weight_kg "
            "FROM body_metrics WHERE weight_kg IS NOT NULL "
            "ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            status["last_weight"] = f"{row[1]} kg ({row[0]})"

        # Today's meals
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute(
            "SELECT COUNT(*), COALESCE(SUM(calories),0) FROM food_logs "
            "WHERE date(timestamp, 'localtime') = ?",
            (today,),
        )
        row = cursor.fetchone()
        if row:
            status["today_meals"] = row[0]
            status["today_calories"] = round(row[1], 1)

        # Last sleep
        cursor.execute(
            "SELECT sleep_date, bedtime, wake_time, duration_hours, quality "
            "FROM sleep_logs ORDER BY sleep_date DESC LIMIT 1"
        )
        row = cursor.fetchone()
        if row:
            quality_str = f" ({row['quality']})" if row['quality'] else ""
            status["last_sleep"] = (
                f"{row['sleep_date']} -- {row['bedtime']} to {row['wake_time']} "
                f"({row['duration_hours']}h){quality_str}"
            )

    except Exception:
        pass

    return status


# ---------------------------------------------------------------------------
# Standalone execution: initialize a database
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    db = sys.argv[1] if len(sys.argv) > 1 else "kai_health.db"
    print(init_health_db(db))
    print(init_workout_db(db))
    print(f"Database ready: {db}")
