# Quick Start Guide - DupeFinder

## 🚀 How to Start Both Servers

### Option 1: Using Two Terminals (Recommended)

#### Terminal 1 - Backend
```bash
cd backend
python start_server.py
```

Wait until you see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Backend is now running at: **http://localhost:8000**

---

#### Terminal 2 - Frontend
```bash
cd frontend-app
npm run dev
```

Wait until you see:
```
  VITE ready in xxx ms
  ➜  Local:   http://localhost:5173/
```

Frontend is now running at: **http://localhost:5173**

---

### Option 2: PowerShell One-Liners

**Start Backend:**
```powershell
cd C:\Users\ab887\Desktop\dupefinder\backend; python start_server.py
```

**Start Frontend (in new terminal):**
```powershell
cd C:\Users\ab887\Desktop\dupefinder\frontend-app; npm run dev
```

---

## ✅ Verify Servers Are Running

**Backend Check:**
```powershell
curl http://localhost:8000/health
```

**Frontend Check:**
Open browser to: http://localhost:5173

---

## 🎯 Testing Authentication

Once both servers are running:

1. **Open**: http://localhost:5173
2. **Click**: "Sign Up" (top right)
3. **Enter**: 
   - Your real email
   - Password: TestPass123! (or similar)
4. **Check email** for 6-digit OTP
5. **Enter OTP** and verify
6. **Login** with credentials
7. **Upload image** to test!

---

## 🐛 Common Issues

### "ModuleNotFoundError: No module named 'app'"
**Solution**: Don't run from `backend/app`, run from `backend` folder:
```bash
cd backend
python start_server.py
```

### "npm error Missing script: dev"
**Solution**: Make sure you're in the `frontend-app` folder:
```bash
cd frontend-app
npm run dev
```

### Backend won't start
**Solution**: Install dependencies first:
```bash
cd backend
pip install -r requirements.txt
python start_server.py
```

### Frontend won't start
**Solution**: Install dependencies first:
```bash
cd frontend-app
npm install
npm run dev
```

---

## 📋 Quick Checklist

- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 5173
- [ ] Can access http://localhost:5173 in browser
- [ ] Can see Login/Signup buttons
- [ ] MongoDB is running (needed for backend)

---

## 🎉 You're Ready!

Open your browser to **http://localhost:5173** and start testing!






