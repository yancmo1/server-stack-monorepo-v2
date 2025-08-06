# Discord Bot Development Workflow

## 🎯 Simplified Workflow (Production-Only Bot)

Discord bot development is done **directly on production** to avoid conflicts and complexity.

### Why Production-Only?
- ✅ No token conflicts
- ✅ No command sync issues  
- ✅ No environment complexity
- ✅ No Discord API rate limits from multiple instances
- ✅ Easier debugging

### Development Process

1. **Make Code Changes Locally**
   ```bash
   # Edit files in apps/coc-discord-bot/
   vim apps/coc-discord-bot/cogs/cwl_notifications.py
   ```

2. **Deploy Bot to Production**
   ```bash
   ./deploy.sh bot "Updated notification logic"
   ```

3. **Test Commands in Discord**
   - Use `/cwl_test` to verify bot is working
   - Use `/test_cwl_notification` to test functionality
   - Use owner commands for advanced testing

4. **Check Logs if Issues**
   ```bash
   ssh yancmo@ubuntumac "docker logs deploy-coc-discord-bot-1 --tail 20"
   ```

5. **Sync Commands if Needed**
   ```bash
   ./scripts/sync_discord_commands.sh
   ```

### Quick Commands Reference

```bash
# Deploy bot only
./deploy.sh bot

# Check bot status  
./deploy.sh status

# Sync commands manually
./scripts/sync_discord_commands.sh

# View bot logs
ssh yancmo@ubuntumac "docker logs deploy-coc-discord-bot-1 --tail 50"
```

### Available Discord Commands

**Public Commands:**
- `/cwl_test` - Quick test
- `/test_cwl_notification` - Send test notification

**Owner Commands:** (Discord ID: 311659929834487810)
- `/sync_cwl_commands` - Re-sync commands  
- `/reset_cwl_cache` - Clear notification cache
- `/quick_sync` - Quick sync
- `/force_sync` - Global sync

### Development Environment

**Local development excludes Discord bot** to prevent conflicts:
```bash
./dev.sh start    # Starts all services EXCEPT Discord bot
```

All Discord bot work happens on production server for reliability.
