# Bot Deployment Status

## Latest Deployment
- **Date**: July 18, 2025
- **Status**: Attempting automated deployment to server
- **Workflow**: Deploy Bot to Server (Self-Hosted)

## Deployment Method
The bot is now deployed using GitHub Actions with a self-hosted runner that runs directly on your server.

When changes are pushed to the main branch affecting the `coc-discord-bot/` directory, the deployment workflow automatically:
1. Generates .env file from GitHub secrets
2. Stops existing containers
3. Builds and starts new containers
4. Runs health checks
5. Verifies bot is online

## Manual Deployment
You can also trigger deployment manually from GitHub Actions or use the deploy script:
```bash
./deploy_to_ubuntumac.sh
```
# Deployment attempt Fri Jul 18 03:26:48 PM UTC 2025
