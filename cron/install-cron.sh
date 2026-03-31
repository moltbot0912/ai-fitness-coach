#!/bin/bash
# install-cron.sh -- Install AI Fitness Coach cron jobs for automated reminders
#
# This script adds two cron entries:
#   - Morning reminder at 10:00 AM
#   - Evening reminder at 7:30 PM
#
# Run: ./cron/install-cron.sh

set -euo pipefail

KAI_DIR="$(cd "$(dirname "$0")/.." && pwd)"
REMINDER_SCRIPT="${KAI_DIR}/cron/workout-reminder.sh"
CRON_LOG="${KAI_DIR}/cron.log"

echo "AI Fitness Coach -- Cron Job Installer"
echo "================================="
echo ""
echo "Project directory: ${KAI_DIR}"
echo "Reminder script:   ${REMINDER_SCRIPT}"
echo "Log file:          ${CRON_LOG}"
echo ""

# Check that the reminder script exists and is executable
if [ ! -f "$REMINDER_SCRIPT" ]; then
    echo "Error: workout-reminder.sh not found at ${REMINDER_SCRIPT}"
    exit 1
fi
chmod +x "$REMINDER_SCRIPT"

# Check .env for required config
if [ ! -f "${KAI_DIR}/.env" ]; then
    echo "Warning: No .env file found. The cron job needs KAI_WHATSAPP_CHAT_ID."
    echo "Create .env from config/.env.example first."
    echo ""
fi

# Define cron entries
MORNING_CRON="0 10 * * * KAI_DIR=${KAI_DIR} ${REMINDER_SCRIPT} >> ${CRON_LOG} 2>&1"
EVENING_CRON="30 19 * * * KAI_DIR=${KAI_DIR} ${REMINDER_SCRIPT} >> ${CRON_LOG} 2>&1"

echo "The following cron jobs will be added:"
echo ""
echo "  Morning (10:00 AM): ${MORNING_CRON}"
echo "  Evening (7:30 PM):  ${EVENING_CRON}"
echo ""

read -p "Install these cron jobs? [y/N] " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Get existing crontab (suppress error if none exists)
    EXISTING_CRON=$(crontab -l 2>/dev/null || true)

    # Check if entries already exist
    if echo "$EXISTING_CRON" | grep -q "workout-reminder.sh"; then
        echo "AI Fitness Coach cron jobs already exist. Skipping to avoid duplicates."
        echo "To remove existing entries, run: crontab -e"
        exit 0
    fi

    # Append new entries
    (echo "$EXISTING_CRON"; echo ""; echo "# AI Fitness Coach reminders"; echo "$MORNING_CRON"; echo "$EVENING_CRON") | crontab -

    echo "Cron jobs installed successfully!"
    echo ""
    echo "To verify: crontab -l"
    echo "To remove: crontab -e  (and delete the AI Fitness Coach lines)"
    echo ""
    echo "Tip: Adjust the times by editing crontab -e"
    echo "  Cron format: minute hour * * *"
    echo "  Example: '0 8 * * *' = 8:00 AM daily"
else
    echo "Cancelled. No changes made."
fi
