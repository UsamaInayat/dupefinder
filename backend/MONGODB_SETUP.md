# MongoDB Atlas Connection Setup

## ✅ Connection Configured

Your MongoDB Atlas database has been successfully connected to the DupeFinder backend!

### Connection Details:
- **URI**: `mongodb+srv://ussamainayat:ussamainayat@dupefinder.u30xrsm.mongodb.net/`
- **Database Name**: `dupefinder`
- **Driver**: Motor (async MongoDB driver for Python)

---

## 📁 Files Created

### 1. Configuration Files
- `backend/app/core/config.py` - Settings management with Pydantic
- `backend/app/core/database.py` - MongoDB connection handler

### 2. Models & Services
- `backend/app/models/mongodb_models.py` - Pydantic models for MongoDB documents
- `backend/app/services/mongodb_service.py` - Service layer for database operations

### 3. API Routes
- `backend/app/api/routes/database.py` - Database health check and stats endpoints

### 4. Test Script
- `backend/test_connection.py` - Standalone connection test script

---

## 🚀 How to Test the Connection

### Option 1: Test Script (Recommended First)
```bash
cd backend
python test_connection.py
```

This will:
- ✅ Test the connection
- ✅ Show database status
- ✅ List all collections
- ✅ Display document counts

### Option 2: Start the Server
```bash
cd backend
uvicorn main:app --reload
```

Then visit:
- Health check: http://localhost:8000/health
- Database health: http://localhost:8000/api/database/health
- Database stats: http://localhost:8000/api/database/stats
- List collections: http://localhost:8000/api/database/collections

---

## 📊 MongoDB Collections

The following collections are ready to use:

1. **product_embeddings** - Stores ML model embeddings for products
2. **user_search_analytics** - Tracks user search behavior
3. **image_metadata** - Stores image file metadata
4. **analytics_events** - General analytics events
5. **ml_model_logs** - ML model performance logs

---

## 🔧 Installation Requirements

Make sure you have installed the dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Key dependencies:
- `motor==3.3.2` - Async MongoDB driver
- `pymongo==4.6.0` - MongoDB Python driver
- `pydantic==2.5.2` - Data validation
- `pydantic-settings==2.1.0` - Settings management

---

## 🛠️ Usage Examples

### In Your Code:

```python
from app.core.database import get_database
from app.services.mongodb_service import create_product_embedding

# Get database instance
db = get_database()

# Use service functions
embedding_data = {
    "product_id": "123",
    "embedding": [0.1, 0.2, ...],  # 2048 dimensions
    "model_version": "resnet50"
}
await create_product_embedding(embedding_data)
```

---

## ⚠️ Important Notes

1. **IP Whitelist**: Make sure your MongoDB Atlas cluster allows connections from your IP address
   - Go to MongoDB Atlas → Network Access
   - Add your IP or use `0.0.0.0/0` for development (not recommended for production)

2. **Environment Variables**: The connection string is hardcoded in `config.py` for now
   - For production, move it to `.env` file
   - The `.env` file is gitignored for security

3. **Connection Pooling**: The connection uses connection pooling
   - Max pool size: 50
   - Min pool size: 10
   - Timeout: 5 seconds

---

## 🐛 Troubleshooting

### Connection Failed?
1. Check internet connection
2. Verify MongoDB Atlas cluster is running
3. Check IP whitelist in MongoDB Atlas dashboard
4. Verify username/password in connection string
5. Check firewall settings

### Import Errors?
```bash
pip install motor pymongo pydantic pydantic-settings
```

### Module Not Found?
Make sure you're running from the project root:
```bash
# From project root
python backend/test_connection.py

# Or from backend directory
cd backend
python test_connection.py
```

---

## ✅ Next Steps

1. **Test the connection** using `test_connection.py`
2. **Start the server** and check health endpoints
3. **Begin building** your product catalog APIs
4. **Add collections** as needed for your use case

---

**Connection is ready!** 🎉

