# Quick Start: Testing the Scraping System

## 🚀 Quick Test (5 minutes)

### Step 1: Run the Test Script
```bash
python test_scraping.py
```

This will check:
- ✅ Excel files are readable
- ✅ Brands can be loaded
- ✅ Category normalization works
- ✅ MongoDB connection
- ✅ Scraper initialization

### Step 2: Start Backend Server
```bash
cd backend
python start_server.py
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 3: Start Frontend
```bash
cd frontend-app
npm run dev
```

### Step 4: Test in Browser

1. **Login to Admin Dashboard**
   - Go to admin login page
   - Login with admin credentials

2. **Navigate to Scraping Module**
   - Find "Auto Sync / Rescraping" in the dashboard
   - You should see brand type selector (Local/Pakistani/Luxury)

3. **Select Brand Type**
   - Choose "Local Affordable Brands" (this has the most links)
   - Brands should load automatically

4. **Select 1-2 Brands for Testing**
   - Click on brand cards to select them
   - Start with just 1-2 brands for testing

5. **Start Scraping**
   - Click "Start Scraping" button
   - Watch the progress section

6. **Monitor Progress**
   - Check "Brands Completed" counter
   - Check "Products Added" counter
   - Read "Activity Log" for details

## ✅ What to Look For

### Success Indicators:
- ✅ Brands load from Excel file
- ✅ Scraping starts without errors
- ✅ Progress updates appear
- ✅ Products are being added (counter increases)
- ✅ Activity logs show scraping activity
- ✅ Status changes to "completed" when done

### If Something Goes Wrong:

**No brands showing?**
- Check browser console (F12) for errors
- Verify Excel file is in project root: `women links dataset.xlsx`
- Check backend logs for file reading errors

**Scraping fails immediately?**
- Check backend terminal for error messages
- Verify MongoDB is running
- Check if brand URLs are valid (start with http://)

**No products found?**
- Some websites block scraping
- Try different brands
- Check activity logs for specific errors
- Generic scraper may need customization for specific sites

## 📊 Check Results in MongoDB

After scraping, verify products were stored:

```javascript
// Connect to MongoDB
use dupefinder

// Count scraped products
db.products.countDocuments({ scraped_at: { $exists: true } })

// View sample products
db.products.find({ scraped_at: { $exists: true } }).limit(5).pretty()

// Check normalized categories
db.products.distinct("normalized_category")

// Check products by brand
db.products.find({ brand: "Khaadi Pret" }).count()
```

## 🎯 Expected Results

After successful scraping:
- Products stored in MongoDB with:
  - `name`: Product name
  - `brand`: Brand name
  - `category`: Original category from Excel
  - `product_category`: Category extracted from website
  - `normalized_category`: Consistent category tag (e.g., "kurta")
  - `price`: Product price
  - `image_url`: Product image URL
  - `product_url`: Link to product page
  - `gender`: "w" or "m"
  - `scraped_at`: Timestamp

## 🔧 Troubleshooting

### Backend won't start?
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Frontend won't start?
```bash
# Install dependencies
cd frontend-app
npm install

# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

### MongoDB connection error?
- Make sure MongoDB service is running
- Check connection string in `backend/app/core/database.py`
- Default: `mongodb://localhost:27017/`

## 📝 Next Steps

Once basic scraping works:
1. **Test with more brands** (5-10 brands)
2. **Check category normalization** - verify all "kurta" variants become "kurta"
3. **Customize scrapers** for websites that don't work with generic scraper
4. **Add more category mappings** in `category_normalizer.py`
5. **Add link columns to men dataset** if needed

## 💡 Tips

- Start with **1-2 brands** for testing
- Use **"Local Affordable Brands"** type first (most links available)
- Check **activity logs** to see what's happening
- Some websites may block scraping - try different brands
- Scraping may take time (2-5 seconds per product)

---

**Need help?** Check `TEST_SCRAPING.md` for detailed troubleshooting guide.



