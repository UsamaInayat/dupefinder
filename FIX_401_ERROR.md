# Fix 401 Unauthorized Errors - Step by Step

## The Problem
You're getting 401 errors because:
1. The admin token is missing or invalid
2. You need to log out and log back in to get a fresh token

## Quick Fix (2 minutes)

### Step 1: Clear Browser Storage
1. Open browser console (Press `F12`)
2. Go to **Console** tab
3. Type this and press Enter:
   ```javascript
   localStorage.clear()
   ```
4. You should see: `undefined`

### Step 2: Refresh the Page
- Press `F5` or `Ctrl+R` to refresh

### Step 3: Log In as Admin
1. You should see the login page
2. Click **"Admin Login"** button (at the bottom)
3. Enter:
   - Email: `admin@dupefinder.com`
   - Password: `admin123`
4. Click **"Login"**

### Step 4: Verify Token is Stored
1. Open browser console (F12)
2. Type:
   ```javascript
   localStorage.getItem('adminToken')
   ```
3. You should see a long token string (starts with `eyJ...`)

### Step 5: Test the Admin Dashboard
- Go to **Auto Sync** module
- You should see brands loading (no 401 errors)

## Alternative: Use Token Checker Tool

I've created a helper tool for you:

1. Open this file in your browser:
   ```
   file:///C:/Users/ab887/Desktop/dupefinder/check_admin_token.html
   ```
   Or just double-click `check_admin_token.html` in File Explorer

2. Click **"Test Admin Login"** button
   - This will automatically log you in and store the token

3. Then refresh your admin dashboard page

## Why This Happens

The admin authentication system stores tokens in `localStorage` with the key `adminToken`. If you:
- Logged in before the code was updated
- Have an old/invalid token
- Never logged in as admin

You'll get 401 errors. The solution is to clear storage and log in fresh.

## Verify It's Working

After logging in, check the browser console:
- ✅ No 401 errors
- ✅ Brands load in Auto Sync
- ✅ Products load in Product Catalogue
- ✅ No CORS errors

## If Still Not Working

1. **Check backend is running:**
   - Backend terminal should show: `INFO:     Uvicorn running on http://127.0.0.1:8000`

2. **Check backend logs:**
   - Look for error messages when you try to access admin pages
   - Share the error message if you see one

3. **Verify admin account exists:**
   ```powershell
   cd backend
   python create_admin.py
   ```
   (Type "yes" if it asks to reset password)

4. **Test admin login directly:**
   - Open: `http://localhost:8000/api/docs`
   - Try the `/api/admin/login` endpoint
   - Use: `admin@dupefinder.com` / `admin123`



