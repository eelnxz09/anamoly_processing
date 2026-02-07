"""
Data Pipeline for Transaction Processing
Handles CSV uploads, Google Sheets integration, and data validation
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
import aiofiles
import hashlib
import json


class DataValidator:
    """Validate and clean transaction data"""
    
    REQUIRED_COLUMNS = ['amount', 'timestamp']
    OPTIONAL_COLUMNS = ['user_id', 'merchant_category', 'location', 'device_type', 'transaction_id']
    
    @staticmethod
    def validate_csv(df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate CSV data structure and content
        
        Returns:
            (is_valid, error_messages)
        """
        errors = []
        
        # Check required columns
        missing_cols = set(DataValidator.REQUIRED_COLUMNS) - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        
        # Check data types
        if 'amount' in df.columns:
            if not pd.api.types.is_numeric_dtype(df['amount']):
                errors.append("'amount' column must be numeric")
            elif (df['amount'] < 0).any():
                errors.append("'amount' column contains negative values")
        
        # Check timestamp format
        if 'timestamp' in df.columns:
            try:
                pd.to_datetime(df['timestamp'])
            except Exception as e:
                errors.append(f"'timestamp' column has invalid date format: {str(e)}")
        
        # Check for empty dataframe
        if len(df) == 0:
            errors.append("CSV file is empty")
        
        # Check for minimum rows
        if len(df) < 10:
            errors.append(f"Too few transactions ({len(df)}). Minimum 10 required for analysis")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and standardize transaction data"""
        df = df.copy()
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.strip()
        
        # Convert timestamp
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Remove duplicates
        if 'transaction_id' in df.columns:
            df = df.drop_duplicates(subset=['transaction_id'])
        else:
            # Create hash-based transaction ID if not present
            df['transaction_id'] = df.apply(
                lambda row: hashlib.md5(
                    f"{row['amount']}{row['timestamp']}".encode()
                ).hexdigest()[:12],
                axis=1
            )
        
        # Handle missing values
        if 'user_id' not in df.columns:
            df['user_id'] = 'unknown'
        
        df['user_id'] = df['user_id'].fillna('unknown')
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        return df
    
    @staticmethod
    def augment_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add derived features for better analysis"""
        df = df.copy()
        
        # Time-based features
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
        
        # Transaction velocity (transactions per hour for each user)
        df['transaction_count'] = df.groupby('user_id').cumcount() + 1
        
        # Time since last transaction (per user)
        df['time_since_last_tx'] = df.groupby('user_id')['timestamp'].diff().dt.total_seconds() / 3600
        df['time_since_last_tx'] = df['time_since_last_tx'].fillna(24)  # Default 24 hours
        
        return df


class CSVProcessor:
    """Handle CSV file uploads and processing"""
    
    def __init__(self, upload_dir: str = "/home/claude/anomaly-detection-webapp/data/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.validator = DataValidator()
    
    async def process_csv(self, file_content: bytes, filename: str) -> Tuple[pd.DataFrame, Dict]:
        """
        Process uploaded CSV file
        
        Returns:
            (dataframe, metadata)
        """
        # Save file
        file_path = self.upload_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)
        
        # Read CSV
        try:
            df = pd.read_csv(file_path)
        except Exception as e:
            raise ValueError(f"Failed to read CSV: {str(e)}")
        
        # Validate
        is_valid, errors = self.validator.validate_csv(df)
        if not is_valid:
            raise ValueError(f"Invalid CSV: {'; '.join(errors)}")
        
        # Clean
        df = self.validator.clean_data(df)
        
        # Augment
        df = self.validator.augment_features(df)
        
        # Generate metadata
        metadata = {
            'filename': filename,
            'upload_time': datetime.now().isoformat(),
            'row_count': len(df),
            'columns': df.columns.tolist(),
            'date_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat()
            },
            'amount_stats': {
                'min': float(df['amount'].min()),
                'max': float(df['amount'].max()),
                'mean': float(df['amount'].mean()),
                'median': float(df['amount'].median())
            }
        }
        
        return df, metadata


class GoogleSheetsConnector:
    """
    Connect to Google Sheets for live data ingestion
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """
        Initialize Google Sheets connector
        
        Args:
            credentials_path: Path to service account JSON credentials
        """
        self.credentials_path = credentials_path
        self.client = None
        self.validator = DataValidator()
    
    def connect(self, spreadsheet_url: str) -> None:
        """Authenticate and connect to Google Sheets"""
        if not self.credentials_path:
            raise ValueError("Google Sheets credentials not configured")
        
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        
        creds = Credentials.from_service_account_file(
            self.credentials_path,
            scopes=scopes
        )
        
        self.client = gspread.authorize(creds)
        self.spreadsheet_url = spreadsheet_url
    
    def fetch_data(self, worksheet_name: str = 'Sheet1') -> pd.DataFrame:
        """
        Fetch transaction data from Google Sheets
        
        Args:
            worksheet_name: Name of worksheet to read
            
        Returns:
            DataFrame with transaction data
        """
        if not self.client:
            raise ValueError("Not connected to Google Sheets. Call connect() first.")
        
        # Open spreadsheet
        sheet = self.client.open_by_url(self.spreadsheet_url)
        worksheet = sheet.worksheet(worksheet_name)
        
        # Get all values
        data = worksheet.get_all_records()
        
        if not data:
            raise ValueError("No data found in spreadsheet")
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Validate
        is_valid, errors = self.validator.validate_csv(df)
        if not is_valid:
            raise ValueError(f"Invalid sheet data: {'; '.join(errors)}")
        
        # Clean and augment
        df = self.validator.clean_data(df)
        df = self.validator.augment_features(df)
        
        return df
    
    def fetch_incremental(self, worksheet_name: str = 'Sheet1', 
                         last_row: int = 0) -> Tuple[pd.DataFrame, int]:
        """
        Fetch only new rows since last fetch
        
        Args:
            worksheet_name: Name of worksheet
            last_row: Last row number fetched
            
        Returns:
            (new_data_df, new_last_row)
        """
        if not self.client:
            raise ValueError("Not connected. Call connect() first.")
        
        sheet = self.client.open_by_url(self.spreadsheet_url)
        worksheet = sheet.worksheet(worksheet_name)
        
        # Get current row count
        all_values = worksheet.get_all_values()
        current_rows = len(all_values)
        
        # No new data
        if current_rows <= last_row:
            return pd.DataFrame(), last_row
        
        # Fetch new rows
        new_values = all_values[last_row:]
        
        # Convert to DataFrame (first row is headers)
        if last_row == 0:
            df = pd.DataFrame(new_values[1:], columns=new_values[0])
        else:
            # Use existing headers
            headers = all_values[0]
            df = pd.DataFrame(new_values, columns=headers)
        
        if len(df) == 0:
            return df, current_rows
        
        # Clean and process
        df = self.validator.clean_data(df)
        df = self.validator.augment_features(df)
        
        return df, current_rows


class DataWarehouse:
    """
    Simple data warehouse layer for historical transaction storage and analysis
    """
    
    def __init__(self, data_dir: str = "/home/claude/anomaly-detection-webapp/data/warehouse"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.transactions_file = self.data_dir / "transactions.parquet"
        self.metadata_file = self.data_dir / "metadata.json"
    
    def store_transactions(self, df: pd.DataFrame, source: str = "upload"):
        """
        Store transactions in data warehouse
        
        Args:
            df: Transaction dataframe
            source: Data source identifier
        """
        # Load existing data if available
        if self.transactions_file.exists():
            existing_df = pd.read_parquet(self.transactions_file)
            
            # Merge with new data
            df['source'] = source
            df['ingestion_time'] = datetime.now()
            
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            
            # Remove duplicates based on transaction_id
            combined_df = combined_df.drop_duplicates(subset=['transaction_id'], keep='last')
        else:
            df['source'] = source
            df['ingestion_time'] = datetime.now()
            combined_df = df
        
        # Save to parquet (efficient columnar storage)
        combined_df.to_parquet(self.transactions_file, index=False)
        
        # Update metadata
        self._update_metadata(combined_df)
        
        print(f"✓ Stored {len(df)} transactions (total: {len(combined_df)})")
    
    def get_transactions(self, 
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None,
                        user_id: Optional[str] = None,
                        limit: Optional[int] = None) -> pd.DataFrame:
        """
        Retrieve transactions with filters
        
        Args:
            start_date: Filter by start date
            end_date: Filter by end date
            user_id: Filter by user
            limit: Maximum number of records
            
        Returns:
            Filtered DataFrame
        """
        if not self.transactions_file.exists():
            return pd.DataFrame()
        
        df = pd.read_parquet(self.transactions_file)
        
        # Apply filters
        if start_date:
            df = df[df['timestamp'] >= start_date]
        
        if end_date:
            df = df[df['timestamp'] <= end_date]
        
        if user_id:
            df = df[df['user_id'] == user_id]
        
        # Sort by timestamp descending
        df = df.sort_values('timestamp', ascending=False)
        
        if limit:
            df = df.head(limit)
        
        return df
    
    def get_statistics(self) -> Dict:
        """Get warehouse statistics"""
        if not self.metadata_file.exists():
            return {}
        
        with open(self.metadata_file, 'r') as f:
            return json.load(f)
    
    def _update_metadata(self, df: pd.DataFrame):
        """Update warehouse metadata"""
        metadata = {
            'total_transactions': len(df),
            'unique_users': df['user_id'].nunique(),
            'date_range': {
                'start': df['timestamp'].min().isoformat(),
                'end': df['timestamp'].max().isoformat()
            },
            'last_updated': datetime.now().isoformat(),
            'sources': df['source'].value_counts().to_dict(),
            'amount_stats': {
                'total': float(df['amount'].sum()),
                'mean': float(df['amount'].mean()),
                'median': float(df['amount'].median()),
                'std': float(df['amount'].std())
            }
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
