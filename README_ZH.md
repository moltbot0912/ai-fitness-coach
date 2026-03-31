# AI Fitness Coach

**AI 驅動的 WhatsApp 健身教練** -- 運動追蹤、營養記錄、智慧建議。

Kai 是一個住在你 WhatsApp 群組裡的個人健身代理。它追蹤你的運動、營養、睡眠和體重，然後用這些數據給你智慧的運動建議、督促你保持規律，並透過 cron 排程發送個人化的提醒訊息。

基於 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 與 WhatsApp 頻道外掛建構。

## 功能特色

- **運動追蹤** -- 記錄訓練部位、時長、地點和動作
- **智慧運動建議** -- AI 根據你最近沒練到的肌群自動推薦動作，並根據睡眠數據調整訓練強度
- **漸進式超負荷追蹤** -- 記錄每個動作的重量/組數/次數，查看力量趨勢
- **營養記錄** -- 追蹤每餐的卡路里、蛋白質、碳水化合物、脂肪
- **體重追蹤** -- 每日體重記錄，查看趨勢
- **睡眠追蹤** -- 記錄睡眠時間與品質，影響運動強度建議
- **週計劃** -- 智慧重排程，顯示哪些肌群已經過期
- **自動提醒** -- 透過 Cron 排程的 WhatsApp 訊息，檢查你的數據後發送情境感知的提醒
- **動作資料庫** -- 70+ 個動作，按肌群和器材分類

## 快速開始（5 分鐘）

### 先決條件

- **Python 3.8+**（只使用標準函式庫，不需要安裝套件）
- **Claude Code** CLI（[安裝指南](https://docs.anthropic.com/en/docs/claude-code/getting-started)）
- Claude Code 的 **WhatsApp 頻道外掛**（用於 WhatsApp 整合）

### 安裝

```bash
# 複製專案
git clone https://github.com/moltbot0912/ai-fitness-coach.git
cd ai-fitness-coach

# 執行設定腳本
chmod +x setup.sh
./setup.sh
```

設定腳本會：
1. 檢查 Python 版本
2. 從範本建立設定檔
3. 初始化 SQLite 資料庫
4. 引導你自訂個人檔案
5. 選擇性安裝 cron 排程

### 手動設定

```bash
# 1. 複製設定範本
cp config/.env.example .env
cp config/profile.example.json config/profile.json

# 2. 編輯你的個人檔案
nano config/profile.json  # 設定姓名、目標、健身器材等

# 3. 初始化資料庫
python3 src/db_manager.py data/kai_health.db

# 4. 測試
python3 src/kai-cli.py quick-status
```

## CLI 指令

### 記錄數據

```bash
# 記錄一餐
python3 src/kai-cli.py log-food "雞胸肉飯" 550 45 60 12

# 記錄體重
python3 src/kai-cli.py log-weight 70.5

# 記錄運動
python3 src/kai-cli.py log-workout "健身房" "胸" 40 "臥推、啞鈴飛鳥、伏地挺身"

# 記錄睡眠
python3 src/kai-cli.py log-sleep 2025-01-15 23:30 07:00 7.5 --quality good

# 記錄單一動作（漸進式超負荷追蹤）
python3 src/kai-cli.py log-exercise "Bench Press" "Chest" 135 3 10 --rpe 8
```

### 查詢數據

```bash
# 快速狀態總覽
python3 src/kai-cli.py quick-status

# 今日營養
python3 src/kai-cli.py daily-summary

# 過去 7 天總覽
python3 src/kai-cli.py weekly-summary

# 體重趨勢
python3 src/kai-cli.py weight-trend

# 睡眠歷史
python3 src/kai-cli.py sleep-trend

# 上次運動詳情
python3 src/kai-cli.py last-workout
```

### 智慧功能

```bash
# 取得運動建議（自動選擇你最近沒練的肌群）
python3 src/kai-cli.py suggest-workout

# 指定時長或重點
python3 src/kai-cli.py suggest-workout --duration 30 --focus chest

# 週計劃與補課建議
python3 src/kai-cli.py weekly-plan

# 所有動作的力量趨勢
python3 src/kai-cli.py strength-trend

# 特定動作的力量趨勢
python3 src/kai-cli.py strength-trend "Bench Press"
```

## 部署選項

### 方案 A：本機電腦（需要常開機器）

適合有一台 Mac/Linux 機器持續運行的情況。

1. 依照上方快速開始操作
2. 安裝 cron 排程：`./cron/install-cron.sh`
3. 保持機器開著，cron 提醒才會觸發

### 方案 B：雲端 VM（每月 $3-5 美元）

更穩定可靠。詳見 [docs/AWS_SETUP.md](docs/AWS_SETUP.md)。

**簡要步驟：**
1. 開一個 AWS Lightsail 或 EC2 t3.micro（或任何 $5/月的 VPS）
2. 安裝 Python 3、Claude Code 和 WhatsApp 外掛
3. Clone 這個 repo 並執行 `setup.sh`
4. 安裝 cron 排程
5. 完成 -- 即使你的筆電關機，提醒也會 24/7 運行

## 設定

### 個人檔案（`config/profile.json`）

你的健身檔案控制運動建議、營養目標和可用器材。

重要欄位：
- `user_name` -- 你的名字（用在提醒訊息中）
- `fitness_goals.primary_goal` -- 影響組數/次數建議
- `nutrition_targets` -- 每日卡路里和巨量營養素目標
- `workout_preferences.frequency_per_week` -- 目標運動頻率（如 "3-4"）
- `workout_preferences.gym_locations` -- 你的器材（決定建議哪些動作）
- `workout_preferences.preferred_muscle_group_rotation` -- 要輪替的肌群

### 環境變數（`.env`）

| 變數 | 預設值 | 說明 |
|---|---|---|
| `KAI_DB_PATH` | `data/kai_health.db` | SQLite 資料庫位置 |
| `KAI_PROFILE_PATH` | `config/profile.json` | 個人檔案位置 |
| `KAI_EXERCISES_PATH` | `src/exercises.md` | 動作資料庫位置 |
| `KAI_TIMEZONE` | （系統預設） | 你的時區 |
| `KAI_WHATSAPP_CHAT_ID` | （無） | WhatsApp 群組 ID |

## 授權

MIT License。詳見 [LICENSE](LICENSE)。
