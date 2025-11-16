# Admin Dashboard Testing Guide

## Quick Start

Make sure both servers are running:

### Backend (Terminal 1):
```bash
cd C:\Users\ab887\Desktop\dupefinder\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Terminal 2):
```bash
cd C:\Users\ab887\Desktop\dupefinder\frontend-app
npm run dev
```

Then open: **http://localhost:3001**

---

## Testing Each Module

### 1. Login & Access Dashboard

**Steps:**
1. Open http://localhost:3001
2. You should see the **Login page** (black & white theme)
3. Login with your registered account
4. You should be redirected to **Admin Dashboard**
5. You should see the **sidebar on the left** with 5 menu items

**Success Criteria:**
- ✅ Login page appears first (not the image upload page)
- ✅ Black & white theme everywhere
- ✅ After login, Admin Dashboard opens
- ✅ Sidebar shows: Overview, User Management, Product Catalogue, ML Training, Auto Sync

---

### 2. Overview Page (Default Landing)

**Steps:**
1. After login, you should land on **Overview**
2. Check if you see:
   - Welcome message
   - 4 stat cards (Users, Products, ML Status, Sync Status)
   - Quick action buttons at the bottom

**What to Check:**
- ✅ Page loads without errors
- ✅ Stats show "0" for users/products (since backend APIs aren't implemented yet)
- ✅ "Active" status for ML Model
- ✅ "Ready" status for Sync
- ✅ NO EMOJIS anywhere
- ✅ All black and white colors
- ✅ Quick action buttons are visible

**Console Logs:**
- You might see: "Users endpoint not ready yet"
- You might see: "Products endpoint not ready yet"
- This is NORMAL - backend endpoints aren't implemented yet

---

### 3. User Management Page

**Steps:**
1. Click **"User Management"** in the sidebar (second item, with ● icon)
2. Page should change to User Management module

**What to Check:**
- ✅ Module title: "User Management"
- ✅ Search bar at the top
- ✅ Filter buttons: All, Active, Inactive
- ✅ Table headers: Email, Status, Verified, Created, Last Login, Actions
- ✅ "Loading users..." or empty table (backend not ready)
- ✅ Pagination controls at bottom
- ✅ NO EMOJIS

**Console Errors:**
- You'll see API error (404 or network error) - this is EXPECTED
- Backend endpoint `/api/admin/users` is not implemented yet

---

### 4. Product Catalogue Page

**Steps:**
1. Click **"Product Catalogue"** in the sidebar (third item, with ▪ icon)
2. Page should change to Product Catalogue module

**What to Check:**
- ✅ Module title: "Product Catalogue Management"
- ✅ Three sections visible:
  1. **Import Products from CSV** - file upload button
  2. **Image Link Cleanup** - "Check Broken Links" button
  3. **Categories** - empty list (backend not ready)
  4. **Products** - table with filters
- ✅ CSV upload form shows file selector
- ✅ Filter dropdown for categories
- ✅ Checkbox for "Broken Links Only"
- ✅ NO EMOJIS

**Console Errors:**
- API errors expected - backend not ready

---

### 5. ML Training Page

**Steps:**
1. Click **"ML Training"** in the sidebar (fourth item, with ▸ icon)
2. Page should change to ML Training module

**What to Check:**
- ✅ Module title: "ML Model Training Dashboard"
- ✅ **Training Configuration** section with:
  - Slider for Train/Test Split (50% to 95%)
  - Percentage display (e.g., "80% train / 20% test")
  - "Start Training" button
- ✅ **Training History & Metrics** section
- ✅ Message: "No training history yet. Start your first training!"
- ✅ Slider is interactive (drag it and see percentage change)
- ✅ NO EMOJIS

**Test the Slider:**
- Drag the slider left/right
- Numbers should update: "XX% train / XX% test"
- Range: 50% minimum to 95% maximum

---

### 6. Auto Sync / Rescraping Page

**Steps:**
1. Click **"Auto Sync"** in the sidebar (fifth item, with ○ icon)
2. Page should change to Auto Sync module

**What to Check:**
- ✅ Module title: "Auto Sync / Rescraping"
- ✅ **Select Brands to Rescrape** section
- ✅ Empty brand grid (backend not ready)
- ✅ "0 brand(s) selected" message
- ✅ "Start Scraping" button (disabled - gray)
- ✅ **Scraping History** section
- ✅ Message: "No scraping history yet."
- ✅ NO EMOJIS

---

## Visual Checklist for ALL Pages

### Color Theme
- [ ] Everything is black (#000), white (#fff), or gray shades
- [ ] NO colors like blue, red, green, purple
- [ ] NO emojis (removed all of them)

### Sidebar
- [ ] Fixed on the left side
- [ ] Shows "DupeFinder Admin" logo at top
- [ ] 5 menu items with simple icons (■, ●, ▪, ▸, ○)
- [ ] Active page has WHITE background
- [ ] Inactive pages have gray text
- [ ] Logout button at bottom

### Layout
- [ ] Main content area on the right
- [ ] Page title at the top
- [ ] White content cards with black borders
- [ ] Proper spacing and padding
- [ ] Text is readable

### Responsiveness
- [ ] Sidebar visible on desktop
- [ ] Content adjusts to window size

---

## Expected Errors (NORMAL)

Since the backend API endpoints aren't implemented yet, you WILL see these errors in the browser console:

```
GET http://localhost:8000/api/admin/users 404 (Not Found)
GET http://localhost:8000/api/admin/products 404 (Not Found)
GET http://localhost:8000/api/admin/categories 404 (Not Found)
GET http://localhost:8000/api/admin/ml/metrics 404 (Not Found)
GET http://localhost:8000/api/admin/scraping/brands 404 (Not Found)
GET http://localhost:8000/api/admin/scraping/history 404 (Not Found)
```

**This is EXPECTED and OK!** These are the backend endpoints we need to implement next.

---

## Success Criteria Summary

### ✅ WORKING (Should be visible)
- Login page as landing
- Admin Dashboard after login
- Sidebar navigation
- All 5 pages render without crashing
- Black & white theme throughout
- NO emojis
- UI elements (buttons, forms, tables, sliders)
- Page switching works
- Logout button

### ⏳ NOT WORKING YET (Expected)
- API data loading
- User list
- Product list
- Training history
- Scraping history
- Actual functionality (CSV upload, training, scraping)

These require backend implementation.

---

## How to Report Issues

If something doesn't look right, tell me:

1. **Which page** (Overview, Users, Products, Training, Scraping)
2. **What's wrong** (layout issue, color issue, emoji still there, crash)
3. **What you see** (describe or screenshot)
4. **Console errors** (if any besides the expected 404s)

---

## Quick Test Checklist

Use this to quickly verify all pages:

```
1. [ ] Login page loads (black & white)
2. [ ] Login works and opens dashboard
3. [ ] Overview page shows welcome + stats cards
4. [ ] User Management page loads with table
5. [ ] Product Catalogue page loads with forms
6. [ ] ML Training page loads with slider
7. [ ] Auto Sync page loads with sections
8. [ ] NO emojis on any page
9. [ ] Sidebar navigation works (click each item)
10. [ ] Logout button works (returns to login)
```

---

**Testing Date:** November 11, 2025
**Status:** Frontend UI Complete - Backend APIs Pending






