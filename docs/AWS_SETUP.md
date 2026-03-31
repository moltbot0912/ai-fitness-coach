# AWS / Cloud VM Deployment Guide

Run AI Fitness Coach 24/7 on a cloud VM for about $0-5/month. This ensures your automated WhatsApp reminders fire reliably even when your laptop is off.

---

## Cost Breakdown

Before choosing a provider, here is what it costs:

### Compute (the VM itself)

| Provider | Plan | Monthly Cost | Specs |
|---|---|---|---|
| **Oracle Cloud** | Always Free ARM | **$0.00** | 1 OCPU, 1 GB RAM (free forever) |
| AWS Lightsail | 512 MB / 1 vCPU | $3.50 | Smallest Lightsail instance |
| Vultr | Cloud Compute | $3.50 | 1 vCPU, 512 MB RAM |
| DigitalOcean | Basic Droplet | $4.00 | 1 vCPU, 512 MB RAM |
| Hetzner | CX22 | EUR 3.29 | 2 vCPU, 4 GB RAM (best value) |

### Additional Costs

| Item | Cost | Notes |
|---|---|---|
| Claude Code API usage | Variable | Depends on your Anthropic plan; cron reminders use ~2 API calls/day |
| Storage | Included | SQLite database is tiny (< 1 MB for years of data) |
| Bandwidth | Included | Minimal bandwidth usage |
| Domain name | Not needed | No web server required |

**Bottom line**: The cheapest option is Oracle Cloud's Always Free tier ($0/month). The most straightforward option is AWS Lightsail at $3.50/month.

---

## Option 1: AWS Lightsail (Recommended for Simplicity)

### 1. Create Instance

1. Go to [AWS Lightsail](https://lightsail.aws.amazon.com/)
2. Click "Create instance"
3. Choose **Linux/Unix** > **OS Only** > **Ubuntu 22.04 LTS**
4. Select the **$3.50/month** plan (512 MB RAM, 1 vCPU)
5. Name it `ai-fitness-coach` and create

### 2. Connect via SSH

```bash
# From the Lightsail console, click "Connect using SSH"
# Or use your own terminal:
ssh -i your-key.pem ubuntu@your-instance-ip
```

### 3. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3
sudo apt install -y python3 python3-pip

# Install Node.js (required for Claude Code)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude Code
npm install -g @anthropic-ai/claude-code

# Authenticate Claude Code
claude auth login
```

### 4. Install AI Fitness Coach

```bash
git clone https://github.com/moltbot0912/ai-fitness-coach.git
cd ai-fitness-coach
chmod +x setup.sh
./setup.sh
```

### 5. Configure WhatsApp

1. Set up the WhatsApp channel plugin for Claude Code
2. Pair your WhatsApp device
3. Set `KAI_WHATSAPP_CHAT_ID` in `.env`

### 6. Install Cron Jobs

```bash
./cron/install-cron.sh
```

### 7. Verify

```bash
# Check cron is set up
crontab -l

# Run a test
python3 src/kai-cli.py quick-status

# Check logs after a cron run
tail -f cron.log
```

---

## Option 2: Oracle Cloud Free Tier ($0/month)

Oracle Cloud offers an "Always Free" ARM instance that never expires. This is the cheapest option.

### 1. Create an Account

1. Go to [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
2. Sign up for an account (requires a credit card for verification but you will not be charged)
3. Select a home region close to you

### 2. Create a Free VM

1. Go to **Compute > Instances > Create Instance**
2. Choose:
   - **Image**: Canonical Ubuntu 22.04 (aarch64)
   - **Shape**: VM.Standard.A1.Flex (Ampere ARM)
   - **OCPU count**: 1
   - **Memory**: 1 GB (minimum)
3. Add your SSH key
4. Click **Create**

### 3. Connect and Install

```bash
ssh -i your-key.pem ubuntu@your-instance-ip

# Update and install dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip

# Install Node.js (ARM64 version)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude Code
npm install -g @anthropic-ai/claude-code
claude auth login

# Clone and set up AI Fitness Coach
git clone https://github.com/moltbot0912/ai-fitness-coach.git
cd ai-fitness-coach
chmod +x setup.sh
./setup.sh

# Install cron jobs
./cron/install-cron.sh
```

> **Note**: Oracle's ARM instances use the `aarch64` architecture. All the tools used by AI Fitness Coach (Python, Node.js, SQLite) work on ARM without issues.

---

## Option 3: DigitalOcean Droplet ($4/month)

### 1. Create a Droplet

1. Go to [DigitalOcean](https://www.digitalocean.com/)
2. Click **Create > Droplets**
3. Choose **Ubuntu 22.04 LTS**, **Basic plan**, **$4/month** (1 vCPU, 512 MB)
4. Choose a datacenter region close to you
5. Add your SSH key and create

### 2. Connect and Install

```bash
ssh root@your-droplet-ip

# Create a non-root user (recommended)
adduser kai
usermod -aG sudo kai
su - kai

# Follow the same installation steps as AWS Lightsail (Step 3 onwards)
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
npm install -g @anthropic-ai/claude-code
claude auth login

git clone https://github.com/moltbot0912/ai-fitness-coach.git
cd ai-fitness-coach
chmod +x setup.sh
./setup.sh
./cron/install-cron.sh
```

---

## Option 4: Docker Deployment

If you prefer containers, you can run AI Fitness Coach in Docker. This works on any machine with Docker installed (local, cloud, NAS, etc.).

### Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

# Install Node.js for Claude Code
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Claude Code
RUN npm install -g @anthropic-ai/claude-code

# Set up the application
WORKDIR /app
COPY . /app/

# Create data directory
RUN mkdir -p /app/data

# Initialize database
RUN python3 src/db_manager.py /app/data/kai_health.db

# Install cron
RUN apt-get update && apt-get install -y cron && apt-get clean

# Default command: start cron and keep container running
CMD ["bash", "-c", "cron && tail -f /dev/null"]
```

### Docker Compose

Create a `docker-compose.yml`:

```yaml
version: '3.8'
services:
  ai-fitness-coach:
    build: .
    volumes:
      - ./data:/app/data          # Persist database
      - ./config:/app/config      # Persist configuration
      - ./.env:/app/.env          # Environment variables
    restart: unless-stopped
```

### Build and Run

```bash
# Build and start
docker compose up -d

# Run CLI commands inside the container
docker compose exec ai-fitness-coach python3 src/kai-cli.py quick-status
docker compose exec ai-fitness-coach python3 src/kai-cli.py suggest-workout

# View logs
docker compose logs -f
```

> **Note**: For Docker deployment, you will need to handle Claude Code authentication inside the container. Mount your Claude credentials or set the API key as an environment variable.

---

## Tips

### Keep It Running

The VM's cron daemon runs automatically. No need for screen/tmux for the cron jobs.

If you want to interact with Kai directly via SSH:
```bash
cd ai-fitness-coach
python3 src/kai-cli.py suggest-workout
```

### Data Backup

Your data lives in `data/kai_health.db`. Back it up periodically:

```bash
# Simple manual backup
cp data/kai_health.db data/kai_health.db.backup

# Set up a daily backup cron (runs at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * cp /home/ubuntu/ai-fitness-coach/data/kai_health.db /home/ubuntu/ai-fitness-coach/data/kai_health.db.\$(date +\%Y\%m\%d).backup") | crontab -
```

To back up to a remote location:
```bash
# Copy to your local machine
scp ubuntu@your-instance-ip:~/ai-fitness-coach/data/kai_health.db ./backup/

# Or sync to S3 (AWS only)
aws s3 cp data/kai_health.db s3://your-bucket/backups/kai_health.db
```

### Monitoring and Alerting

#### Basic Monitoring

Check that cron jobs are running:
```bash
# View recent log entries
tail -20 cron.log

# Check if cron ran today
grep "$(date +%Y-%m-%d)" cron.log

# Check cron status
systemctl status cron
```

#### Simple Health Check Script

Create a script that checks if the system is working:

```bash
#!/bin/bash
# health-check.sh -- Check that AI Fitness Coach is operational

KAI_DIR="${KAI_DIR:-$HOME/ai-fitness-coach}"

echo "=== AI Fitness Coach Health Check ==="
echo "Date: $(date)"
echo ""

# Check database exists
if [ -f "${KAI_DIR}/data/kai_health.db" ]; then
    DB_SIZE=$(du -h "${KAI_DIR}/data/kai_health.db" | cut -f1)
    echo "[OK] Database exists (${DB_SIZE})"
else
    echo "[FAIL] Database not found!"
fi

# Check CLI works
if python3 "${KAI_DIR}/src/kai-cli.py" quick-status > /dev/null 2>&1; then
    echo "[OK] CLI is working"
else
    echo "[FAIL] CLI error!"
fi

# Check cron jobs are installed
if crontab -l 2>/dev/null | grep -q "workout-reminder"; then
    echo "[OK] Cron jobs installed"
else
    echo "[WARN] Cron jobs not installed"
fi

# Check last cron run
if [ -f "${KAI_DIR}/cron.log" ]; then
    LAST_RUN=$(tail -1 "${KAI_DIR}/cron.log" | head -c 19)
    echo "[INFO] Last cron log entry: ${LAST_RUN}"
else
    echo "[INFO] No cron log found yet"
fi

echo ""
echo "=== Done ==="
```

#### Uptime Monitoring (Optional)

For external uptime monitoring, you can use free services:

- **UptimeRobot** (free, 50 monitors): Set up a cron job that pings a UptimeRobot heartbeat URL
- **Healthchecks.io** (free, 20 monitors): Add a curl to your cron job to report success

Example with Healthchecks.io:
```bash
# Add to the end of workout-reminder.sh
curl -fsS --retry 3 https://hc-ping.com/your-unique-uuid > /dev/null
```

### Updating

```bash
cd ai-fitness-coach
git pull
# Your data and config files are in .gitignore, so they won't be overwritten
```

### Security Tips

- **SSH keys only**: Disable password authentication in `/etc/ssh/sshd_config`
- **Firewall**: Only open port 22 (SSH). AI Fitness Coach does not need any inbound ports
- **Updates**: Run `sudo apt update && sudo apt upgrade` periodically
- **API keys**: Never commit `.env` to git (it is already in `.gitignore`)
