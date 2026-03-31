#!/bin/bash
# workout-reminder.sh -- AI Fitness Coach automated reminder via WhatsApp
#
# This script fetches your current fitness status and sends a personalized
# reminder to your WhatsApp group using Claude Code's WhatsApp channel plugin.
#
# Prerequisites:
#   - Claude Code CLI installed and authenticated
#   - WhatsApp channel plugin configured
#   - KAI_DIR environment variable set (or edit the path below)
#
# Usage:
#   ./workout-reminder.sh              # Use defaults
#   KAI_DIR=/path/to/ai-fitness-coach ./workout-reminder.sh  # Custom path
#
# Cron example (10 AM and 7:30 PM daily):
#   0 10 * * * /path/to/ai-fitness-coach/cron/workout-reminder.sh >> /tmp/kai-cron.log 2>&1
#   30 19 * * * /path/to/ai-fitness-coach/cron/workout-reminder.sh >> /tmp/kai-cron.log 2>&1

set -euo pipefail

# --- Configuration ---
KAI_DIR="${KAI_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
KAI_CLI="${KAI_DIR}/src/kai-cli.py"

# Load .env if present
if [ -f "${KAI_DIR}/.env" ]; then
    set -a
    source "${KAI_DIR}/.env"
    set +a
fi

CHAT_ID="${KAI_WHATSAPP_CHAT_ID:-}"
TIMEZONE="${KAI_TIMEZONE:-}"

if [ -z "$CHAT_ID" ]; then
    echo "Error: KAI_WHATSAPP_CHAT_ID is not set. Set it in .env or as an environment variable."
    exit 1
fi

# Ensure PATH includes common tool locations
export PATH="$HOME/.bun/bin:$HOME/local/node/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

# --- Fetch current status ---
STATUS=$(python3 "${KAI_CLI}" quick-status 2>&1)
LAST_WORKOUT=$(python3 "${KAI_CLI}" last-workout 2>&1)

# --- Send personalized reminder via Claude ---
claude -p --dangerously-skip-permissions \
  --dangerously-load-development-channels plugin:whatsapp@whatsapp-claude-plugin \
  "You are Kai, a fitness coach and accountability partner.

Here is the user's current health/fitness data (from the database):

--- quick-status ---
${STATUS}

--- last-workout ---
${LAST_WORKOUT}
---

Send a personalized reminder to the workout group (chat_id: ${CHAT_ID}) using the WhatsApp reply tool.

Rules:
1. Use a friendly, encouraging tone with emojis
2. Make decisions based on the data:
   - If 2+ days without exercise, gently remind them to get moving
   - If they already worked out today, encourage them and remind about nutrition/protein
   - If calorie or protein intake is low, remind about eating enough
   - If they've been consistent lately, give positive reinforcement
   - If Latest weight date is not today, remind them to weigh in
   - In the morning, ask about last night's sleep
3. Keep the message short (3-5 sentences), natural, not robotic
4. If everything looks good (worked out, ate well), just send a short motivational message
5. Don't list raw data numbers; weave observations naturally into the message" \
  2>&1 >> "${KAI_DIR}/cron.log"
