# Quick Start Guide

Get the anomaly detection system running in 5 minutes.

## Prerequisites Check

```bash
python --version  # Should be 3.9+
node --version    # Should be 16+
```

## Option 1: Quick Demo (Fastest)

### 1. Start Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
```

✅ API running at http://localhost:8000

### 2. Start Frontend
```bash
# New terminal
cd frontend
npm install
npm run dev
```

✅ App running at http://localhost:3000

### 3. Upload Sample Data
1. Open http://localhost:3000
2. Go to "Upload Data" tab
3. Upload `data/sample_csv/sample_transactions.csv`
4. Wait for upload to complete

### 4. Train Model
1. Dashboard will show "Train Model" button
2. Click it and wait ~5 seconds
3. Model is now trained!

### 5. View Results
1. Go to "Transactions" tab
2. See risk scores for all transactions
3. Click any transaction to see why it was flagged
4. Explore Analytics tab for visualizations

🎉 **Done! You're now detecting anomalies.**

## Option 2: Live Data with Google Sheets

### 1. Create Google Sheet

Make a sheet with these columns:
```
amount | timestamp           | user_id  | merchant_category | location
250.00 | 2024-01-15 14:30:00| user_001 | retail           | new_york
```

### 2. Make Sheet Public
- Click "Share" in Google Sheets
- Change to "Anyone with the link can view"
- Copy the URL

### 3. Connect in App
1. Go to "Live Data" tab
2. Paste your sheet URL
3. Enter worksheet name (usually "Sheet1")
4. Click "Connect"

### 4. Add New Rows
- Add transactions to your sheet
- App fetches updates every 30 seconds
- New anomalies detected automatically!

## Testing the Detection

Add these transactions to test anomaly detection:

**Normal transaction:**
```
50.00,2024-01-20 14:30:00,user_001,food,new_york
```
→ Should get Low risk score

**Suspicious amount:**
```
15000.00,2024-01-20 14:35:00,user_001,jewelry,new_york
```
→ Should get High/Critical risk score

**Unusual time:**
```
500.00,2024-01-20 03:00:00,user_001,retail,new_york
```
→ Should get Medium/High risk (3am transaction)

**Foreign location:**
```
2000.00,2024-01-20 14:40:00,user_001,electronics,tokyo
```
→ Should get High risk (unusual location for this user)

## Common Issues

### Port Already in Use
```bash
# Backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

### Module Not Found
```bash
# Backend
cd backend
pip install -r requirements.txt --upgrade

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS Errors
- Make sure backend is running on port 8000
- Check browser console for specific error
- Verify API_BASE_URL in App.jsx is correct

### Model Training Fails
- Ensure you have at least 10 transactions uploaded
- Check backend logs for specific error
- Try with sample data first

## Next Steps

### Improve Detection Accuracy
1. Upload more historical data (100+ transactions recommended)
2. Include more columns (user_id, location, device_type)
3. Use ensemble model for better accuracy
4. Adjust contamination parameter (default: 0.1)

### Production Deployment

**Backend:**
```bash
# Use production ASGI server
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
```

**Frontend:**
```bash
# Build for production
npm run build
# Serve build folder with nginx or similar
```

### Advanced Features

**Custom Model Training:**
```python
from ml.anomaly_detector import AnomalyDetector

detector = AnomalyDetector(
    model_type='isolation_forest',
    contamination=0.15  # Expect 15% anomalies
)
detector.train(df, use_pca=True, n_components=10)
```

**Batch Analysis:**
```bash
curl -X POST http://localhost:8000/analyze
```

**Export Results:**
```python
import pandas as pd

# Get all flagged transactions
df = warehouse.get_transactions(limit=1000)
results = model.predict(df)
anomalies = df[results['is_anomaly']]
anomalies.to_csv('flagged_transactions.csv')
```

## Tips for Best Results

1. **Data Quality Matters**
   - Clean timestamps (consistent format)
   - Valid amounts (no negatives)
   - Unique transaction IDs
   - Complete user information

2. **Training Data Volume**
   - Minimum: 10 transactions
   - Good: 100+ transactions
   - Excellent: 1000+ transactions
   - More data = better detection

3. **Feature Engineering**
   - Include user_id for user-level analysis
   - Add location for geographic patterns
   - Device type helps detect account takeovers
   - Merchant category for spending patterns

4. **Model Selection**
   - Isolation Forest: Fast, good for most cases
   - One-Class SVM: Better for complex patterns
   - Ensemble: Best accuracy, slower

5. **Contamination Tuning**
   - 0.05 (5%): Conservative, fewer false positives
   - 0.10 (10%): Balanced (default)
   - 0.15 (15%): Aggressive, catches more anomalies

## Getting Help

- Check the [README](README.md) for full documentation
- See [API docs](http://localhost:8000/docs) for endpoint details
- Open an issue on GitHub for bugs
- Star the repo if it helps! ⭐

---

**Ready to detect some fraud? Let's go! 🚀**
