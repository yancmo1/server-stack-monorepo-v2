# URL Migration Summary for VS Code Workspaces

## 📋 Copy-Paste Command Ready!

**File Location**: `server-audit/workspace-migration/PASTE_THIS_COMMAND.txt`

Just copy the entire contents of that file and paste it into any other VS Code workspace chat to automatically update all URL references.

## 🔄 Migration Mapping Overview:

### Port-Based → Subdomain Migration:
```
OLD: http(s)://yancmo.xyz:5550     → NEW: https://dashboard.yancmo.xyz
OLD: http(s)://yancmo.xyz:5551     → NEW: https://cruise.yancmo.xyz  
OLD: http(s)://yancmo.xyz:5552     → NEW: https://clashmap.yancmo.xyz
OLD: http(s)://yancmo.xyz:5553     → NEW: https://qsl.yancmo.xyz
OLD: http(s)://yancmo.xyz:5554     → NEW: https://crumb.yancmo.xyz (NEW APP)
OLD: http(s)://yancmo.xyz:5555     → NEW: https://tracker.yancmo.xyz
OLD: http(s)://yancmo.xyz:5557     → NEW: https://connector.yancmo.xyz
OLD: http(s)://yancmo.xyz:9090     → NEW: https://metrics.yancmo.xyz
OLD: http(s)://yancmo.xyz:3000     → NEW: https://grafana.yancmo.xyz
```

### App Name Changes:
- `clanmap` → `clashmap`
- `pwa` → `tracker`

### IP Address References:
- Any `136.228.117.217:PORT` → corresponding `https://subdomain.yancmo.xyz`

## 🎯 What the Command Will Do:

1. **Search** all file types: .html, .js, .json, .md, .env, .yml, etc.
2. **Find** all port-based URL references 
3. **Replace** with HTTPS subdomain equivalents
4. **Update** app name references (clanmap→clashmap, pwa→tracker)
5. **Report** what files were changed
6. **Preserve** localhost and 127.0.0.1 references (for development)

## 📁 Common Files That Will Need Updates:

- **Configuration**: `.env`, `config.json`, `package.json`
- **Documentation**: `README.md`, docs files
- **Code**: API endpoints, hardcoded URLs
- **Manifests**: PWA manifest files
- **Docker**: `docker-compose.yml` (if cross-referencing services)

## 🚨 Important Notes:

- **Backup First**: The agent will show changes before applying
- **Review Changes**: Check the summary before confirming 
- **Test After**: Verify functionality with new URLs
- **Development URLs**: localhost:PORT references will be preserved

## 🔧 Manual Verification Commands:
After migration, run these to check for missed references:
```bash
grep -r ":5550\|:5551\|:5552\|:5553\|:5554\|:5555\|:5557\|:9090\|:3000" .
grep -r "clanmap" .
grep -r "136.228.117.217" .
```

---

**Ready to use**: Just paste the command from `PASTE_THIS_COMMAND.txt` into any workspace!