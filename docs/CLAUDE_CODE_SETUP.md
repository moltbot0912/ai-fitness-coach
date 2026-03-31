# Claude Code + WhatsApp Channel Plugin Setup Guide

This guide walks you through setting up Claude Code with the WhatsApp channel plugin to power the AI Fitness Coach. By the end, you will have a fully working WhatsApp fitness bot that tracks your workouts, nutrition, and sleep -- and sends you automated reminders.

**Estimated setup time:** 30-60 minutes (first time).

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [WhatsApp Channel Plugin Setup](#2-whatsapp-channel-plugin-setup)
3. [Project Directory Setup](#3-project-directory-setup)
4. [Claude Code Configuration](#4-claude-code-configuration)
5. [Tools / CLI Integration](#5-tools--cli-integration)
6. [Memory Setup](#6-memory-setup)
7. [Cron Jobs Setup](#7-cron-jobs-setup)
8. [Running 24/7](#8-running-247)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

You need three things before starting:

### 1.1 Claude Code CLI

Claude Code is Anthropic's official command-line interface for Claude. It is the runtime that powers this entire project.

**Install Claude Code:**

```bash
# Install via npm (requires Node.js 18+)
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

If you do not have Node.js, install it first:
- **macOS:** `brew install node`
- **Ubuntu/Debian:** `curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs`
- **Windows:** Download from [nodejs.org](https://nodejs.org/)

**Authenticate Claude Code:**

```bash
claude auth login
```

This opens a browser window where you sign in with your Anthropic account. You need an active Claude Pro, Team, or Enterprise subscription (or API credits) to use Claude Code.

### 1.2 Bun Runtime

The WhatsApp channel plugin is built with [Bun](https://bun.sh), a fast JavaScript runtime. The plugin's MCP server requires Bun to run.

```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash

# Verify installation
bun --version
```

### 1.3 Python 3.8+

The fitness tracking CLI (`kai-cli.py`) is written in Python and uses only the standard library -- no pip packages required.

```bash
# Check your Python version
python3 --version

# If not installed:
# macOS: brew install python3
# Ubuntu: sudo apt install python3
```

### 1.4 WhatsApp Account

You need:
- A WhatsApp account with an active phone number
- The WhatsApp app installed on your phone (iOS or Android)
- The ability to scan QR codes or enter pairing codes in the WhatsApp "Linked Devices" screen

---

## 2. WhatsApp Channel Plugin Setup

The WhatsApp channel plugin connects Claude Code to WhatsApp using the linked-device protocol (the same protocol WhatsApp Web uses). It is **not** a bot API -- it links to your personal WhatsApp account as an additional device.

### 2.1 Install the Plugin

The plugin is hosted at [Rich627/whatsapp-claude-plugin](https://github.com/Rich627/whatsapp-claude-plugin) on GitHub.

From inside a Claude Code session, install it:

```bash
# Start Claude Code
claude

# Inside the Claude Code session, run:
/plugin install whatsapp@whatsapp-claude-plugin
```

This downloads the plugin and registers it in your Claude Code settings at `~/.claude/settings.json`.

> **What happens behind the scenes:** The plugin is cloned to `~/.claude/plugins/` and its MCP server configuration is registered. The MCP server uses Baileys (a WhatsApp Web API library) to connect to WhatsApp as a linked device.

### 2.2 Configure the Plugin Marketplace

If the plugin marketplace is not yet registered, you may need to add it manually. Check your `~/.claude/settings.json` for:

```json
{
  "extraKnownMarketplaces": {
    "whatsapp-claude-plugin": {
      "source": {
        "source": "github",
        "repo": "Rich627/whatsapp-claude-plugin"
      }
    }
  },
  "enabledPlugins": {
    "whatsapp@whatsapp-claude-plugin": true
  }
}
```

### 2.3 Device Pairing (QR Code)

The first time you launch Claude Code with the WhatsApp plugin, it needs to pair with your WhatsApp account.

**Step 1:** Launch Claude Code with the WhatsApp channel:

```bash
claude --channels plugin:whatsapp@whatsapp-claude-plugin
```

**Step 2:** Run the setup wizard inside the Claude Code session:

```
/whatsapp:setup
```

**Step 3:** The wizard generates a QR code image. To scan it:

1. Open WhatsApp on your phone
2. Go to **Settings** (or tap the three dots on Android)
3. Tap **Linked Devices**
4. Tap **Link a Device**
5. Scan the QR code displayed in your terminal

**Alternative -- Pairing Code:** If you cannot scan the QR code (e.g., the terminal does not render images well), you can pair by phone number instead:

1. In the WhatsApp "Link a Device" screen, tap **Link with phone number instead**
2. The setup wizard will show you a numeric pairing code
3. Enter that code in WhatsApp

**Step 4:** Once paired, you will see a "Connected" confirmation. The authentication credentials are saved to `~/.claude/channels/whatsapp/.baileys_auth/` and will be reused on future launches.

> **Warning:** WhatsApp may temporarily lock pairing if you attempt too many times in a short period. If this happens, wait 10-15 minutes before trying again.

### 2.4 Access Control (Allowlist)

By default, the plugin uses a **pairing** policy: when an unknown person messages the linked WhatsApp number, the server replies with a 6-character pairing code and drops the message. You approve them from your Claude Code session.

**Managing access:**

```bash
# Inside Claude Code, run these skill commands:

# View current access state
/whatsapp:access

# Approve a pending pairing code
/whatsapp:access pair a4f91c

# Add a user directly by their WhatsApp JID
/whatsapp:access allow 886912345678@s.whatsapp.net

# Remove a user
/whatsapp:access remove 886912345678@s.whatsapp.net

# Change policy to allowlist-only (silently drops unknown senders)
/whatsapp:access policy allowlist

# Enable a WhatsApp group
/whatsapp:access group add 120363424405607157@g.us

# Enable a group without requiring @mentions
/whatsapp:access group add 120363424405607157@g.us --no-mention
```

**WhatsApp JIDs:** User IDs are phone numbers with country code (no leading `+`) followed by `@s.whatsapp.net`. For example, the US number +1-555-123-4567 becomes `15551234567@s.whatsapp.net`. Group IDs end in `@g.us`.

The access configuration is stored at `~/.claude/channels/whatsapp/access.json`:

```json
{
  "dmPolicy": "pairing",
  "allowFrom": ["886912345678@s.whatsapp.net"],
  "groups": {
    "120363424405607157@g.us": {
      "requireMention": false,
      "allowFrom": []
    }
  },
  "mentionPatterns": ["claude", "kai"],
  "ackReaction": ""
}
```

---

## 3. Project Directory Setup

### 3.1 Clone the Repository

```bash
# Choose where to put the project (home directory or Desktop are both fine)
cd ~/Desktop
git clone https://github.com/moltbot0912/ai-fitness-coach.git
cd ai-fitness-coach
```

### 3.2 Run the Setup Script

```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
1. Check your Python version
2. Create `.env` from `config/.env.example`
3. Create `config/profile.json` from `config/profile.example.json`
4. Initialize the SQLite database at `data/kai_health.db`
5. Ask you to customize your profile
6. Optionally install cron jobs

### 3.3 Directory Structure Explained

After setup, your project looks like this:

```
ai-fitness-coach/
  config/
    .env.example           # Template for environment variables
    profile.example.json   # Template for user profile
    profile.json           # YOUR profile (created by setup, git-ignored)
    group-config.example.md  # Template for WhatsApp group personality config
  cron/
    workout-reminder.sh    # Cron script that sends WhatsApp reminders
    install-cron.sh        # Script to install cron entries
  data/
    kai_health.db          # SQLite database (created by setup, git-ignored)
  docs/
    ARCHITECTURE.md        # System architecture overview
    AWS_SETUP.md           # Cloud deployment guide
    COMMANDS.md            # CLI command reference
    SETUP.md               # General setup guide
    CLAUDE_CODE_SETUP.md   # This file
  src/
    kai-cli.py             # Main CLI tool for all fitness operations
    db_manager.py          # SQLite database layer
    exercises.md           # Exercise database (70+ exercises)
  .env                     # YOUR environment config (created by setup, git-ignored)
  setup.sh                 # One-click setup script
  README.md                # Project overview
```

**Important:** The `.env`, `config/profile.json`, and `data/` directory are in `.gitignore`. They contain your personal data and will not be overwritten by `git pull`.

### 3.4 Where to Run Claude Code From

Always run Claude Code from the `ai-fitness-coach/` project root. This ensures the CLI paths resolve correctly:

```bash
cd ~/Desktop/ai-fitness-coach
claude --channels plugin:whatsapp@whatsapp-claude-plugin
```

The `kai-cli.py` tool automatically loads `.env` from the project root, so relative paths like `data/kai_health.db` work when you run from this directory.

---

## 4. Claude Code Configuration

### 4.1 How Group Config Works (the "Soul" File)

When Claude Code receives a WhatsApp message from a group, the WhatsApp plugin reads a `config.md` file that defines the personality, instructions, and tools for that group. This is the heart of the AI Fitness Coach.

The config file is structured like this:

```markdown
# Soul -- AI Fitness Coach

## Identity
Name: Kai
Role: Fitness Coach -- tracks workouts, provides suggestions

## Communication Style
- Friendly, encouraging tone
- Use emojis to keep things fun
- Keep messages concise (3-5 sentences)

## Goals
- Track workout sessions
- Provide workout suggestions and plans
- Track nutrition (calories, protein, carbs, fat)
- Track sleep for recovery optimization

## Boundaries
- Do not provide medical advice
- Respect physical limitations and injuries

## Tools
Use the Kai CLI to log and query health/fitness data. Run commands via Bash.
(... CLI commands listed here ...)

## Cron Jobs
- Morning reminder: Daily 10:00 AM
- Evening reminder: Daily 7:30 PM
```

A template is provided at `config/group-config.example.md`. You will copy this to the correct location in step 4.3.

### 4.2 Create a WhatsApp Group and Get the Chat ID

You need a WhatsApp group to serve as your fitness coaching channel.

**Step 1: Create a WhatsApp group.**

1. Open WhatsApp on your phone
2. Create a new group (you can add just yourself if you want a personal coaching group)
3. Name it something like "Fitness Coach" or "Kai Workout"

**Step 2: Get the group's chat ID.**

The easiest way to find the group ID is to send a message in the group after the WhatsApp plugin is connected. The plugin logs group IDs for all incoming messages.

Method A -- Send a message and check logs:
1. Make sure Claude Code is running with the WhatsApp channel
2. Send any message in the new group from your phone
3. If the group is not yet enabled, the server logs the group JID
4. You can also check the Claude Code session -- it will show the incoming message with the `chat_id`

Method B -- Enable the group and watch for it:
```bash
# Inside Claude Code, run the access skill to see known groups:
/whatsapp:access
```

Group IDs look like `120363424405607157@g.us`.

**Step 3: Enable the group in access control.**

```bash
# Inside Claude Code:
/whatsapp:access group add YOUR_GROUP_ID@g.us --no-mention
```

The `--no-mention` flag means the bot responds to every message in the group, not just @mentions. For a personal fitness group, this is usually what you want.

### 4.3 Where Config Files Go

The WhatsApp plugin looks for group config files in:

```
~/.claude/channels/whatsapp/groups/<group_id>/config.md
```

For example, if your group ID is `120363424405607157@g.us`:

```
~/.claude/channels/whatsapp/groups/120363424405607157@g.us/config.md
```

**Set up the group config:**

```bash
# Create the group directory
mkdir -p ~/.claude/channels/whatsapp/groups/YOUR_GROUP_ID@g.us

# Copy the template config
cp ~/Desktop/ai-fitness-coach/config/group-config.example.md \
   ~/.claude/channels/whatsapp/groups/YOUR_GROUP_ID@g.us/config.md
```

**Important: Update file paths in the config!**

Open the config file and replace all `/path/to/ai-fitness-coach/` with your actual project path. For example, if you cloned to `~/Desktop/ai-fitness-coach`, change:

```bash
python3 /path/to/ai-fitness-coach/src/kai-cli.py log-food ...
```

to:

```bash
python3 /Users/yourusername/Desktop/ai-fitness-coach/src/kai-cli.py log-food ...
```

> **Use absolute paths.** The WhatsApp plugin may run commands from any working directory, so relative paths will break. Always use full paths like `/Users/yourusername/Desktop/ai-fitness-coach/src/kai-cli.py`.

### 4.4 CLAUDE.md / AGENTS.md (Optional)

Claude Code supports project-level instruction files:

- **CLAUDE.md** -- Placed in the project root, this file gives Claude Code context about the project every time it opens a session in that directory.
- **AGENTS.md** -- Similar to CLAUDE.md but specifically for agent-mode behavior.

For the AI Fitness Coach, you generally do not need a CLAUDE.md because the group `config.md` handles the personality and instructions when messages arrive via WhatsApp. However, if you want Claude Code to have project context when you work on the codebase directly (not via WhatsApp), you can create one:

```bash
# Optional: create a project-level CLAUDE.md
cat > ~/Desktop/ai-fitness-coach/CLAUDE.md << 'EOF'
# AI Fitness Coach

This is a WhatsApp-based fitness coaching bot powered by Claude Code.

## Key files
- src/kai-cli.py -- Main CLI for all fitness operations
- src/db_manager.py -- SQLite database layer
- config/profile.json -- User's fitness profile
- config/group-config.example.md -- WhatsApp group personality template

## Development
- Python 3.8+ (standard library only, no external packages)
- Database: SQLite at data/kai_health.db
- Run CLI: python3 src/kai-cli.py --help
EOF
```

### 4.5 Environment Variables

Edit the `.env` file in the project root:

```bash
# Required for automated WhatsApp reminders
KAI_WHATSAPP_CHAT_ID=120363424405607157@g.us

# Optional: your timezone (affects cron timing context)
KAI_TIMEZONE=America/New_York

# Optional: override default paths
# KAI_DB_PATH=./data/kai_health.db
# KAI_PROFILE_PATH=./config/profile.json
# KAI_EXERCISES_PATH=./src/exercises.md
```

Replace `120363424405607157@g.us` with your actual group ID from step 4.2.

---

## 5. Tools / CLI Integration

### 5.1 How Claude Code Discovers and Uses CLI Tools

Claude Code does not have a hardcoded list of tools. Instead, the group `config.md` file tells it which commands are available and how to use them. When a WhatsApp message arrives:

1. The WhatsApp plugin reads `config.md` for the group
2. Claude sees the `## Tools` section, which lists all available CLI commands
3. Claude decides which command to run based on the user's message
4. Claude executes the command using the Bash tool
5. Claude reads the output and formats a friendly response

This means **you control what tools Claude has access to** by editing the `## Tools` section in your group's `config.md`.

### 5.2 The Tools Section Pattern

The `## Tools` section in `config.md` follows this pattern:

```markdown
## Tools

Use the Kai CLI to log and query health/fitness data. Run commands via Bash.

**Logging data:**
\`\`\`bash
# Log food (all positional args required: description, calories, protein_g, carbs_g, fat_g)
python3 /full/path/to/ai-fitness-coach/src/kai-cli.py log-food "<description>" <calories> <protein_g> <carbs_g> <fat_g>

# Log weight
python3 /full/path/to/ai-fitness-coach/src/kai-cli.py log-weight <weight_kg>
\`\`\`

**When to use:**
- When the user reports eating something, estimate macros and use `log-food`
- When the user shares a weight, use `log-weight`
```

Each command includes:
- The full command syntax with placeholder arguments
- Comments explaining what the arguments mean
- A "When to use" section that guides Claude on when to invoke each command

### 5.3 Example: How Claude Uses kai-cli.py

**User sends in WhatsApp:** "I just had a chicken salad for lunch"

**Claude's internal process:**
1. Reads the `## Tools` section from the group config
2. Recognizes this is a food logging situation
3. Estimates the macros for a chicken salad (e.g., 450 cal, 35g protein, 20g carbs, 18g fat)
4. Runs: `python3 /path/to/src/kai-cli.py log-food "Chicken salad" 450 35 20 18`
5. Reads the CLI output (which includes today's running totals)
6. Sends a WhatsApp reply like: "Logged your chicken salad! You're at 1,200 / 2,200 kcal today. Keep it up!"

### 5.4 Adding Your Own Tools

You can add any CLI tool to the `## Tools` section. For example, if you have a separate smartcard CLI:

```markdown
## Tools

(... existing kai-cli commands ...)

**Smartcard tracking:**
\`\`\`bash
# Check credit card spending summary
python3 /path/to/smartcard-cli.py summary --month current

# Log a transaction
python3 /path/to/smartcard-cli.py log-tx "<description>" <amount> "<category>"
\`\`\`

**When to use:**
- When the user asks about spending, use the smartcard summary command
- When the user mentions a purchase, use log-tx to record it
```

Claude will learn to use these tools from the instructions in config.md.

### 5.5 Available kai-cli.py Commands

For a full command reference, see `docs/COMMANDS.md`. Quick summary:

| Command | Purpose |
|---|---|
| `log-food` | Log a meal with calories and macros |
| `log-weight` | Log a weight measurement |
| `log-workout` | Log a completed workout session |
| `log-sleep` | Log sleep data (bedtime, wake time, quality) |
| `log-exercise` | Log individual exercise for progressive overload |
| `quick-status` | Snapshot of last workout, weight, sleep, today's intake |
| `daily-summary` | Today's nutrition totals |
| `weekly-summary` | Last 7 days overview |
| `weight-trend` | Weight history |
| `sleep-trend` | Sleep history and averages |
| `suggest-workout` | AI-generated workout based on history and sleep |
| `strength-trend` | Progressive overload tracking |
| `weekly-plan` | Weekly plan with catch-up suggestions |
| `last-workout` | Details of the most recent workout |

---

## 6. Memory Setup

### 6.1 What is memory.md?

The WhatsApp plugin has a built-in memory system. After meaningful conversations in a group, Claude appends a brief summary to `memory.md`. At the start of each new conversation, Claude reads this file to recall prior context.

This gives Claude persistent memory across sessions -- it remembers your goals, recent progress, injuries, preferences, and anything discussed in the group.

### 6.2 Where memory.md Lives

Memory files are stored per-group alongside the config:

```
~/.claude/channels/whatsapp/groups/<group_id>/memory.md
```

For example:
```
~/.claude/channels/whatsapp/groups/120363424405607157@g.us/memory.md
```

### 6.3 Memory Format

The file uses a simple dated-entry format:

```markdown
# Group Memory
<!-- Claude appends conversation summaries here automatically -->

## 2026-03-27 21:00
- User logged 3 workouts this week (chest, back, legs)
- Protein intake has been consistently under target
- Discussed switching from 3-day to 4-day split

## 2026-03-28 20:00
- User reported knee discomfort during squats
- Adjusted leg day to remove barbell squats, added leg press instead
- Weight trend: 70.2 kg (up from 69.8 last week)
```

### 6.4 Group Memory vs Project Memory

| | Group Memory | Project Memory |
|---|---|---|
| **File** | `~/.claude/channels/whatsapp/groups/<id>/memory.md` | `CLAUDE.md` in project root |
| **Scope** | One WhatsApp group | One code project |
| **Written by** | Claude (automatically after conversations) | You (manually) |
| **Read by** | Claude when a WhatsApp message arrives from that group | Claude when you open the project in Claude Code |
| **Purpose** | Remember user context, preferences, conversation history | Give Claude context about the codebase |

### 6.5 Managing Memory

The memory file grows over time. You can:

- **Read it** to see what Claude remembers: `cat ~/.claude/channels/whatsapp/groups/YOUR_GROUP_ID/memory.md`
- **Edit it** to correct mistakes or remove outdated information
- **Clear it** to start fresh: `echo "# Group Memory" > ~/.claude/channels/whatsapp/groups/YOUR_GROUP_ID/memory.md`
- **Seed it** with initial context (your goals, schedule, preferences) so Claude has context from day one

**Tip:** Before your first conversation, you can pre-populate memory.md with your fitness background:

```markdown
# Group Memory

## Initial Context
- User: [Your Name]
- Goal: Build muscle, target weight 75 kg (currently 70 kg)
- Schedule: Can work out Mon/Wed/Fri evenings
- Equipment: Home gym with dumbbells, barbell, bench, pull-up bar
- Injuries: None
- Diet: No restrictions, aiming for 2,200 kcal / 120g protein daily
```

---

## 7. Cron Jobs Setup

Cron jobs enable automated WhatsApp reminders -- Kai will check your data and send personalized messages at scheduled times (e.g., morning check-in, evening recap).

### 7.1 How Cron Scripts Work with Claude Code

The cron system uses a shell script (`cron/workout-reminder.sh`) that:

1. Runs `kai-cli.py quick-status` and `kai-cli.py last-workout` to get your current fitness data
2. Passes the data as a prompt to Claude Code using the `claude -p` flag
3. Claude reads the data, generates a personalized message, and sends it to your WhatsApp group via the plugin

The key command is:

```bash
claude -p --dangerously-skip-permissions \
  --dangerously-load-development-channels plugin:whatsapp@whatsapp-claude-plugin \
  "You are Kai, a fitness coach. Here is the user's data: ... Send a reminder to chat_id: YOUR_GROUP_ID"
```

**Breakdown of the flags:**

| Flag | Purpose |
|---|---|
| `-p` | Non-interactive "print" mode -- runs a single prompt and exits |
| `--dangerously-skip-permissions` | Skips the interactive permission prompts (required for unattended cron execution) |
| `--dangerously-load-development-channels` | Loads the WhatsApp channel plugin for this one-shot execution |

### 7.2 The `claude -p` Pattern

The `claude -p` pattern is the standard way to use Claude Code in scripts and automation:

```bash
# Basic pattern
claude -p "Your prompt here"

# With WhatsApp plugin for sending messages
claude -p --dangerously-skip-permissions \
  --dangerously-load-development-channels plugin:whatsapp@whatsapp-claude-plugin \
  "Send a message to chat_id 120363424405607157@g.us saying: Hello!"
```

This starts a fresh Claude Code session, processes the prompt, and exits. No interactive terminal required.

### 7.3 Setting Up Crontab

**Option A: Use the install script (recommended).**

```bash
cd ~/Desktop/ai-fitness-coach
./cron/install-cron.sh
```

This installs two entries:
- **10:00 AM** -- Morning reminder (sleep check, meal/workout nudge)
- **7:30 PM** -- Evening reminder (daily progress check)

**Option B: Manual crontab setup.**

```bash
# Open crontab editor
crontab -e

# Add these lines (adjust paths and times):
# AI Fitness Coach reminders
0 10 * * * KAI_DIR=/Users/yourusername/Desktop/ai-fitness-coach /Users/yourusername/Desktop/ai-fitness-coach/cron/workout-reminder.sh >> /Users/yourusername/Desktop/ai-fitness-coach/cron.log 2>&1
30 19 * * * KAI_DIR=/Users/yourusername/Desktop/ai-fitness-coach /Users/yourusername/Desktop/ai-fitness-coach/cron/workout-reminder.sh >> /Users/yourusername/Desktop/ai-fitness-coach/cron.log 2>&1
```

**Cron time format:** `minute hour * * *`
- `0 10 * * *` = every day at 10:00 AM
- `30 19 * * *` = every day at 7:30 PM
- `0 8 * * 1-5` = weekdays at 8:00 AM

### 7.4 Verifying Cron Jobs

```bash
# List installed cron jobs
crontab -l

# Check the log after a cron run
tail -20 ~/Desktop/ai-fitness-coach/cron.log

# Check if it ran today
grep "$(date +%Y-%m-%d)" ~/Desktop/ai-fitness-coach/cron.log
```

### 7.5 macOS Cron Permissions

On macOS, cron may not have permission to run commands. You need to grant it **Full Disk Access**:

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **Privacy & Security** > **Full Disk Access**
3. Click the `+` button
4. Navigate to `/usr/sbin/cron` and add it

If cron still does not work, try using `launchd` instead (see section 8.3).

### 7.6 Required .env Configuration

The cron script reads `KAI_WHATSAPP_CHAT_ID` from the `.env` file:

```bash
# In ~/Desktop/ai-fitness-coach/.env
KAI_WHATSAPP_CHAT_ID=120363424405607157@g.us
```

Without this variable, the cron script will exit with an error.

---

## 8. Running 24/7

### 8.1 Interactive Session (Manual)

For real-time WhatsApp conversations with Kai, you need Claude Code running with the WhatsApp channel:

```bash
cd ~/Desktop/ai-fitness-coach
claude --channels plugin:whatsapp@whatsapp-claude-plugin
```

This keeps Claude Code listening for incoming WhatsApp messages. When someone messages the group, Claude reads the group config, processes the message, and replies.

**However:** Closing the terminal or disconnecting from SSH kills the session. For persistent operation, use one of the methods below.

### 8.2 tmux / screen (Recommended for Interactive Sessions)

`tmux` or `screen` lets you run a terminal session that survives disconnections.

**Using tmux:**

```bash
# Install tmux (if not already installed)
# macOS: brew install tmux
# Ubuntu: sudo apt install tmux

# Create a new tmux session named "kai"
tmux new-session -s kai

# Inside the tmux session, start Claude Code
cd ~/Desktop/ai-fitness-coach
claude --channels plugin:whatsapp@whatsapp-claude-plugin

# Detach from tmux (session keeps running): press Ctrl+B, then D

# Re-attach later
tmux attach-session -t kai

# List running sessions
tmux list-sessions

# Kill the session when done
tmux kill-session -t kai
```

**Using screen:**

```bash
# Create a new screen session
screen -S kai

# Start Claude Code
cd ~/Desktop/ai-fitness-coach
claude --channels plugin:whatsapp@whatsapp-claude-plugin

# Detach: press Ctrl+A, then D

# Re-attach
screen -r kai
```

### 8.3 launchd (macOS -- Auto-Start on Boot)

On macOS, you can use `launchd` to automatically start the WhatsApp channel on boot.

Create a plist file at `~/Library/LaunchAgents/com.kai.whatsapp.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.kai.whatsapp</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/claude</string>
        <string>--channels</string>
        <string>plugin:whatsapp@whatsapp-claude-plugin</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yourusername/Desktop/ai-fitness-coach</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/yourusername/Desktop/ai-fitness-coach/launchd-out.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/yourusername/Desktop/ai-fitness-coach/launchd-err.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

Load it:

```bash
# Load (starts immediately and on boot)
launchctl load ~/Library/LaunchAgents/com.kai.whatsapp.plist

# Unload (stop)
launchctl unload ~/Library/LaunchAgents/com.kai.whatsapp.plist

# Check status
launchctl list | grep kai
```

> **Note:** Update the paths in the plist to match your actual username and Claude Code installation path. You can find the Claude binary path with `which claude`.

### 8.4 systemd (Linux -- Auto-Start on Boot)

On Linux servers, create a systemd service at `~/.config/systemd/user/kai-whatsapp.service`:

```ini
[Unit]
Description=AI Fitness Coach WhatsApp Channel
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/yourusername/ai-fitness-coach
ExecStart=/usr/bin/claude --channels plugin:whatsapp@whatsapp-claude-plugin
Restart=on-failure
RestartSec=30
Environment=PATH=/usr/local/bin:/usr/bin:/bin
Environment=HOME=/home/yourusername

[Install]
WantedBy=default.target
```

Enable and start:

```bash
# Reload systemd
systemctl --user daemon-reload

# Enable (start on boot)
systemctl --user enable kai-whatsapp

# Start now
systemctl --user start kai-whatsapp

# Check status
systemctl --user status kai-whatsapp

# View logs
journalctl --user -u kai-whatsapp -f
```

### 8.5 Auto-Restart on Crash

Both `launchd` (with `KeepAlive`) and `systemd` (with `Restart=on-failure`) automatically restart the process if it crashes. For tmux/screen, you can use a simple wrapper script:

```bash
#!/bin/bash
# restart-kai.sh -- Auto-restart loop
while true; do
    echo "[$(date)] Starting Claude Code..."
    cd ~/Desktop/ai-fitness-coach
    claude --channels plugin:whatsapp@whatsapp-claude-plugin
    echo "[$(date)] Claude Code exited. Restarting in 10 seconds..."
    sleep 10
done
```

### 8.6 Cron Jobs vs Interactive Sessions

**You do not need an interactive session running for cron jobs to work.** The cron script uses `claude -p` which starts a fresh one-shot session each time. The interactive session is only needed for:

- Real-time WhatsApp conversations (responding to messages as they arrive)
- Using the `/whatsapp:access` and `/whatsapp:setup` skills

If you only want automated reminders and do not need real-time chat, cron jobs alone are sufficient.

---

## 9. Troubleshooting

### 9.1 WhatsApp Connection Issues

**Problem: "Connection closed" or repeated disconnects.**

WhatsApp allows only one active connection per auth state. If you have two instances running, they will fight:

```bash
# Kill all WhatsApp plugin processes
pkill -f "bun.*whatsapp"

# Then restart Claude Code
claude --channels plugin:whatsapp@whatsapp-claude-plugin
```

**Problem: "Logged out" error.**

Your linked device was removed from WhatsApp. Re-pair:

```bash
# Inside Claude Code:
/whatsapp:configure reset-auth

# Then restart Claude Code and run setup again:
/whatsapp:setup
```

**Problem: QR code not appearing or "too many attempts".**

WhatsApp rate-limits pairing attempts. Wait 10-15 minutes, then try again. If QR rendering is poor in your terminal, use the pairing code method instead (tap "Link with phone number instead" in WhatsApp).

### 9.2 Permission Issues

**Problem: "Permission denied" when Claude tries to run kai-cli.py.**

Make sure the script is executable:
```bash
chmod +x ~/Desktop/ai-fitness-coach/src/kai-cli.py
```

**Problem: Claude Code asks for permission to run every Bash command.**

For automated operation, the WhatsApp plugin tools should be pre-approved in `~/.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__plugin_whatsapp_whatsapp__reply",
      "mcp__plugin_whatsapp_whatsapp__react",
      "mcp__plugin_whatsapp_whatsapp__download_attachment",
      "mcp__plugin_whatsapp_whatsapp__edit_message",
      "mcp__plugin_whatsapp_whatsapp__status"
    ]
  }
}
```

For Bash commands (like running kai-cli.py), you will need to approve them interactively or add specific patterns to the allow list.

### 9.3 Database Issues

**Problem: "No such table" or database errors.**

Re-initialize the database:
```bash
python3 ~/Desktop/ai-fitness-coach/src/db_manager.py ~/Desktop/ai-fitness-coach/data/kai_health.db
```

**Problem: Database file not found.**

Make sure the `data/` directory exists:
```bash
mkdir -p ~/Desktop/ai-fitness-coach/data
```

Check that `.env` has the correct path or is using the default.

### 9.4 Cron Jobs Not Firing

**Step 1: Verify cron entries exist.**
```bash
crontab -l
```

**Step 2: Check the log file.**
```bash
tail -30 ~/Desktop/ai-fitness-coach/cron.log
```

**Step 3: Run the script manually to see errors.**
```bash
KAI_DIR=~/Desktop/ai-fitness-coach ~/Desktop/ai-fitness-coach/cron/workout-reminder.sh
```

**Step 4: Check PATH.**

Cron runs with a minimal PATH. The `workout-reminder.sh` script adds common paths, but if `claude` or `python3` are installed in unusual locations, you may need to set the full path in the script or crontab.

**Step 5: macOS Full Disk Access.**

On macOS, cron needs Full Disk Access permissions. See section 7.5.

### 9.5 Messages Not Being Delivered

**Check 1: Is the group enabled?**
```bash
# Inside Claude Code:
/whatsapp:access
```

Verify your group ID appears under "groups".

**Check 2: Is `requireMention` blocking messages?**

If `requireMention` is `true`, the bot only responds when @mentioned. Set it to `false` for a dedicated fitness group:
```bash
/whatsapp:access group add YOUR_GROUP_ID@g.us --no-mention
```

**Check 3: Is the sender on the allowlist?**

For DMs, the sender must be on the allowlist or go through pairing.

**Check 4: Is `KAI_WHATSAPP_CHAT_ID` correct in `.env`?**

The chat ID must exactly match the group JID (e.g., `120363424405607157@g.us`).

### 9.6 Claude Code Not Finding the Group Config

If Claude responds but does not have the Kai personality or tool instructions:

1. Verify the config file exists at the correct path:
   ```bash
   ls ~/.claude/channels/whatsapp/groups/YOUR_GROUP_ID@g.us/config.md
   ```

2. Verify the file has content:
   ```bash
   cat ~/.claude/channels/whatsapp/groups/YOUR_GROUP_ID@g.us/config.md
   ```

3. The group ID in the directory name must exactly match the group JID.

### 9.7 Common Error Messages

| Error | Cause | Fix |
|---|---|---|
| `command not found: claude` | Claude Code not installed or not in PATH | `npm install -g @anthropic-ai/claude-code` |
| `command not found: bun` | Bun not installed | `curl -fsSL https://bun.sh/install \| bash` |
| `KAI_WHATSAPP_CHAT_ID is not set` | Missing from `.env` | Add the group ID to `.env` |
| `No such file or directory: kai-cli.py` | Wrong path in config.md | Update paths in the group config to use absolute paths |
| `440 disconnect` | Two WhatsApp sessions running simultaneously | Kill the extra process: `pkill -f "bun.*whatsapp"` |
| `database is locked` | Another process is writing to SQLite | Wait and retry; SQLite handles this automatically |

---

## Quick Reference

### File Locations Summary

| File | Path | Purpose |
|---|---|---|
| Claude settings | `~/.claude/settings.json` | Global Claude Code configuration |
| WhatsApp access | `~/.claude/channels/whatsapp/access.json` | Who can message the bot |
| WhatsApp auth | `~/.claude/channels/whatsapp/.baileys_auth/` | WhatsApp session credentials |
| Group config | `~/.claude/channels/whatsapp/groups/<id>/config.md` | Bot personality and tools for a group |
| Group memory | `~/.claude/channels/whatsapp/groups/<id>/memory.md` | Conversation history for a group |
| Project .env | `<project>/. env` | Project environment variables |
| User profile | `<project>/config/profile.json` | Fitness goals, nutrition targets, equipment |
| Database | `<project>/data/kai_health.db` | All logged fitness data |
| Cron log | `<project>/cron.log` | Output from automated reminders |

### Essential Commands

```bash
# Start Claude Code with WhatsApp
claude --channels plugin:whatsapp@whatsapp-claude-plugin

# Run the fitness CLI directly
python3 src/kai-cli.py quick-status
python3 src/kai-cli.py suggest-workout --duration 40
python3 src/kai-cli.py log-weight 70.5

# Manage WhatsApp access (inside Claude Code)
/whatsapp:access
/whatsapp:access group add GROUP_ID@g.us --no-mention
/whatsapp:access allow PHONE@s.whatsapp.net

# Check cron
crontab -l
tail -f cron.log
```
