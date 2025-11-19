# Fix CORS and 500 Error - Quick Guide

## Problem
- CORS error: "No 'Access-Control-Allow-Origin' header is present"
- 500 Internal Server Error on admin login

## Solution

### Step 1: Restart Backend Server

**IMPORTANT:** The backend server MUST be restarted after code changes!

1. **Stop the backend server:**
   - Go to the terminal where backend is running
   - Press `Ctrl+C` to stop it

2. **Start it again:**
   ```powershell
   cd C:\Users\ab887\Desktop\dupefinder\backend
   python start_server.py
   ```

3. **Verify it's running:**
   You should see:
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete.
   ```

### Step 2: Verify Backend is Accessible

Open a browser and go to:
```
http://localhost:8000/
```

You should see:
```json
{
  "message": "DupeFinder API - Affordable Alternatives for Luxury Wearables",
  "version": "0.1.0",
  "status": "active"
}
```

### Step 3: Test Admin Login

1. **Refresh your frontend page** (http://localhost:3000)
2. **Click "Admin Login"**
3. **Use credentials:**
   - Email: `admin@dupefinder.com`
   - Password: `admin123`

### Step 4: Check Backend Logs

If it still doesn't work, check the backend terminal for error messages. Common issues:

- **Database not connected:** Make sure MongoDB is running
- **Import errors:** Should be fixed now, but restart if you see import errors
- **Port already in use:** Make sure port 8000 is not used by another app

## What Was Fixed

1. ✅ Fixed import paths in `admin.py` (changed `backend.app` to `app`)
2. ✅ CORS configuration already includes `localhost:3000`
3. ✅ Admin login endpoint should work after restart

## If Still Not Working

1. **Check MongoDB is running:**
   ```powershell
   # On Windows
   net start MongoDB
   ```

2. **Check backend logs** for specific error messages

3. **Verify admin account exists:**
   ```powershell
   cd backend
   python create_admin.py
   ```
   (Type "yes" if it asks to reset password)

4. **Test backend directly:**
   ```powershell
   curl http://localhost:8000/
   ```

## Expected Behavior After Fix

- ✅ No CORS errors in browser console
- ✅ Admin login works
- ✅ Redirects to admin dashboard
- ✅ Can access scraping module



