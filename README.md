# Anomaly Detection Using Transaction Data

<div align="center">

![Status](https://img.shields.io/badge/status-active-success.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/react-18+-61dafb.svg)

**Free, open-source web app for real-time transaction anomaly detection using machine learning.**

Upload CSVs or connect live Google Sheets and watch fraud patterns surface instantly.

[Features](#features) • [Demo](#demo) • [Installation](#installation) • [Usage](#usage) • [Documentation](#documentation)

</div>

---

## 🎯 Overview

This project is a production-grade web application that detects suspicious or abnormal financial transactions using Machine Learning. The system learns normal transaction behavior from historical data (amount, timing, frequency, patterns) and flags transactions that deviate significantly from these patterns.

**Key Capabilities:**
- 🔍 **Real-time anomaly detection** using Isolation Forest & One-Class SVM
- 📊 **Risk scoring** (0-100) with explainability for every transaction
- 📈 **Live data ingestion** via Google Sheets or CSV uploads
- 🏦 **Data warehousing** for historical analysis and trend tracking
- 🎨 **Modern fintech UI** with dark mode and real-time updates
- 🔓 **100% free** and open-source

## ✨ Features

### Core Functionality
- ✅ Upload transaction data via CSV files
- ✅ Automatic data validation and preprocessing
- ✅ Machine Learning-based anomaly detection (unsupervised)
- ✅ Real-time and batch transaction analysis
- ✅ Deep pattern analysis based on:
  - Transaction amount
  - Time and frequency
  - User behavior trends
  - Location and device patterns

### Intelligence & Scoring
- 🎯 **Fraud Risk Score** (0–100) for every transaction
- 🚦 **Color-coded severity levels**: Low, Medium, High, Critical
- 💡 **Explainability panel**: Why this transaction was flagged
- 📉 **Confidence scores** for model predictions
- 🔍 **Feature importance** analysis

### Transaction History Tracking
- 📜 Complete past transaction timeline
- 👤 User-wise and account-wise tracking
- 📊 Compare current vs. historical behavior
- 📈 Trend graphs and anomaly frequency charts

### Analytics Dashboard
- 🕐 Hourly transaction patterns
- 📊 Risk distribution visualizations
- 👥 Top risk users analysis
- 📉 Behavioral clustering insights

### Live Data Integration
- 🔗 **Google Sheets connector** for real-time monitoring
- ⚡ Automatic updates every 30 seconds
- 📡 REST API for external integrations
- 🔄 Incremental data processing

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  Dashboard │ Upload │ Transactions │ Analytics │ Live Data  │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────┐
│                    Backend (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Data Pipeline│  │  ML Engine   │  │   API Layer  │      │
│  │              │  │              │  │              │      │
│  │ • CSV Upload │  │ • Isolation  │  │ • /upload    │      │
│  │ • Validation │  │   Forest     │  │ • /train     │      │
│  │ • Google     │  │ • One-Class  │  │ • /analyze   │      │
│  │   Sheets     │  │   SVM        │  │ • /stats     │      │
│  │ • Cleaning   │  │ • Ensemble   │  │              │      │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘      │
│         │                  │                                 │
│         └──────────────────┴────────────────┐                │
│                                             │                │
└─────────────────────────────────────────────┼────────────────┘
                                              │
                     ┌────────────────────────▼───────────────┐
                     │      Data Warehouse (Parquet)          │
                     │  • Transaction history                 │
                     │  • User profiles                       │
                     │  • Analysis results                    │
                     └────────────────────────────────────────┘
```

## 🚀 Installation

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/anomaly-detection-webapp.git
cd anomaly-detection-webapp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Start the server
python main.py
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

The app will be available at `http://localhost:3000`

## 📖 Usage

### 1. Upload Transaction Data

**CSV Format Requirements:**

Required columns:
- `amount` - Transaction amount (numeric)
- `timestamp` - Transaction date/time (ISO format or any standard format)

Optional columns:
- `user_id` - User identifier
- `merchant_category` - Transaction category
- `location` - Transaction location
- `device_type` - Device used for transaction

**Example CSV:**
```csv
amount,timestamp,user_id,merchant_category,location
250.00,2024-01-15 14:30:00,user_001,retail,new_york
1500.00,2024-01-15 15:45:00,user_002,electronics,los_angeles
75.50,2024-01-15 16:20:00,user_001,food,new_york
```

Sample data is provided in `data/sample_csv/sample_transactions.csv`

### 2. Train the Model

Once data is uploaded:
1. Click "Train Model" button in the dashboard
2. Wait for training to complete (usually < 10 seconds for 1000s of transactions)
3. Model will be saved automatically

### 3. Analyze Transactions

After training:
- View risk scores in the Transactions tab
- Click on any transaction to see detailed explanation
- Filter by risk level or search by user/amount
- Export results for further analysis

### 4. Connect Live Data (Google Sheets)

**Setup:**
1. Create a Google Sheet with required columns
2. Share sheet publicly or with service account
3. Go to "Live Data" tab
4. Paste sheet URL and worksheet name
5. Click "Connect"

**For Private Sheets:**
1. Create Google Cloud Project
2. Enable Google Sheets API
3. Create service account
4. Download credentials JSON
5. Place at `backend/credentials.json`
6. Share sheet with service account email

## 🔌 API Documentation

### Upload CSV
```http
POST /upload/csv
Content-Type: multipart/form-data

file: <csv_file>
```

### Train Model
```http
POST /train
Content-Type: application/json

{
  "use_ensemble": false,
  "contamination": 0.1
}
```

### Get Transactions
```http
GET /transactions?limit=100&risk_level=High&user_id=user_001
```

### Get Explanation
```http
GET /transactions/{transaction_id}/explain
```

### Get Statistics
```http
GET /statistics
```

Full API documentation available at `http://localhost:8000/docs` when running.

## 🧠 Machine Learning Approach

### Models Used

**1. Isolation Forest**
- Primary model for anomaly detection
- Works by isolating observations
- Efficient for high-dimensional data
- Default contamination: 10%

**2. One-Class SVM**
- Support Vector Machine for outlier detection
- Learns decision boundary around normal data
- Good for complex patterns

**3. Ensemble (Optional)**
- Combines both models
- Weighted voting (IF: 60%, SVM: 40%)
- Higher accuracy but slower

### Feature Engineering

Automatic feature extraction:
- **Amount features**: Raw amount, log-transformed amount
- **Time features**: Hour, day of week, weekend flag, night flag
- **User features**: Average amount, standard deviation, transaction count
- **Behavioral features**: Amount vs. user average, transaction velocity
- **Frequency features**: Time since last transaction

### Risk Scoring

Risk score calculation:
1. Model outputs anomaly score (more negative = more anomalous)
2. Normalize to 0-100 scale
3. Boost scores for flagged anomalies
4. Categorize into risk levels:
   - **Low** (0-30): Normal behavior
   - **Medium** (30-60): Slight deviation
   - **High** (60-85): Significant anomaly
   - **Critical** (85-100): Extreme outlier

## 📊 Data Warehouse

Transactions are stored in efficient Parquet format with:
- Automatic deduplication
- Time-series indexing
- User profiling
- Source tracking

**Querying:**
```python
from data_pipeline.processor import DataWarehouse

warehouse = DataWarehouse()

# Get last 100 transactions
df = warehouse.get_transactions(limit=100)

# Get transactions for specific user
df = warehouse.get_transactions(user_id='user_001')

# Get transactions in date range
df = warehouse.get_transactions(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

## 🎨 UI Design

Built with a dark fintech theme inspired by:
- Trading terminals (TradingView aesthetic)
- Modern fintech apps (Stripe, Revolut)
- Data-dense dashboards (Bloomberg)

**Design Principles:**
- Clean, professional typography
- Smooth animations and transitions
- Data-first layout
- Real-time updates
- Glassmorphism effects
- Minimal gradients
- High information density

## 🛠️ Tech Stack

**Backend:**
- FastAPI (Web framework)
- Scikit-learn (ML models)
- Pandas (Data processing)
- NumPy (Numerical computing)
- SQLAlchemy (ORM, optional)
- Gspread (Google Sheets)

**Frontend:**
- React 18
- Lucide React (Icons)
- Custom CSS (Dark theme)
- Fetch API (HTTP client)

**Data:**
- Parquet (Data warehouse)
- CSV (Import/Export)
- JSON (Configuration)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Scikit-learn for ML algorithms
- FastAPI for the excellent web framework
- React community for amazing tools

## 📧 Contact

Project Link: [https://github.com/yourusername/anomaly-detection-webapp](https://github.com/yourusername/anomaly-detection-webapp)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

Made with ❤️ for the open-source community

</div>
