#!/bin/bash
# backup_to_meganz.sh
# Nightly backup script for coc-stack-monorepo
# Archives and uploads /home to MEGA, prunes old backups, and sends notification

# Set variables
BACKUP_SRC="/home"
BACKUP_NAME="home-backup-$(date +'%Y%m%d_%H%M%S').tar.gz"
BACKUP_TMP="/tmp/$BACKUP_NAME"
MEGA_FOLDER="/UBUNTU-MAC"
LOG_FILE="$HOME/backup_meganz.log"

# Create compressed archive (exclude __pycache__, .git, node_modules, and tmp files)
tar --exclude='*/__pycache__' --exclude='.git' --exclude='node_modules' --exclude='*.pyc' -czf "$BACKUP_TMP" -C "$BACKUP_SRC" . | tee -a "$LOG_FILE"

# Upload to MEGA UBUNTU-MAC folder using MEGAcmd batch mode
EMAIL="yancmo@gmail.com"
PASSWORD="88vbH4699V82S8"
echo -e "login $EMAIL $PASSWORD\nput $BACKUP_TMP $MEGA_FOLDER\nexit" | /usr/bin/mega-cmd | tee -a "$LOG_FILE"

# Remove local temp backup
rm -f "$BACKUP_TMP"

# Prune old backups (keep only 5 most recent in MEGA UBUNTU-MAC)
echo -e "login $EMAIL $PASSWORD\nls $MEGA_FOLDER\nexit" | /usr/bin/mega-cmd > /tmp/mega_ls.txt
FILE_LIST=$(grep 'coc-backup-' /tmp/mega_ls.txt | sort -r | awk 'NR>5 {print $NF}')
for file in $FILE_LIST; do
    echo -e "login $EMAIL $PASSWORD\nrm $MEGA_FOLDER/$file\nexit" | /usr/bin/mega-cmd | tee -a "$LOG_FILE"
    sleep 1
    # Sleep to avoid overwhelming MEGA server
done

# Send email notification (requires send_backup_log_test_email.py)
PYTHON_VENV="$HOME/scripts/venv/bin/python"
EMAIL_SCRIPT="$HOME/scripts/send_backup_log_test_email.py"
if [ -x "$PYTHON_VENV" ] && [ -f "$EMAIL_SCRIPT" ]; then
    "$PYTHON_VENV" "$EMAIL_SCRIPT" "$LOG_FILE"
else
    echo "Email notification script or Python venv not found!"
fi

echo "Backup complete." | tee -a "$LOG_FILE"
