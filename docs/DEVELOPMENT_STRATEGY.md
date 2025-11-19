# DupeFinder - Development Strategy & Planning

**Document Version**: 1.0  
**Date**: November 6, 2025  
**Status**: Planning Phase

---

## 🎯 Project Overview (Updated)

### Architecture Clarification

**IMPORTANT CHANGE**: The project consists of TWO separate applications:

1. **Admin Web Application** (React)
   - Purpose: Catalog management and curation
   - Users: Admin team only
   - Features: Add/edit products, bulk import, analytics

2. **Mobile Application** (Flutter)
   - Purpose: End-user dupe finding
   - Users: General public
   - Features: Image search, product browsing, favorites

3. **Shared Backend** (FastAPI)
   - Serves both admin and mobile
   - Single API with different endpoints for each

---

## 🚀 Critical Path: Admin-First Approach

```
Phase 1: Infrastructure ✅ DONE
    ↓
Phase 2: Data Strategy ⏸️ NEED YOUR INPUT
    ↓
Phase 3: Backend API for Admin
    ↓
Phase 4: Admin Dashboard
    ↓
Phase 5: Data Collection
    ↓
Phase 6: ML Model Training
    ↓
Phase 7: Mobile App Development
    ↓
Phase 8: Integration & Launch
```

**Why Admin First?**
- Need product catalog before ML training
- Need ML model before mobile app is useful
- Admin tool helps team curate data efficiently
- Can test backend independently

---

## 📊 Current Status: BLOCKED on Data Strategy

### What We've Done ✅
- ✅ Project structure created
- ✅ Git repository set up
- ✅ Configuration files ready
- ✅ Documentation in place

### What We Need From You 🚨

#### **1. Brand Selection**

**Question**: Which brands do you want to include?

**Two Types Needed**:
- **Luxury Brands** (for reference/comparison)
  - Example: Rolex, Gucci, Louis Vuitton, etc.
  - These are what users will photograph
  
- **Affordable Alternative Brands** (to recommend)
  - Example: Daniel Wellington, Michael Kors, Fossil, etc.
  - These are what we'll suggest as dupes

**Recommendation**: Start with 5-10 brands, expand later

**Please Provide**:
```
Luxury Brands:
1. [Brand Name] - [Website URL]
2. [Brand Name] - [Website URL]
...

Affordable Brands:
1. [Brand Name] - [Website URL]
2. [Brand Name] - [Website URL]
...
```

---

#### **2. Data Collection Method**

**Question**: How will we get product data?

**Option A: Web Scraping**
- **Pros**: Automated, large datasets, current prices
- **Cons**: Technical, may violate ToS, maintenance needed
- **What I need**: Brand website URLs, permission to scrape
- **I can build**: Custom scrapers for each brand

**Option B: CSV/Excel Import**
- **Pros**: Simple, controlled quality, legal
- **Cons**: Manual work, time-consuming, outdated quickly
- **What I need**: CSV template, you collect data
- **I can build**: Import system in admin dashboard

**Option C: Manual Entry via Admin**
- **Pros**: Full control, flexible
- **Cons**: Very time-consuming, small datasets
- **What I need**: Nothing
- **I can build**: User-friendly forms in admin

**Option D: APIs (if available)**
- **Pros**: Official, reliable, legal
- **Cons**: Rare for fashion brands, may cost money
- **What I need**: API access tokens
- **I can build**: API integration

**My Recommendation**: 
Start with Option B (CSV import) + Option C (manual entry) for flexibility. Add scraping later if needed.

**Your Decision**: _________________

---

#### **3. Data Requirements per Product**

**Question**: What information do we need for each product?

**Minimum Required**:
- Product name
- Brand
- Price (in PKR or USD?)
- At least 1 product image
- Category (Watch, Bag, Shoes, etc.)
- Product URL (where to buy)

**Optional but Recommended**:
- Description
- Multiple images (different angles)
- Original luxury price (for comparison)
- Size/dimensions
- Color
- Material
- Gender (male/female/unisex)
- Stock status
- City/location (for local stores)

**Your Requirements**: (Check what you want to include)
```
[ ] Product Name
[ ] Brand
[ ] Price
[ ] Currency (PKR/USD/Other: _____)
[ ] Images (How many per product? ____)
[ ] Category
[ ] Description
[ ] Size
[ ] Color
[ ] Material
[ ] Gender
[ ] Purchase URL
[ ] Other: _________________
```

---

#### **4. Dataset Size & Timeline**

**Question**: How much data and when?

**ML Training Requirements**:
- **Minimum**: 100-200 products per category (will work, but limited)
- **Good**: 500-1000 products total (decent accuracy)
- **Ideal**: 2000+ products (80%+ accuracy target)

**Recommendation**: 
- **Phase 1 (MVP)**: 300-500 products across 3-5 categories
- **Phase 2 (Launch)**: 1000-1500 products across all categories
- **Phase 3 (Scale)**: 3000+ products

**Your Plan**:
```
Initial dataset size: _____ products
Number of categories: _____
Timeline: 
  - Week 1-2: Collect _____ products
  - Week 3-4: Collect _____ products
  - Week 5+: Expand to _____ products
```

---

#### **5. Development Environment**

**Question**: Docker or manual setup?

**Option A: Use Docker**
- One command starts everything
- Consistent across team
- **Requirement**: Install Docker Desktop (4-6GB)

**Option B: Manual Setup**
- Install PostgreSQL, Python, Node.js separately
- More control, better for learning
- **Requirement**: Install each tool individually

**My Recommendation**: Start manual (learn the tools), use Docker for deployment later

**Your Choice**: _________________

**PostgreSQL**: Do you have it installed? Yes / No / Will install

---

## 📋 Next Steps (Once You Provide Answers)

### Immediate Actions:

1. **If you choose CSV import**:
   - I'll create a CSV template
   - You fill it with product data
   - I'll build import functionality in admin

2. **If you choose web scraping**:
   - You provide brand URLs
   - I'll build scrapers
   - We review and validate data

3. **If you choose manual entry**:
   - I'll build admin forms
   - You enter products one by one
   - Slower but most flexible

### Development Sequence:

**Week 1-2: Backend + Admin Foundation**
- Set up FastAPI backend
- Create database (PostgreSQL)
- Build basic admin authentication
- Create product CRUD API

**Week 3-4: Admin Dashboard**
- Build React admin interface
- Product list/add/edit pages
- CSV import (if chosen)
- Image upload

**Week 5-6: Data Collection**
- Collect/import products
- Validate data quality
- Organize images
- Test catalog

**Week 7-8: ML Training**
- Prepare training dataset
- Train image similarity model
- Generate embeddings
- Build FAISS index

**Week 9-12: Mobile App**
- Build Flutter app
- Implement image search
- Product display
- User features

**Week 13-14: Integration & Testing**
- Connect all pieces
- End-to-end testing
- Performance optimization
- Bug fixes

**Week 15-16: Polish & Deployment**
- Final testing
- Documentation
- Presentation prep
- Deployment

---

## 🎨 What Each Module Will Look Like

### Admin Dashboard Features:

**Page 1: Login**
- Email/password authentication
- JWT token storage

**Page 2: Product List**
- Table showing all products
- Search and filter
- Pagination
- Edit/Delete buttons

**Page 3: Add/Edit Product**
- Form with all product fields
- Image upload with preview
- Category dropdown
- Save/Cancel buttons

**Page 4: Bulk Import**
- CSV file upload
- Preview before import
- Validation errors display
- Import confirmation

**Page 5: Analytics (Later)**
- Total products count
- Most searched categories
- Popular products

### Mobile App Features:

**Screen 1: Home/Search**
- Camera button (take photo)
- Gallery button (choose photo)
- Recent searches

**Screen 2: Search Results**
- Grid of similar products
- Similarity score
- Price and savings
- Tap to see details

**Screen 3: Product Detail**
- Product images carousel
- Description, price, specs
- "Where to Buy" link
- Add to favorites

**Screen 4: Favorites**
- Saved products
- Remove option

**Screen 5: Profile** (Later)
- User info
- Savings summary
- Search history

---

## 🤔 Important Questions to Clarify

### Data Questions:
1. **Local vs Online Stores**: Include both or focus on one?
2. **Pakistan Focus**: Is this for Pakistani market specifically?
3. **Price Currency**: PKR, USD, or multiple currencies?
4. **Product Categories**: Which categories to prioritize?
   - Watches
   - Bags/Purses
   - Shoes
   - Accessories
   - Clothing
   - Jewelry
   - All of the above?

### Technical Questions:
1. **Authentication**: Need user accounts or just search without login?
2. **Payment**: Will users buy through app or redirect to store?
3. **Notifications**: Push notifications for price drops/new products?
4. **Offline Mode**: Should mobile work offline (saved favorites)?
5. **Deployment**: Where to host (AWS, GCP, local server)?

### Team Questions:
1. **Team Size**: How many people working on this?
2. **Roles**: Who does what (frontend, backend, data collection)?
3. **Timeline**: When is the FYP due?
4. **Budget**: Any budget for hosting, APIs, services?

---

## 📝 Recommended First Step

**My Recommendation**: Let's start with a **Minimal Viable Product (MVP)** approach:

### MVP Scope:
- **1 Category**: Watches only
- **5 Brands**: 2 luxury + 3 affordable
- **200 Products**: 40 products per brand
- **Manual Entry**: Use admin to add products (no scraping yet)
- **Basic ML**: Simple ResNet model
- **Simple Mobile**: Just search and results (no user accounts yet)

### Why This Works:
- ✅ Achievable in 4-6 weeks
- ✅ Demonstrates core functionality
- ✅ Can expand after proving concept
- ✅ Less data collection burden
- ✅ Easier to present/demo

**Do you want to start with MVP approach?** Yes / No

If yes, which category? _________________

---

## 🚦 Decision Summary

Please fill out and send back:

```
=== DECISIONS ===

1. Brand List:
   Luxury: [List or "Will provide later"]
   Affordable: [List or "Will provide later"]

2. Data Collection: 
   Method: [Scraping / CSV / Manual / Mix]
   
3. Data Fields:
   [List checked items from section 3]

4. Dataset Size:
   Initial: _____ products
   Timeline: _____

5. Development:
   Environment: [Docker / Manual]
   PostgreSQL: [Installed / Will install / Need help]

6. MVP Approach:
   Start with MVP: [Yes / No]
   Category: _____
   
7. Timeline:
   FYP Due Date: _____
   Available hours per week: _____

8. Questions/Concerns:
   [Any questions or concerns]
```

---

## 📞 Next Actions

**Once you provide the above information**, I will:

1. ✅ Update the development plan
2. ✅ Create detailed task breakdowns
3. ✅ Set up the backend and database
4. ✅ Build the admin dashboard
5. ✅ Create data collection tools based on your choice
6. ✅ Guide you through the entire development process

**We'll proceed step-by-step, one phase at a time!**

---

**Ready to start when you are!** 🚀



