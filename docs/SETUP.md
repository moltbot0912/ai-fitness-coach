# Detailed Setup Guide

This guide walks through every step to get AI Fitness Coach running. It assumes no prior experience with Python projects or command-line tools.

---

## Prerequisites

### Python 3.12+

Check your version:
```bash
python3 --version
```

**Expected output:**
```
Python 3.11.5    # (any version 3.8 or higher is fine)
```

If you don't have Python 3.12+:

- **macOS**: `brew install python3` (requires [Homebrew](https://brew.sh/); install Homebrew first if needed)
- **Ubuntu/Debian**: `sudo apt update && sudo apt install -y python3`

### Claude Code CLI

The WhatsApp integration requires Claude Code. Install it following the [official guide](https://docs.anthropic.com/en/docs/claude-code/getting-started).

```bash
# Install Claude Code (requires Node.js 18+)
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

**Expected output:**
```
claude-code v1.x.x
```

> **Don't have Node.js?** Install it first:
> - macOS: `brew install node`
> - Ubuntu/Debian: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs`

### WhatsApp Channel Plugin

The WhatsApp integration uses Claude Code's channel plugin system. This is **optional** -- you can use the CLI without it.

To set up the WhatsApp channel plugin:
1. Refer to the [Claude Code channel plugins documentation](https://docs.anthropic.com/en/docs/claude-code)
2. The plugin allows Claude Code to send and receive WhatsApp messages
3. Once installed, you will get a chat ID for your WhatsApp group that you will need later

---

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/moltbot0912/ai-fitness-coach.git
cd ai-fitness-coach
```

**What you should see:** A directory with `README.md`, `setup.sh`, `src/`, `config/`, `docs/`, etc.

```bash
ls
# Expected: LICENSE  README.md  README_ZH.md  config/  cron/  data/  docs/  requirements.txt  setup.sh  src/
```

### 2. Run the Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

**What happens during setup:**
```
======================================
  AI Fitness Coach -- Setup
======================================

[1/6] Checking Python...
  Found Python 3.11
  OK

[2/6] Checking dependencies...
  No external dependencies needed (uses Python standard library only)

[3/6] Setting up configuration...
  Created .env from template
  Created config/profile.json from template

[4/6] Initializing database...
  Database initialized successfully.
  Workout tables initialized successfully.
  Database ready: .../data/fitness.db

[5/6] Profile setup...
  Your profile is at: config/profile.json
  Open profile.json for editing now? [y/N]

[6/6] Automated reminders (optional)...
  Install cron jobs for automated reminders? [y/N]

======================================
  Setup complete!
======================================
```

This creates:
- `.env` -- Environment configuration
- `config/profile.json` -- Your fitness profile
- `data/fitness.db` -- SQLite database (all your data will live here)

### 3. Configure Your Profile

Edit `config/profile.json`:

```bash
# Use any text editor you prefer
nano config/profile.json
# Or: code config/profile.json
# Or: vim config/profile.json
```

Here is the full profile with explanations:

```json
{
  "user_name": "YourName",
  "fitness_goals": {
    "primary_goal": "Build muscle and increase strength",
    "current_stats": {
      "height_cm": 175,
      "weight_kg": 70
    },
    "target_weight_kg": 75
  },
  "nutrition_targets": {
    "calories_per_day": 2200,
    "protein_g_per_day": 120,
    "carbs_g_per_day": 250,
    "fat_g_per_day": 70
  },
  "workout_preferences": {
    "duration_minutes": [30, 40],
    "frequency_per_week": "3-4",
    "preferred_muscle_group_rotation": [
      "Chest", "Back", "Legs", "Shoulders", "Biceps", "Triceps", "Core"
    ],
    "gym_locations": {
      "My Gym": {
        "equipment": ["Dumbbells", "Barbell", "Bench"],
        "categories": ["Barbell", "Dumbbell", "Bodyweight"]
      }
    }
  }
}
```

**Field-by-field guide:**

| Field | What to set | Example |
|---|---|---|
| `user_name` | Your first name | `"Alex"` |
| `primary_goal` | Your fitness objective | `"Lose weight"`, `"Build muscle"`, `"General fitness"` |
| `height_cm` | Your height in centimeters | `175` |
| `weight_kg` | Your current weight in kg | `70` |
| `target_weight_kg` | Your goal weight | `75` (gain) or `65` (lose) |
| `calories_per_day` | Daily calorie target | `2200` (bulk), `1800` (cut) |
| `protein_g_per_day` | Daily protein in grams | Rule of thumb: 1.6-2.2g per kg body weight |
| `frequency_per_week` | Workout days per week | `"3-4"`, `"5-6"` |
| `duration_minutes` | Workout length range in min | `[30, 40]` or `[45, 60]` |
| `gym_locations` | Where you work out + equipment | See equipment categories below |

**Equipment categories** determine which exercises get suggested:
- `Barbell` -- Barbell exercises (bench press, squats, rows)
- `Dumbbell` -- Dumbbell exercises (curls, presses, flies)
- `Cable` -- Cable machine exercises (crossovers, pushdowns)
- `Machine` -- Gym machines (lat pulldown, leg press)
- `Bodyweight` -- No equipment needed (push-ups, pull-ups, planks)

> **Tip**: If you work out at home with just dumbbells, set categories to `["Dumbbell", "Bodyweight"]`. If you go to a full gym, include all five.

### 4. Configure Environment

Edit `.env`:

```bash
nano .env
```

```bash
# Required for WhatsApp reminders (leave commented out if not using WhatsApp)
AFC_WHATSAPP_CHAT_ID=your-group-id@g.us

# Optional -- set your timezone for accurate date handling
AFC_TIMEZONE=America/New_York
```

**Common timezone values:**
| Region | Value |
|---|---|
| US Eastern | `America/New_York` |
| US Pacific | `America/Los_Angeles` |
| UK | `Europe/London` |
| Central Europe | `Europe/Berlin` |
| Japan | `Asia/Tokyo` |
| Taiwan | `Asia/Taipei` |
| Australia Eastern | `Australia/Sydney` |

To find your WhatsApp group chat ID, check the WhatsApp channel plugin documentation. The ID typically looks like `120363012345678901@g.us`.

### 5. Test the CLI

Run these commands one at a time to verify everything works:

```bash
# 1. Log a test weight entry
python3 src/fitness-cli.py log-weight 70.0
# Expected: "Logged weight: 70.0 kg"

# 2. Check your status
python3 src/fitness-cli.py quick-status
# Expected: Shows last workout, weight, sleep, today's intake

# 3. Log a test meal
python3 src/fitness-cli.py log-food "Test meal" 500 30 50 15
# Expected: "Logged food: Test meal (500 kcal)" followed by daily totals

# 4. Get a workout suggestion
python3 src/fitness-cli.py suggest-workout
# Expected: A structured workout plan based on your profile
```

### 6. Set Up WhatsApp Integration

> **Skip this step** if you only want to use the CLI directly.

1. Make sure the Claude Code WhatsApp channel plugin is installed and paired with your phone.

2. Copy the group config to your WhatsApp channel's group directory:
   ```bash
   cp config/group-config.example.md /path/to/whatsapp-channel/groups/YOUR_GROUP_ID/config.md
   ```

3. Edit the copied config file to update all file paths. Replace `/path/to/ai-fitness-coach/` with your actual installation path:
   ```bash
   # Find your actual path
   pwd
   # Then edit the config and replace all /path/to/ai-fitness-coach/ with the output of pwd
   ```

4. Test by sending a message to your WhatsApp group (e.g., "What's my status?"). The coach should respond.

### 7. Install Cron Jobs (Optional)

```bash
./cron/install-cron.sh
```

This installs two daily reminders:
- **10:00 AM** -- Morning check-in (asks about sleep, reminds about workouts)
- **7:30 PM** -- Evening check-in (checks nutrition progress, workout status)

**What the installer shows:**
```
AI Fitness Coach -- Cron Job Installer
=================================

Project directory: /Users/you/ai-fitness-coach
Reminder script:   /Users/you/ai-fitness-coach/cron/workout-reminder.sh
Log file:          /Users/you/ai-fitness-coach/cron.log

The following cron jobs will be added:

  Morning (10:00 AM): 0 10 * * * AFC_DIR=... .../cron/workout-reminder.sh >> .../cron.log 2>&1
  Evening (7:30 PM):  30 19 * * * AFC_DIR=... .../cron/workout-reminder.sh >> .../cron.log 2>&1

Install these cron jobs? [y/N]
```

Customize times by editing your crontab: `crontab -e`

> **Cron format reminder**: `minute hour * * *`
> - `0 8 * * *` = 8:00 AM daily
> - `30 20 * * *` = 8:30 PM daily
> - `0 10 * * 1-5` = 10:00 AM weekdays only

---

## Verify Installation Checklist

After setup, verify each component is working:

- [ ] **Python version**: `python3 --version` shows 3.12+
- [ ] **Database exists**: `ls data/fitness.db` shows the file
- [ ] **Profile exists**: `ls config/profile.json` shows the file
- [ ] **CLI runs**: `python3 src/fitness-cli.py --help` shows the help menu
- [ ] **Log weight**: `python3 src/fitness-cli.py log-weight 70.0` succeeds
- [ ] **Log food**: `python3 src/fitness-cli.py log-food "Test" 500 30 50 15` succeeds
- [ ] **Quick status**: `python3 src/fitness-cli.py quick-status` shows data
- [ ] **Workout suggestion**: `python3 src/fitness-cli.py suggest-workout` generates a plan
- [ ] **Cron jobs** (if installed): `crontab -l` shows the AI Fitness Coach entries
- [ ] **WhatsApp** (if configured): Send a test message to your group and verify the coach responds

---

## Platform-Specific Notes

### macOS

- **Homebrew recommended**: Install Python and Node.js via `brew install python3 node`
- **Cron permissions**: macOS requires granting cron Full Disk Access. Go to **System Settings > Privacy & Security > Full Disk Access** and add `/usr/sbin/cron`
- **Gatekeeper**: If setup.sh is blocked, run `xattr -d com.apple.quarantine setup.sh` to remove the quarantine flag
- **Default shell**: macOS uses zsh by default. All scripts are written for bash/zsh compatibility

### Linux (Ubuntu/Debian)

- **Python**: Usually pre-installed. If not: `sudo apt update && sudo apt install -y python3`
- **Node.js**: Install via NodeSource: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs`
- **Cron**: Pre-installed and running on most distributions. Verify with `systemctl status cron`
- **Permissions**: If you get permission errors, check file ownership: `ls -la src/fitness-cli.py`

---

## Troubleshooting

### "No module named 'db_manager'"

**Cause**: Running the CLI from outside the project directory.

**Fix**: Use the full path to the script:
```bash
python3 /path/to/ai-fitness-coach/src/fitness-cli.py quick-status
```

Or `cd` into the project directory first:
```bash
cd /path/to/ai-fitness-coach
python3 src/fitness-cli.py quick-status
```

### Database not found / "no such table"

**Cause**: The database was not initialized, or the setup script was interrupted.

**Fix**: Manually create the database:
```bash
mkdir -p data
python3 src/db_manager.py data/fitness.db
```

**Expected output:**
```
Database initialized successfully.
Workout tables initialized successfully.
Database ready: data/fitness.db
```

### "Permission denied" when running setup.sh

**Cause**: The script is not marked as executable.

**Fix**:
```bash
chmod +x setup.sh
chmod +x cron/install-cron.sh
chmod +x cron/workout-reminder.sh
```

### Cron jobs not firing

1. **Check cron is set up**: `crontab -l` -- should show the AI Fitness Coach entries
2. **Check the log file**: `cat cron.log` -- look for errors
3. **Ensure full paths** are used in the crontab entry (the installer does this automatically)
4. **macOS**: Grant cron Full Disk Access in **System Settings > Privacy & Security**
5. **Test the script manually**:
   ```bash
   AFC_DIR=$(pwd) ./cron/workout-reminder.sh
   ```

### WhatsApp messages not sending

1. **Verify Claude Code is authenticated**: `claude --version` should show the version without errors
2. **Check the WhatsApp plugin status**: Make sure the plugin is installed and your device is paired
3. **Verify chat ID**: Make sure `AFC_WHATSAPP_CHAT_ID` in `.env` matches your actual group ID
4. **Test Claude directly**: Try running a simple Claude command to verify it works:
   ```bash
   claude -p "Say hello"
   ```

### "python3: command not found"

**Cause**: Python 3 is not installed or not in your PATH.

**Fix by platform**:
- macOS: `brew install python3`
- Ubuntu/Debian: `sudo apt install python3`
- Check if it is installed under a different name: `python --version` (some systems use `python` instead of `python3`)

### "npm: command not found" (when installing Claude Code)

**Cause**: Node.js is not installed.

**Fix**: Install Node.js first:
- macOS: `brew install node`
- Ubuntu/Debian: `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs`
- Or download from [nodejs.org](https://nodejs.org/)

### Profile changes not taking effect

**Cause**: The CLI reads `config/profile.json` on every run. If changes are not taking effect:

1. Make sure you edited the right file: `cat config/profile.json`
2. Check for JSON syntax errors: `python3 -c "import json; json.load(open('config/profile.json'))"`
3. The file should parse without errors. If you see an error, fix the JSON syntax (missing commas, quotes, brackets, etc.)

---

## Limitations and Warnings

- **Requires Anthropic API key** -- Claude Code requires an active Claude Pro, Team, or Enterprise subscription, or API credits. This is a recurring cost.
- **Requires an always-on machine** -- For WhatsApp integration and cron reminders, you need a machine that stays running (your computer or a cloud VM at ~$3-5/month). See [AWS_SETUP.md](AWS_SETUP.md).
- **WhatsApp linked device limitations** -- The WhatsApp plugin links as an additional device to your account. WhatsApp allows a limited number of linked devices, and the link may need to be re-established periodically.
- **Nutrition estimates are approximations** -- AI-generated calorie and macro estimates are based on general knowledge, not certified nutritional databases. They are useful for tracking trends but should not be treated as exact values.
- **Not a substitute for professional advice** -- This tool is not a replacement for professional medical, nutritional, or fitness advice. Consult a qualified professional before starting any new exercise or diet program.
- **Voice transcription accuracy varies** -- Voice message transcription (via Whisper) works best in quiet environments. Background noise, accents, and uncommon terminology may reduce accuracy.
- **Supported platforms** -- macOS and Linux only. Windows is not supported.
