# WSL2 Access Guide for QA Search Interface

## Quick Access URLs

Run this command to get current URLs:
```bash
./show_urls.sh
```

## Accessing from Windows Browser

### Method 1: Using localhost (Recommended)
```
Frontend: http://localhost:3000
Backend:  http://localhost:5000/api/health
```

**Pros:** Easy to remember, persists across WSL restarts
**Cons:** May require WSL2 networking to be properly configured

### Method 2: Using WSL IP Address
```bash
# Get your WSL IP
hostname -I
# Example: 172.22.213.193

# Then use:
Frontend: http://172.22.213.193:3000
Backend:  http://172.22.213.193:5000/api/health
```

**Pros:** Direct connection, bypasses localhost issues
**Cons:** IP changes on WSL restart

## Troubleshooting Connection Issues

### Issue: "Connection Refused" or "Connection Reset"

**Solution 1: Make sure services are listening on all interfaces**

Frontend should show:
```
➜  Network: http://172.22.213.193:3000/
```

Backend should show:
```
* Running on all addresses (0.0.0.0)
* Running on http://172.22.213.193:5000
```

**Solution 2: Check Windows Firewall**

1. Open Windows Defender Firewall
2. Click "Allow an app through firewall"
3. Look for "WSL" or "vEthernet (WSL)"
4. Ensure both Private and Public are checked

**Solution 3: Restart WSL networking**

From Windows PowerShell (as Administrator):
```powershell
wsl --shutdown
```
Then restart your WSL terminal.

**Solution 4: Port forwarding (if nothing else works)**

From Windows PowerShell (as Administrator):
```powershell
# Forward port 3000
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=172.22.213.193

# Forward port 5000
netsh interface portproxy add v4tov4 listenport=5000 listenaddress=0.0.0.0 connectport=5000 connectaddress=172.22.213.193
```

To remove port forwarding later:
```powershell
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0
netsh interface portproxy delete v4tov4 listenport=5000 listenaddress=0.0.0.0
```

To view all port proxies:
```powershell
netsh interface portproxy show all
```

## Testing Connectivity

### From WSL (should always work):
```bash
curl http://localhost:3000
curl http://localhost:5000/api/health
```

### From Windows PowerShell:
```powershell
# Test localhost
curl http://localhost:3000
curl http://localhost:5000/api/health

# Test WSL IP
curl http://172.22.213.193:3000
curl http://172.22.213.193:5000/api/health
```

## Configuration Files

### Frontend: vite.config.js
```javascript
server: {
  host: '0.0.0.0',  // Listen on all interfaces
  port: 3000,
  // ...
}
```

### Backend: backend/config.py
```python
HOST = os.getenv("HOST", "0.0.0.0")  # Listen on all interfaces
PORT = int(os.getenv("PORT", "5000"))
```

## Common WSL2 Networking Issues

### Symptom: localhost works from WSL but not from Windows

**Cause:** WSL2 uses a virtualized network adapter

**Solution:** Use WSL IP address instead of localhost, or set up port forwarding

### Symptom: IP address changes every time WSL restarts

**Cause:** WSL2 uses dynamic IP assignment

**Solution:**
- Use localhost (with proper configuration)
- Or set up static IP in .wslconfig

### Symptom: Can't connect to backend from frontend

**Cause:** Backend not listening on 0.0.0.0

**Solution:** Ensure `HOST=0.0.0.0` in .env file

## .wslconfig for Better Networking (Optional)

Create/edit `C:\Users\YourUsername\.wslconfig`:

```ini
[wsl2]
# Enable localhost forwarding
localhostForwarding=true

# Network settings
networkingMode=mirrored
firewall=false

# Optional: Set memory limit
memory=4GB
```

After creating/editing, restart WSL:
```powershell
wsl --shutdown
```

## Quick Verification Script

Save as `test_access.sh`:
```bash
#!/bin/bash
WSL_IP=$(hostname -I | awk '{print $1}')

echo "Testing connectivity..."
echo ""

echo "1. Testing frontend (localhost):"
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000 || echo "Failed"

echo ""
echo "2. Testing frontend (WSL IP):"
curl -s -o /dev/null -w "%{http_code}\n" http://$WSL_IP:3000 || echo "Failed"

echo ""
echo "3. Testing backend (localhost):"
curl -s http://localhost:5000/api/health | grep -q "healthy" && echo "Success" || echo "Failed"

echo ""
echo "4. Testing backend (WSL IP):"
curl -s http://$WSL_IP:5000/api/health | grep -q "healthy" && echo "Success" || echo "Failed"

echo ""
echo "Access URLs:"
echo "  Frontend: http://localhost:3000 or http://$WSL_IP:3000"
echo "  Backend:  http://localhost:5000 or http://$WSL_IP:5000"
```

Run with:
```bash
chmod +x test_access.sh
./test_access.sh
```

## Still Not Working?

1. Check if services are actually running:
   ```bash
   # Check frontend
   curl http://localhost:3000

   # Check backend
   curl http://localhost:5000/api/health
   ```

2. Check if ports are listening:
   ```bash
   netstat -tlnp | grep -E '3000|5000'
   ```

3. Check WSL version:
   ```bash
   wsl --version
   ```

4. Update WSL to latest version:
   ```powershell
   wsl --update
   ```

5. Try accessing from Windows using the actual WSL IP

6. As a last resort, use Docker (which has better networking)

## Summary

**Easiest method:** Use `http://localhost:3000` after ensuring:
1. Frontend has `host: '0.0.0.0'` in vite.config.js
2. Backend has `HOST=0.0.0.0` in .env
3. WSL2 localhost forwarding is enabled

**Most reliable method:** Use WSL IP address directly (get it with `hostname -I`)

**Production method:** Use Docker with port mapping (already configured in docker-compose.yml)
