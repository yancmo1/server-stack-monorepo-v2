# 🔄 QUICK RESTORE COMMANDS

If the 5K Tracker breaks, use these commands to restore the working version:

## Method 1: Git Restore (Recommended)
```bash
cd /Users/yancyshepherd/MEGA/PythonProjects/YANCY
git checkout 8e0655b -- WORKING_APP_BACKUP_app.py
cp WORKING_APP_BACKUP_app.py apps/5k-tracker-pwa/app.py
./scripts/deploy_pwa_tracker.sh
```

## Method 2: Docker Image Restore
```bash
ssh yancmo@ubuntumac
cd ~/apps/server-stack-monorepo-v2/deploy
docker tag ed455f8fb9836f5ca081d234350a8979e7b4c956f4a6b2e4310a3d11d79cfa2a deploy-pwa-tracker
docker compose up -d tracker
```

## Method 3: Full Git Reset
```bash
cd ~/apps/server-stack-monorepo-v2
git checkout f932236 -- apps/5k-tracker-pwa/app.py
cd deploy && docker compose build --no-cache tracker && docker compose up -d tracker
```

## Test After Restore
```bash
curl -s https://yancmo.xyz/tracker/ | grep "Race Tracker"
curl -s https://yancmo.xyz/tracker/manifest.json | grep "name"
```

**Working Commit**: f932236 (app deployed)
**Backup Commit**: 8e0655b (backup files)
**Docker Image**: ed455f8fb9836f5ca081d234350a8979e7b4c956f4a6b2e4310a3d11d79cfa2a
