# MongoDB Installation Guide for Windows

Complete guide to install and configure MongoDB Community Edition on Windows for DupeFinder project.

---

## 📥 Method 1: Direct Download (Recommended)

### Step 1: Download MongoDB

1. Go to: https://www.mongodb.com/try/download/community
2. Select:
   - **Version**: 7.0.14 (or latest 7.x)
   - **Platform**: Windows
   - **Package**: MSI
3. Click **Download**

### Step 2: Install MongoDB

1. **Run the installer** (mongodb-windows-x86_64-7.0.14-signed.msi)
2. Click **Next** on welcome screen
3. Accept license agreement → **Next**
4. Choose **Complete** installation
5. **Important**: On "Service Configuration" screen:
   - ✅ Check "Install MongoDB as a Service"
   - ✅ Check "Run service as Network Service user"
   - Leave default data and log directories
   - Click **Next**
6. **MongoDB Compass**: Uncheck if you don't need the GUI (optional)
7. Click **Install**
8. Click **Finish**

### Step 3: Verify Installation

Open PowerShell **as Administrator**:

```powershell
# Check if MongoDB service is running
Get-Service MongoDB

# Should show:
# Status   Name               DisplayName
# ------   ----               -----------
# Running  MongoDB            MongoDB Server
```

Test MongoDB connection:

```powershell
# Navigate to MongoDB bin directory
cd "C:\Program Files\MongoDB\Server\7.0\bin"

# Run MongoDB shell
.\mongosh

# You should see:
# Current Mongosh Log ID: ...
# Connecting to: mongodb://127.0.0.1:27017/?directConnection=true
# Using MongoDB: 7.0.14
# test>
```

Type `exit` to close the shell.

---

## 📥 Method 2: Using Chocolatey

### Step 1: Install Chocolatey

Open PowerShell **as Administrator** and run:

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

### Step 2: Install MongoDB

```powershell
choco install mongodb -y
```

### Step 3: Start MongoDB Service

```powershell
net start MongoDB
```

---

## ⚙️ Configuration

### Default Settings

- **Port**: 27017
- **Data Directory**: `C:\Program Files\MongoDB\Server\7.0\data`
- **Log Directory**: `C:\Program Files\MongoDB\Server\7.0\log`
- **Config File**: `C:\Program Files\MongoDB\Server\7.0\bin\mongod.cfg`

### Connection String

```
mongodb://localhost:27017/
```

---

## 🧪 Test MongoDB Connection from Python

Create a test file `test_mongodb.py`:

```python
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Test connection
try:
    client.admin.command('ping')
    print("[OK] Successfully connected to MongoDB!")
    
    # List databases
    print("\nAvailable databases:")
    for db_name in client.list_database_names():
        print(f"  - {db_name}")
    
except Exception as e:
    print(f"[ERROR] Connection failed: {e}")
```

Run it:
```bash
python test_mongodb.py
```

Expected output:
```
[OK] Successfully connected to MongoDB!

Available databases:
  - admin
  - config
  - local
```

---

## 🛠️ Common Commands

### Service Management (PowerShell as Admin)

```powershell
# Start MongoDB service
net start MongoDB

# Stop MongoDB service
net stop MongoDB

# Restart MongoDB service
net stop MongoDB && net start MongoDB

# Check service status
Get-Service MongoDB
```

### MongoDB Shell Commands

```bash
# Connect to MongoDB
mongosh

# Show all databases
show dbs

# Use a database
use dupefinder

# Show collections in current database
show collections

# Count documents in collection
db.products.countDocuments()

# Find all products
db.products.find()

# Find products in a category
db.products.find({ category: "bags" })

# Exit shell
exit
```

---

## 🐛 Troubleshooting

### Issue 1: "MongoDB service won't start"

**Solution:**
1. Open Services (Win + R → `services.msc`)
2. Find "MongoDB Server"
3. Right-click → **Start**

If it fails:
1. Check log file: `C:\Program Files\MongoDB\Server\7.0\log\mongod.log`
2. Look for errors
3. Common fix: Delete `C:\Program Files\MongoDB\Server\7.0\data\mongod.lock`
4. Restart service

### Issue 2: "Access Denied" during installation

**Solution:**
- Right-click installer → **Run as Administrator**
- Or install using Chocolatey (Method 2)

### Issue 3: "mongosh not recognized"

**Solution:**
Add MongoDB to PATH:
1. Open Environment Variables
2. Edit System PATH
3. Add: `C:\Program Files\MongoDB\Server\7.0\bin`
4. Restart terminal

### Issue 4: "pymongo module not found"

**Solution:**
```bash
pip install pymongo
```

### Issue 5: Port 27017 already in use

**Solution:**
Check what's using the port:
```powershell
netstat -ano | findstr :27017
```

Kill the process or change MongoDB port in `mongod.cfg`:
```yaml
net:
  port: 27018  # Use different port
```

---

## 🔒 Security (Optional for Local Development)

For production, enable authentication:

1. Create admin user:
```javascript
use admin
db.createUser({
  user: "admin",
  pwd: "your_password",
  roles: ["root"]
})
```

2. Enable authentication in `mongod.cfg`:
```yaml
security:
  authorization: enabled
```

3. Update connection string:
```
mongodb://admin:your_password@localhost:27017/
```

**Note**: Not needed for local development/40% milestone.

---

## 📚 Useful Resources

- **Official Docs**: https://www.mongodb.com/docs/manual/
- **Download Page**: https://www.mongodb.com/try/download/community
- **MongoDB Compass** (GUI): https://www.mongodb.com/products/compass
- **PyMongo Docs**: https://pymongo.readthedocs.io/

---

## ✅ Verification Checklist

After installation, verify:

- [ ] MongoDB service is running
- [ ] Can connect via `mongosh`
- [ ] Python can connect (test_mongodb.py passes)
- [ ] Port 27017 is accessible
- [ ] No firewall blocks
- [ ] Ready to run `backend/init_mongodb.py`

---

## 🚀 Next Steps

Once MongoDB is installed and running:

1. Navigate to project root
2. Run database initialization:
   ```bash
   python backend/init_mongodb.py
   ```
3. Start FastAPI backend:
   ```bash
   python backend/app/main.py
   ```

---

**Last Updated**: November 9, 2025  
**For DupeFinder FYP Project**








