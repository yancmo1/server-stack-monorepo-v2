# 🚢 How to Start & Access Your Cruise Price Tracker

You now have **3 different ways** to access your improved cruise price tracker:

## 🌐 Option 1: New Web Interface (Recommended)

**Start the modern web app:**
```bash
cd cruise-price-check
python3 start_web_app.py
```

**Then open in your browser:**
- **Local access:** http://localhost:5000
- **From other devices:** http://YOUR-IP:5000 (replace YOUR-IP with your Mac's IP)

**Features:**
- ✅ Beautiful modern interface
- ✅ Real-time price checking
- ✅ Price history with charts
- ✅ Statistics dashboard
- ✅ Mobile-friendly design

---

## 💻 Option 2: Command Line Interface

**Single price check:**
```bash
python3 improved_price_tracker.py --check
```

**Continuous monitoring (every 6 hours):**
```bash
python3 improved_price_tracker.py --monitor
```

**View price history:**
```bash
python3 improved_price_tracker.py --history 30
```

**Features:**
- ✅ Perfect for automation
- ✅ Can run in background
- ✅ Logs to cruise_price_tracker.log
- ✅ Great for cron jobs

---

## 🔧 Option 3: Original Web App (Legacy)

**Start the original Flask app:**
```bash
python3 app.py
```

**Access at:**
- http://localhost:5002 (if SSL certificates available)
- May require SSL setup

**Note:** This is your original system with the complex navigation that often breaks.

---

## 🎯 Recommended Quick Start

1. **Start the new web interface:**
   ```bash
   cd cruise-price-check
   python3 start_web_app.py
   ```

2. **Open your browser to:** http://localhost:5000

3. **Click "Check Price Now"** to test the system

4. **View the results** - should show $1,462 for all rate combinations

---

## 📱 Access from Phone/Tablet

1. **Find your Mac's IP address:**
   ```bash
   ifconfig | grep "inet " | grep -v 127.0.0.1
   ```

2. **Start the web app:**
   ```bash
   python3 start_web_app.py
   ```

3. **On your phone, go to:** http://YOUR-MAC-IP:5000

---

## 🔄 For 24/7 Monitoring

**Option A: Leave terminal open**
```bash
python3 improved_price_tracker.py --monitor
```

**Option B: Background process**
```bash
nohup python3 improved_price_tracker.py --monitor > monitor.log 2>&1 &
```

**Option C: Cron job (check every 6 hours)**
```bash
# Add to crontab: crontab -e
0 */6 * * * cd /path/to/cruise-price-check && python3 improved_price_tracker.py --check
```

---

## 📧 Enable Email Alerts

1. **Edit cruise_config.json:**
   ```json
   {
     "alerts": {
       "email_enabled": true,
       "email_from": "your-gmail@gmail.com",
       "email_to": "your-email@gmail.com",
       "email_password": "your-app-password"
     }
   }
   ```

2. **For Gmail, get an App Password:**
   - Go to Google Account settings
   - Enable 2-Factor Authentication
   - Generate App Password for "Mail"
   - Use that password in the config

---

## 🎉 What You'll See

**Successful price check shows:**
```json
{
  "check_time": "2025-06-30T15:31:07",
  "results": [
    {
      "rate_code": "PJS",
      "meta_code": "IS", 
      "price": 1462.0,
      "success": true
    }
  ],
  "baseline_price": 1462
}
```

**Price drop alert example:**
```
🚨 CRUISE PRICE DROP ALERT! 🚨

Your cruise price has dropped by $75!

Original price: $1,462
New price: $1,387
Savings: $75

Book now at: https://www.carnival.com/booking/...
```

---

## 🛠️ Troubleshooting

**If web interface won't start:**
```bash
# Check if port 5000 is in use
lsof -i :5000
# Use different port if needed
python3 start_web_app.py --port 5001
```

**If price checks fail:**
```bash
# Check the logs
tail -f cruise_price_tracker.log
```

**If Chrome driver issues:**
```bash
# Update webdriver
pip3 install --upgrade webdriver-manager
```

---

## 🚀 Ready to Go!

Your improved cruise price tracker is **much more reliable** than the old system because it:

- ✅ **Bypasses complex navigation** - goes directly to booking URLs
- ✅ **Actually works** - just proved it can extract $1,462 prices
- ✅ **Tracks changes** - stores history and sends alerts
- ✅ **Handles errors** - automatic retries and logging
- ✅ **Modern interface** - beautiful web dashboard

**Start with:** `python3 start_web_app.py` and open http://localhost:5000

Happy cruise price tracking! 🚢