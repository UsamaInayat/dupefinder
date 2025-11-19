# How to Test the Scraping System

## Prerequisites

1. **Backend Server Running**
   - Make sure MongoDB is running
   - Backend server should be on `http://localhost:8000`

2. **Frontend Running**
   - Frontend should be running (usually on `http://localhost:5173` or similar)

3. **Excel Files in Place**
   - `women links dataset.xlsx` should be in the project root
   - `men dataset.xlsx` should be in the project root

4. **Admin Account**
   - You need to be logged in as an admin user

## Step-by-Step Testing Guide

### Step 1: Start the Backend Server

```bash
cd backend
python start_server.py
# OR
python -m uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 2: Start the Frontend

```bash
cd frontend-app
npm run dev
# OR
yarn dev
```

### Step 3: Login as Admin

1. Go to the admin login page
2. Login with your admin credentials
3. Navigate to the Admin Dashboard

### Step 4: Access Scraping Management

1. In the Admin Dashboard, find the **"Auto Sync / Rescraping"** module
2. This should show you a list of brands from the Excel files

### Step 5: Test Brand Loading

**Check if brands are loading:**
- You should see brand cards with:
  - Brand name
  - Product count (initially 0)
  - Category (e.g., "Women → Stitched")
  - Brand URL

**If no brands show up:**
- Check browser console for errors
- Verify Excel files are in the project root
- Check backend logs for errors

### Step 6: Select a Brand and Start Scraping

1. **Select 1-2 brands** (start small for testing)
2. Click **"Start Scraping"** button
3. You should see:
   - Progress bar
   - Brands completed count
   - Products added count
   - Activity logs

### Step 7: Monitor Progress

Watch the progress section:
- **Brands Completed**: Shows X / Y brands processed
- **Products Added**: Total products scraped and stored
- **Activity Log**: Real-time logs of scraping activity

### Step 8: Check Results

After scraping completes:
1. Check MongoDB to see if products were stored
2. Verify products have `normalized_category` field
3. Check that categories are consistent (e.g., "kurta" not "kurtis")

## Quick Test Script

You can also test the API directly using curl or Postman:

### Test 1: Get Available Brands
```bash
curl -X GET "http://localhost:8000/api/admin/scraping/brands?brand_type=local" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Test 2: Start Scraping
```bash
curl -X POST "http://localhost:8000/api/admin/scraping/start" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand_ids": [
      {
        "brand_name": "Khaadi Pret",
        "brand_url": "https://khaadi.com",
        "category": "Women → Stitched"
      }
    ]
  }'
```

### Test 3: Check Scraping Status
```bash
curl -X GET "http://localhost:8000/api/admin/scraping/status/JOB_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

## Troubleshooting

### Issue: No brands showing up
**Solution:**
- Check if Excel files exist in project root
- Verify file names are exactly: `women links dataset.xlsx` and `men dataset.xlsx`
- Check backend logs for file reading errors
- Verify you're logged in as admin

### Issue: Scraping fails immediately
**Solution:**
- Check backend logs for error messages
- Verify MongoDB is running and connected
- Check if brand URLs are valid (start with http:// or https://)
- Some websites may block scraping - try different brands

### Issue: No products found
**Solution:**
- The generic scraper may not work for all websites
- Some sites need custom scraping logic
- Check activity logs to see what's happening
- Verify product URLs are being found

### Issue: Categories not normalizing
**Solution:**
- Check if `normalized_category` field exists in MongoDB
- Verify category extraction is working
- Check `category_normalizer.py` mappings

## Expected Behavior

✅ **Working correctly if:**
- Brands load from Excel files
- Scraping starts without errors
- Progress updates in real-time
- Products are stored in MongoDB
- Products have `normalized_category` field
- Categories are consistent (e.g., all "kurta" not mixed with "kurtis")

## Next Steps After Testing

1. **Customize scrapers** for specific websites that don't work with generic scraper
2. **Add more category mappings** in `category_normalizer.py`
3. **Monitor scraping jobs** and fix any errors
4. **Add link columns to men dataset** if needed

## MongoDB Query to Check Scraped Products

```javascript
// Connect to MongoDB and run:
db.products.find({ 
  normalized_category: "kurta",
  gender: "w"
}).limit(10)

// Check all scraped products
db.products.find({ 
  scraped_at: { $exists: true }
}).count()

// Check products by brand
db.products.find({ 
  brand: "Khaadi Pret"
}).count()
```



