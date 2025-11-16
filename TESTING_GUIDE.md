# DupeFinder Authentication Testing Guide

## 🎉 Phase A Complete - JWT + OTP Authentication Ready!

The backend authentication system with email OTP verification is fully implemented and ready to test through the frontend!

---

## 🚀 How to Start the Application

### Step 1: Start the Backend Server

Open a terminal in the `backend` folder and run:

```bash
cd backend/app
python main.py
```

**Expected Output:**
```
============================================================
DupeFinder API Server
============================================================

Starting server...
Docs: http://localhost:8000/api/docs
API:  http://localhost:8000/api
...
```

The backend API will be running at: **http://localhost:8000**

---

### Step 2: Start the Frontend Server

Open a **NEW terminal** in the `frontend-app` folder and run:

```bash
cd frontend-app
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

The frontend will be running at: **http://localhost:5173**

---

## 🧪 Testing the Authentication Flow

### 1. Open the Frontend

Go to: **http://localhost:5173**

You'll see the DupeFinder homepage with **Login** and **Sign Up** buttons in the top right.

---

### 2. Test Signup with OTP Verification

1. **Click "Sign Up"**
2. **Fill in the form:**
   - Email: Your real email address (you'll receive the OTP here)
   - Password: Must be at least 8 characters with:
     - Uppercase letter
     - Lowercase letter
     - Digit
     - Example: `TestPass123!`
   - Confirm Password: Same as above

3. **Click "Sign Up"**
   - You'll see a success message: "Account created successfully. Please check your email..."
   - The page will switch to **OTP Verification** step

4. **Check Your Email**
   - From: ussamainayat@gmail.com
   - Subject: "DupeFinder - Email Verification Code"
   - Look for the 6-digit OTP code (also check spam folder!)

5. **Enter the 6-Digit OTP**
   - Type or paste the OTP code
   - Click "Verify OTP"
   - If correct: Success message → Auto-redirects to login page
   - If wrong/expired: Error message → Click "Resend OTP" to get a new one

---

### 3. Test Login

1. **Enter your email and password**
2. **Click "Login"**
3. **Success!** You're logged in and can now:
   - Upload images to search for similar products
   - Access the dashboard (button appears in top right)

---

### 4. Test Login Before Verification (Should Fail)

Try logging in with an account that hasn't verified the OTP:
- You'll see: "Email not verified. Please verify your email first."

---

## 🎯 What Works Now

✅ **Signup with OTP**
- Email validation
- Password strength check
- OTP sent via Gmail SMTP
- OTP expires in 10 minutes
- Auto-stores in MongoDB

✅ **OTP Verification**
- 6-digit code validation
- Expiry checking
- One-time use (can't reuse same OTP)
- Resend OTP functionality

✅ **Login**
- Email/password validation
- Checks if email is verified
- Returns JWT access token (30 min) + refresh token (7 days)
- Updates last login timestamp

✅ **Protected Routes**
- Image search requires authentication
- JWT Bearer token validation
- User info from token

✅ **Session Management**
- Tokens stored in localStorage
- Auto-logout on token expiry
- Refresh token mechanism

---

## 📧 Email Configuration

**Sender**: ussamainayat@gmail.com  
**OTP Expiry**: 10 minutes  
**Email Template**: Black & white styled HTML

---

## 🐛 Troubleshooting

### Backend not starting?
```bash
cd backend
pip install -r requirements.txt
python -m backend.app.main
```

### Frontend not starting?
```bash
cd frontend-app
npm install
npm run dev
```

### Not receiving OTP emails?
1. Check spam folder
2. Verify Gmail SMTP settings are correct
3. Check backend console for email sending logs
4. Try "Resend OTP" button

### Login not working?
1. Make sure you verified the OTP first
2. Check password (case-sensitive)
3. Look at browser console (F12) for errors

---

## 📱 Test Accounts

You can create multiple test accounts with different emails:
- Each email needs its own OTP verification
- OTP codes are unique per signup
- Accounts remain in MongoDB database

---

## 🎨 UI Features

- **Two-step signup**: Email/Password → OTP Verification
- **Success/Error messages**: Green for success, red for errors
- **Loading states**: Buttons show "Loading..." during API calls
- **Auto-redirect**: After OTP verification, auto-redirects to login after 2 seconds
- **OTP input**: Large, centered 6-digit input field
- **Resend OTP**: Button with cooldown to prevent spam

---

## 🔍 Testing Checklist

- [ ] Signup with valid email and password
- [ ] Receive OTP email within 30 seconds
- [ ] Verify OTP successfully
- [ ] Try wrong OTP (should show error)
- [ ] Try expired OTP after 10+ minutes (should show error)
- [ ] Resend OTP (should receive new code)
- [ ] Login with verified account (should succeed)
- [ ] Try login before verification (should fail)
- [ ] Try login with wrong password (should fail)
- [ ] Upload image after login (should work)
- [ ] Logout and try to upload (should prompt login)

---

## 🎉 Ready to Test!

1. Start backend: `cd backend/app && python main.py`
2. Start frontend: `cd frontend-app && npm run dev`
3. Open browser: http://localhost:5173
4. Click "Sign Up" and follow the flow!

**Note**: Both servers must be running simultaneously for the full experience.

---

## 📊 What's Next

After you test Phase A (Authentication), we'll continue with:
- **Phase B**: Admin Dashboard Backend (14 tasks)
- **Phase C**: Frontend Auth UI enhancements
- **Phase D**: Admin Dashboard Frontend
- **Phase E**: Black & White Theme
- **Phase F**: Integration Testing

---

**Happy Testing! 🚀**






