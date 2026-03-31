# AI Fitness Coach

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-blueviolet.svg)](https://docs.anthropic.com/en/docs/claude-code)

**AI-powered WhatsApp fitness coach** with workout tracking, nutrition logging, and smart recommendations.

Kai is a personal fitness agent that lives in your WhatsApp group. It tracks your workouts, nutrition, sleep, and weight -- then uses that data to give you smart workout suggestions, hold you accountable, and send personalized reminders via cron jobs.

Built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with the WhatsApp channel plugin.

---

## Features

- **Workout Tracking** -- Log sessions with muscle group, duration, location, and exercises
- **Smart Workout Suggestions** -- AI picks exercises based on what you haven't trained recently, adjusts intensity based on your sleep data
- **Progressive Overload Tracking** -- Log weight/sets/reps per exercise, see strength trends over time
- **Nutrition Logging** -- Track calories, protein, carbs, and fat for every meal
- **Weight Tracking** -- Log daily weigh-ins, see trends
- **Sleep Tracking** -- Log sleep times and quality, affects workout intensity recommendations
- **Weekly Planning** -- Smart rescheduling that shows what muscle groups are overdue
- **Automated Reminders** -- Cron-powered WhatsApp messages that check your data and send context-aware nudges
- **Exercise Database** -- 70+ exercises categorized by muscle group and equipment type

### Feature Comparison

| Feature | AI Fitness Coach | MyFitnessPal | Strong App | Fitbod | Apple Health |
|---|---|---|---|---|---|
| WhatsApp integration | Yes | No | No | No | No |
| AI workout suggestions | Yes (context-aware) | No | No | Yes (paid) | No |
| Sleep-adjusted intensity | Yes | No | No | No | No |
| Progressive overload tracking | Yes | No | Yes | Yes | No |
| Nutrition logging | Yes | Yes | No | No | No |
| Automated reminders | Yes (cron + AI) | Basic push | Basic push | Basic push | Basic push |
| Conversational interface | Yes (natural language) | No | No | No | No |
| Fully open source | Yes | No | No | No | No |
| Self-hosted / private data | Yes | No | No | No | Partial |
| Cost | Free (self-hosted) | Freemium ($80/yr) | Freemium ($70/yr) | $60/yr | Free (Apple only) |

---

## Example WhatsApp Conversation

Here is what a typical interaction with Kai looks like in your WhatsApp group:

```
You:    Just had grilled chicken with rice and veggies for lunch

Kai:    Got it! Logged your lunch:
        - Grilled chicken with rice and veggies
        - ~520 kcal | 42g protein | 55g carbs | 12g fat

        Today's totals: 1,040 / 2,200 kcal | 78 / 120g protein
        You've got about 1,160 kcal left -- maybe a protein shake
        later to hit your target?
```

```
You:    What should I train today?

Kai:    Based on your history, you haven't trained Back in 5 days
        and Shoulders in 4 days. Your sleep has been solid (7.5h avg),
        so I'd push the volume a bit.

        Here's a 40-min Back + Shoulders session at Home Gym:

        Warm-up (5 min):
        - Arm circles, band pull-aparts

        Back (20 min):
        - Barbell Rows: 4 x 10 @ moderate weight
        - Dumbbell Rows: 3 x 12 each arm
        - Pull-ups: 3 x max

        Shoulders (10 min):
        - Dumbbell Shoulder Press: 3 x 10
        - Lateral Raises: 3 x 15

        Cool-down (5 min):
        - Stretch lats, traps, rear delts
```

```
[10:00 AM -- Automated Morning Reminder]

Kai:    Good morning! It's been 2 days since your last workout
        (Chest at Home Gym). How was your sleep last night?
        Today might be a good day for Back or Legs -- just say
        the word and I'll build you a plan!
```

---

## How It Works

### High-Level Data Flow

```
+------------------+       +-------------------+       +------------------+
|                  |       |                   |       |                  |
|  You (WhatsApp)  +------>+ Claude Code +     +------>+ kai-cli.py       |
|                  |       | WhatsApp Plugin   |       | (CLI interface)  |
|  "I ate chicken  |       |                   |       |                  |
|   breast + rice" |       | Reads group       |       | Estimates macros |
|                  |       | config (Kai       |       | Calls log-food   |
+------------------+       | persona)          |       |                  |
                           +-------------------+       +--------+---------+
                                                                |
                                                                v
                                                       +--------+---------+
                                                       |                  |
                                                       | db_manager.py    |
                                                       | (SQLite layer)   |
                                                       |                  |
                                                       +--------+---------+
                                                                |
                                                                v
                                                       +--------+---------+
                                                       |                  |
                                                       | kai_health.db    |
                                                       | (local SQLite)   |
                                                       |                  |
                                                       +------------------+
```

### Step-by-Step Flow

1. **You** send a message to your WhatsApp group (e.g., "I ate chicken breast with rice", "What should I train today?", or a photo of your meal)
2. **Claude Code** (with the WhatsApp channel plugin) receives the message and reads the group config file
3. **Kai's personality** (defined in `config/group-config.example.md`) interprets the message -- estimating macros from food descriptions, understanding workout completions, etc.
4. **kai-cli.py** is called with the appropriate command to log data to or query from the local SQLite database
5. **Claude** formats the database response into a friendly, conversational WhatsApp reply
6. **Cron jobs** run twice daily (10 AM and 7:30 PM), fetch your current status via `quick-status`, and use Claude to generate and send a personalized reminder

### Cron Reminder Flow

```
Cron (10 AM) --> workout-reminder.sh --> kai-cli.py quick-status
                                     --> kai-cli.py last-workout
                                              |
                                              v
                                     Claude generates personalized
                                     message based on data
                                              |
                                              v
                                     WhatsApp plugin sends message
                                     to your group
```

---

## Quick Start (5 minutes)

Follow these steps from start to finish. No prior experience required.

### Step 1: Check Prerequisites

You need these three things installed before starting:

#### Python 3.8+

Check if Python is already installed:

```bash
python3 --version
# Expected output: Python 3.8.x or higher (e.g., Python 3.11.5)
```

If not installed:
- **macOS**: `brew install python3` (requires [Homebrew](https://brew.sh/))
- **Ubuntu/Debian**: `sudo apt install python3`
- **Windows**: Download from [python.org](https://www.python.org/downloads/), then use WSL for this project

#### Claude Code CLI

Install it following the [official guide](https://docs.anthropic.com/en/docs/claude-code/getting-started):

```bash
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

> **Note**: Claude Code requires Node.js 18+. If you don't have Node.js, install it from [nodejs.org](https://nodejs.org/).

#### WhatsApp Channel Plugin

The WhatsApp integration uses Claude Code's channel plugin system. This is optional -- the CLI works standalone without WhatsApp.

### Step 2: Clone and Set Up

```bash
# Clone the repository
git clone https://github.com/moltbot0912/ai-fitness-coach.git

# Enter the project directory
cd ai-fitness-coach

# Make the setup script executable and run it
chmod +x setup.sh
./setup.sh
```

The setup script will walk you through:
1. Checking your Python version
2. Creating config files from templates (`.env`, `profile.json`)
3. Initializing the SQLite database (`data/kai_health.db`)
4. Opening your profile for customization
5. Optionally installing cron jobs for automated WhatsApp reminders

### Step 3: Customize Your Profile

Edit `config/profile.json` with your details:

```bash
nano config/profile.json
# Or use any text editor: code, vim, etc.
```

Key things to set:
- **`user_name`** -- Your name (used in reminder messages)
- **`fitness_goals.primary_goal`** -- e.g., "Build muscle", "Lose weight", "General fitness"
- **`nutrition_targets.calories_per_day`** -- Your daily calorie goal
- **`nutrition_targets.protein_g_per_day`** -- Your daily protein goal in grams
- **`workout_preferences.frequency_per_week`** -- How often you work out (e.g., "3-4")
- **`workout_preferences.gym_locations`** -- Your gym name and available equipment

### Step 4: Test It

```bash
# Log a test weight entry
python3 src/kai-cli.py log-weight 70.0

# Check your status (should show the weight you just logged)
python3 src/kai-cli.py quick-status

# Get a workout suggestion
python3 src/kai-cli.py suggest-workout
```

If all three commands run without errors, you are all set.

### Step 5: Connect WhatsApp (Optional)

If you want the WhatsApp integration:

1. Set up the Claude Code WhatsApp channel plugin
2. Copy the group config: `cp config/group-config.example.md /path/to/whatsapp-channel/groups/YOUR_GROUP_ID/config.md`
3. Edit the config to update file paths to your installation
4. Set `KAI_WHATSAPP_CHAT_ID` in your `.env` file
5. Install cron jobs for automated reminders: `./cron/install-cron.sh`

See [docs/SETUP.md](docs/SETUP.md) for the full detailed setup guide.

### Manual Setup (if you prefer)

```bash
# 1. Copy config templates
cp config/.env.example .env
cp config/profile.example.json config/profile.json

# 2. Edit your profile
nano config/profile.json  # Set your name, goals, gym equipment, etc.

# 3. Initialize the database
python3 src/db_manager.py data/kai_health.db

# 4. Test it
python3 src/kai-cli.py quick-status
```

---

## CLI Commands

For the full command reference with all arguments and options, see [docs/COMMANDS.md](docs/COMMANDS.md).

### Logging Data

```bash
# Log a meal
python3 src/kai-cli.py log-food "Chicken breast and rice" 550 45 60 12

# Log weight
python3 src/kai-cli.py log-weight 70.5

# Log a workout session
python3 src/kai-cli.py log-workout "Home Gym" "Chest" 40 "Bench Press, Dumbbell Fly, Push-ups"

# Log sleep
python3 src/kai-cli.py log-sleep 2025-01-15 23:30 07:00 7.5 --quality good

# Log a single exercise (for progressive overload tracking)
python3 src/kai-cli.py log-exercise "Bench Press" "Chest" 135 3 10 --rpe 8
```

### Querying Data

```bash
# Quick status overview
python3 src/kai-cli.py quick-status

# Today's nutrition
python3 src/kai-cli.py daily-summary

# Last 7 days overview
python3 src/kai-cli.py weekly-summary

# Weight trend
python3 src/kai-cli.py weight-trend

# Sleep history
python3 src/kai-cli.py sleep-trend

# Last workout details
python3 src/kai-cli.py last-workout
```

### Smart Features

```bash
# Get a workout suggestion (auto-picks muscle groups you haven't trained)
python3 src/kai-cli.py suggest-workout

# Request specific duration or focus
python3 src/kai-cli.py suggest-workout --duration 30 --focus chest

# Weekly plan with catch-up suggestions
python3 src/kai-cli.py weekly-plan

# Strength progression for all exercises
python3 src/kai-cli.py strength-trend

# Strength progression for a specific exercise
python3 src/kai-cli.py strength-trend "Bench Press"
```

---

## Deployment Options

### Option A: Local PC (always-on machine)

Best if you have a Mac/Linux machine that stays on.

1. Follow the Quick Start above
2. Install cron jobs: `./cron/install-cron.sh`
3. Keep your machine running for the cron reminders to fire

### Option B: Cloud VM ($3-5/month)

Best for reliability. See [docs/AWS_SETUP.md](docs/AWS_SETUP.md) for a step-by-step guide.

**TL;DR:**
1. Launch an AWS Lightsail or EC2 t3.micro instance (or any $5/month VPS)
2. Install Python 3, Claude Code, and the WhatsApp plugin
3. Clone this repo and run `setup.sh`
4. Install cron jobs
5. Done -- reminders run 24/7 even when your laptop is off

---

## Configuration

### Profile (`config/profile.json`)

Your fitness profile controls workout suggestions, nutrition targets, and equipment availability.

Key fields:
- `user_name` -- Your name (used in reminders)
- `fitness_goals.primary_goal` -- Drives set/rep recommendations
- `nutrition_targets` -- Daily calorie and macro goals
- `workout_preferences.frequency_per_week` -- Target workout frequency (e.g. "3-4")
- `workout_preferences.gym_locations` -- Your equipment (determines which exercises are suggested)
- `workout_preferences.preferred_muscle_group_rotation` -- Muscle groups to cycle through

### Environment Variables (`.env`)

| Variable | Default | Description |
|---|---|---|
| `KAI_DB_PATH` | `data/kai_health.db` | SQLite database location |
| `KAI_PROFILE_PATH` | `config/profile.json` | Profile JSON location |
| `KAI_EXERCISES_PATH` | `src/exercises.md` | Exercise database location |
| `KAI_TIMEZONE` | (system default) | Your timezone (e.g. `America/New_York`) |
| `KAI_WHATSAPP_CHAT_ID` | (none) | WhatsApp group ID for reminders |

### WhatsApp Group Config (`config/group-config.example.md`)

If using the WhatsApp channel plugin, this file configures Kai's personality, tone, and behavior for your group chat. Copy it to your WhatsApp channel's group config directory.

---

## How It Works (Detailed)

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full architecture overview.

**In short:**
1. **You** send messages to your WhatsApp group (meal photos, workout reports, questions)
2. **Claude Code** (with the WhatsApp plugin) receives the message and reads the group config
3. **Kai's personality** (defined in the group config) processes the message
4. **kai-cli.py** logs data to / queries from a local SQLite database
5. **Cron jobs** run twice daily, fetch your status, and send personalized reminders

---

## Adding Exercises

Edit `src/exercises.md` to add your own exercises. The format is:

```markdown
## Muscle Group Name
### Equipment: Equipment Type
- Exercise Name
- Another Exercise
```

Equipment types used by the suggestion engine: `Barbell`, `Dumbbell`, `Cable`, `Machine`, `Bodyweight`.

---

## FAQ

### Do I need a paid API key?

Yes, Claude Code requires an Anthropic API subscription or a Claude Pro/Team plan. The AI Fitness Coach project itself is free and open source, but the underlying Claude Code CLI requires authentication.

### Can I use this without WhatsApp?

Yes. The CLI (`kai-cli.py`) works entirely standalone. You can log food, workouts, sleep, and weight directly from the terminal. The WhatsApp integration is optional and adds the conversational interface and automated reminders.

### Where is my data stored?

All data is stored locally in a SQLite database file (`data/kai_health.db`). Nothing is sent to external servers beyond the Claude API calls for generating responses. Your fitness data stays on your machine.

### Can I run this on Windows?

The CLI and database work on Windows natively. For cron-based reminders and the WhatsApp integration, use WSL (Windows Subsystem for Linux). See the platform-specific notes in [docs/SETUP.md](docs/SETUP.md).

### How do I back up my data?

Copy the `data/kai_health.db` file. That single file contains all your workouts, nutrition logs, weight history, and sleep data. See [docs/AWS_SETUP.md](docs/AWS_SETUP.md) for automated backup instructions.

### Can multiple people use the same instance?

Currently, the system is designed for a single user per installation. Each person should have their own profile and database. Multiple people in the same WhatsApp group will share a single Kai bot, but data tracking is per-installation.

### How accurate are the AI macro estimates?

Kai uses Claude's general knowledge to estimate macros from food descriptions. The estimates are reasonable approximations but not lab-precise. For more accuracy, provide specific quantities (e.g., "200g chicken breast" instead of "some chicken"). You can always override by providing exact macro values.

### How do I change the reminder times?

Edit your crontab: `crontab -e`. The default times are 10:00 AM and 7:30 PM. Change the cron expressions to your preferred times. See `cron/install-cron.sh` for the format.

---

## Contributing

Contributions are welcome! Here are some ideas:

- **New exercises** -- Add exercises to `src/exercises.md`
- **New commands** -- Add CLI commands for new tracking features
- **Localization** -- Add more language support (Chinese docs already available in `README_ZH.md`)
- **Integrations** -- Connect to fitness APIs, smartwatches, etc.
- **Charts/visualization** -- Generate progress charts
- **Unit tests** -- Add test coverage for `db_manager.py` and CLI commands

### Development

```bash
# Clone and set up
git clone https://github.com/moltbot0912/ai-fitness-coach.git
cd ai-fitness-coach
./setup.sh

# Run the CLI
python3 src/kai-cli.py --help

# Run tests (if any)
python3 -m pytest tests/
```

---

## License

MIT License. See [LICENSE](LICENSE).
