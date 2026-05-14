# ANPR System — Windows Deployment Guide

## Overview

This guide covers deploying the ANPR backend and frontend as persistent Windows services using Windows Task Scheduler. No Docker or Linux is required.

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Windows 10 / Server 2019+ | 64-bit |
| Python 3.11 (x64) | Added to PATH |
| Node.js 20 LTS | Added to PATH |
| Git (optional) | For cloning / pulling updates |

## Step 1: Clone or download the project

```bat
git clone https://github.com/your-org/anpr-system.git C:\anpr
cd C:\anpr
```

## Step 2: Configure environment variables

Copy `.env.example` to `.env` inside the `backend\` directory and fill in all values:

```bat
copy backend\.env.example backend\.env
notepad backend\.env
```

Key settings for Windows / Karsun deployment:

```env
DATABASE_URL=sqlite+aiosqlite:///./anpr.db
CORS_ALLOW_ALL_ORIGINS=true
APP_ENV=production
KARSUN_IP=http://192.168.1.100        # camera LAN IP
KARSUN_USERNAME=admin
KARSUN_PASSWORD=your-camera-password
```

## Step 3: Install Python dependencies

```bat
cd C:\anpr\backend
pip install -r requirements.txt
pip install pyinstaller
```

## Step 4: Build the backend executable

```bat
cd C:\anpr
scripts\build-windows.bat
```

Output: `backend\dist\anpr-backend.exe`

## Step 5: Build the frontend

```bat
cd C:\anpr\frontend
npm install
npm run build
```

Output: `frontend\build\index.js`

## Step 6: Verify manual start

```bat
cd C:\anpr
scripts\start.bat
```

Open `http://localhost` in a browser. Log in with the admin credentials from `.env`.

## Step 7: Register as a startup task in Windows Task Scheduler

1. Open **Task Scheduler** (`taskschd.msc`)
2. Click **Create Task** (not Basic Task)
3. **General** tab:
   - Name: `ANPR System`
   - Select **Run whether user is logged on or not**
   - Check **Run with highest privileges**
   - Configure for: **Windows 10** (or your OS version)
4. **Triggers** tab → New:
   - Begin the task: **At startup**
   - Delay: `30 seconds` (optional, allows network to initialise)
5. **Actions** tab → New:
   - Action: **Start a program**
   - Program/script: `C:\anpr\scripts\start.bat`
   - Start in: `C:\anpr`
6. **Conditions** tab:
   - Uncheck **Start the task only if the computer is on AC power**
7. **Settings** tab:
   - Check **If the task is already running, do not start a new instance**
8. Click **OK** and enter the Windows service account password when prompted.

## Step 8: Set a static IP address on the Windows server

1. Open **Network and Sharing Center** → change adapter settings
2. Right-click the active adapter → **Properties**
3. Select **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**
4. Select **Use the following IP address** and fill in:
   - IP address: e.g. `192.168.1.10`
   - Subnet mask: `255.255.255.0`
   - Default gateway: your router IP
   - Preferred DNS: `8.8.8.8`
5. Click **OK**

Configure the camera to push HTTP events to `http://192.168.1.10:8000/api/webhook/camera`.

## Updating the application

1. Stop the Task Scheduler task (or reboot will be needed after update)
2. Pull latest code: `git pull`
3. Rebuild: `scripts\build-windows.bat` and `cd frontend && npm run build`
4. Restart the Task Scheduler task (or reboot)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 80 already in use | Set `PORT=8080` in `start.bat` and update camera config |
| Backend won't start | Check `backend\logs\app.log` for errors |
| Camera not syncing | Verify `KARSUN_IP` is reachable: `ping 192.168.1.100` |
| DB locked error | Ensure only one instance of `anpr-backend.exe` is running |
