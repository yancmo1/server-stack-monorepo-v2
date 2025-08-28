# Cloudflare DNS Configuration Guide

## Server Details
- **Server Public IP**: `136.228.117.217`
- **Domain**: `yancmo.xyz`
- **DNS Provider**: Cloudflare

## Required DNS Records

### Step-by-Step Cloudflare Setup

1. **Login to Cloudflare Dashboard**
   - Go to https://dash.cloudflare.com/
   - Select your domain: `yancmo.xyz`
   - Click on "DNS" in the left sidebar

2. **Add A Records for All Subdomains**
   Create the following A records (all pointing to `136.228.117.217`):

### Application Subdomains (Port-based services)
| Name | Type | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| `dashboard` | A | `136.228.117.217` | Proxied (☁️) | Auto |
| `cruise` | A | `136.228.117.217` | Proxied (☁️) | Auto |
| `clashmap` | A | `136.228.117.217` | Proxied (☁️) | Auto |
| `qsl` | A | `136.228.117.217` | Proxied (☁️) | Auto |
| `crumb` | A | `136.228.117.217` | Proxied (☁️) | Auto |
| `tracker` | A | `136.228.117.217` | Proxied (☁️) | Auto |
| `connector` | A | `136.228.117.217` | Proxied (☁️) | Auto |

### Administrative Subdomains (Monitoring services)
| Name | Type | Content | Proxy Status | TTL |
|------|------|---------|--------------|-----|
| `grafana` | A | `136.228.117.217` | DNS Only (☁️ OFF) | Auto |
| `metrics` | A | `136.228.117.217` | DNS Only (☁️ OFF) | Auto |

## Detailed Instructions

### For Each Record:
1. Click "Add Record" button
2. **Type**: Select "A"
3. **Name**: Enter subdomain name (e.g., "dashboard")
4. **IPv4 address**: Enter `136.228.117.217`
5. **Proxy status**: 
   - **Proxied (☁️)** for app subdomains (dashboard, cruise, clashmap, qsl, crumb, tracker, connector)
   - **DNS Only (☁️ OFF)** for admin subdomains (grafana, metrics)
6. **TTL**: Leave as "Auto"
7. Click "Save"

### Why Different Proxy Settings?

**App Subdomains (Proxied ☁️):**
- Gets Cloudflare's DDoS protection
- SSL/TLS handled by Cloudflare
- Traffic filtering and rate limiting
- Analytics and insights
- Better for public-facing applications

**Admin Subdomains (DNS Only):**
- Direct connection to your server
- Better for monitoring tools (Grafana, Prometheus)
- Avoids potential proxy interference with admin interfaces
- Still gets SSL via your Let's Encrypt certificates

## Verification Commands

Once you've added all records, verify DNS propagation:

```bash
# Test DNS resolution for each subdomain
nslookup dashboard.yancmo.xyz
nslookup cruise.yancmo.xyz
nslookup clashmap.yancmo.xyz
nslookup qsl.yancmo.xyz
nslookup crumb.yancmo.xyz
nslookup tracker.yancmo.xyz
nslookup connector.yancmo.xyz
nslookup grafana.yancmo.xyz
nslookup metrics.yancmo.xyz
nslookup pwa.yancmo.xyz
nslookup connector.yancmo.xyz
nslookup grafana.yancmo.xyz
nslookup metrics.yancmo.xyz

# Or use dig for more detailed info
dig +short dashboard.yancmo.xyz
dig +short grafana.yancmo.xyz
```

## Expected DNS Propagation Time
- **Cloudflare**: Usually instant to 5 minutes
- **Global propagation**: Up to 24 hours (typically 1-2 hours)
- **TTL**: Auto (typically 300 seconds = 5 minutes)

## Security Considerations

### Cloudflare Proxy Benefits (☁️ ON):
- ✅ Hides your server's real IP address
- ✅ DDoS protection and rate limiting
- ✅ Web Application Firewall (WAF)
- ✅ SSL/TLS termination at edge
- ✅ Caching for static content
- ✅ Analytics and security insights

### DNS Only Benefits (☁️ OFF):
- ✅ Direct connection (lower latency)
- ✅ No proxy interference with applications
- ✅ Better for SSH, custom protocols
- ✅ Full control over SSL certificates
- ✅ Easier troubleshooting

## Post-DNS Setup Checklist

Once DNS records are active:

1. **Test DNS resolution** (commands above)
2. **Install SSL certificates** with certbot
3. **Deploy Nginx configurations**
4. **Update Docker port bindings**
5. **Apply firewall restrictions**

## Troubleshooting

### If records don't resolve:
```bash
# Check Cloudflare's DNS servers directly
dig @1.1.1.1 dashboard.yancmo.xyz
dig @1.0.0.1 grafana.yancmo.xyz

# Clear local DNS cache
sudo systemctl restart systemd-resolved  # Ubuntu
# or
sudo service network-manager restart
```

### Common Issues:
- **"Too many redirects"**: Check proxy status, may need DNS Only
- **SSL errors**: Wait for Let's Encrypt after Nginx deployment
- **504 Gateway Timeout**: Service not running on expected port
- **Connection refused**: Firewall blocking access

---

## Quick Action Summary

**Immediate Steps:**
1. Go to Cloudflare DNS dashboard
2. Add 9 A records (all pointing to `136.228.117.217`)
3. Set proxy status as specified above
4. Wait 5-10 minutes for DNS propagation
5. Test with `nslookup` or `dig` commands

**After DNS is Active:**
- Ready to run SSL certificate installation
- Ready to deploy Nginx reverse proxy configs
- Ready to secure Docker port bindings