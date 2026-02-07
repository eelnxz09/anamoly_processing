"""
Anomaly Detection ML Models
Implements Isolation Forest and One-Class SVM for transaction anomaly detection
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from typing import Dict, List, Tuple, Optional
import joblib
import json
from datetime import datetime
from pathlib import Path


class AnomalyDetector:
    """
    Multi-model anomaly detection system for financial transactions
    """
    
    def __init__(self, model_type: str = 'isolation_forest', contamination: float = 0.1):
        """
        Initialize anomaly detector
        
        Args:
            model_type: 'isolation_forest' or 'one_class_svm'
            contamination: Expected proportion of anomalies in dataset
        """
        self.model_type = model_type
        self.contamination = contamination
        self.scaler = RobustScaler()  # More robust to outliers than StandardScaler
        self.pca = None
        self.model = None
        self.feature_names = []
        self.is_trained = False
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize the selected ML model"""
        if self.model_type == 'isolation_forest':
            self.model = IsolationForest(
                contamination=self.contamination,
                n_estimators=200,
                max_samples='auto',
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'one_class_svm':
            self.model = OneClassSVM(
                kernel='rbf',
                gamma='auto',
                nu=self.contamination
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract and engineer features from transaction data
        
        Features extracted:
        - Transaction amount statistics
        - Time-based features
        - Frequency patterns
        - Behavioral patterns
        """
        features = pd.DataFrame()
        
        # Amount features
        features['amount'] = df['amount']
        features['amount_log'] = np.log1p(df['amount'])
        
        # Time features
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            features['hour'] = df['timestamp'].dt.hour
            features['day_of_week'] = df['timestamp'].dt.dayofweek
            features['day_of_month'] = df['timestamp'].dt.day
            features['is_weekend'] = (df['timestamp'].dt.dayofweek >= 5).astype(int)
            features['is_night'] = ((df['timestamp'].dt.hour >= 22) | (df['timestamp'].dt.hour <= 6)).astype(int)
        
        # User-level aggregations
        if 'user_id' in df.columns:
            user_stats = df.groupby('user_id')['amount'].agg(['mean', 'std', 'count']).reset_index()
            user_stats.columns = ['user_id', 'user_avg_amount', 'user_std_amount', 'user_tx_count']
            df = df.merge(user_stats, on='user_id', how='left')
            
            features['user_avg_amount'] = df['user_avg_amount']
            features['user_std_amount'] = df['user_std_amount'].fillna(0)
            features['user_tx_count'] = df['user_tx_count']
            features['amount_vs_user_avg'] = df['amount'] / (df['user_avg_amount'] + 1e-5)
        
        # Merchant/category features
        if 'merchant_category' in df.columns:
            features['merchant_category_encoded'] = pd.Categorical(df['merchant_category']).codes
        
        # Location features
        if 'location' in df.columns:
            features['location_encoded'] = pd.Categorical(df['location']).codes
        
        # Device features
        if 'device_type' in df.columns:
            features['device_type_encoded'] = pd.Categorical(df['device_type']).codes
        
        # Fill NaN values
        features = features.fillna(0)
        
        self.feature_names = features.columns.tolist()
        return features
    
    def train(self, df: pd.DataFrame, use_pca: bool = False, n_components: int = 10):
        """
        Train the anomaly detection model
        
        Args:
            df: Transaction dataframe
            use_pca: Whether to apply PCA for dimensionality reduction
            n_components: Number of PCA components
        """
        # Extract features
        X = self.extract_features(df)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Optional PCA
        if use_pca and X_scaled.shape[1] > n_components:
            self.pca = PCA(n_components=n_components, random_state=42)
            X_scaled = self.pca.fit_transform(X_scaled)
        
        # Train model
        self.model.fit(X_scaled)
        self.is_trained = True
        
        print(f"✓ Model trained on {len(X)} transactions with {X_scaled.shape[1]} features")
    
    def predict(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Predict anomalies and calculate risk scores
        
        Returns:
            Dictionary with predictions, scores, and risk levels
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before prediction")
        
        # Extract features
        X = self.extract_features(df)
        X_scaled = self.scaler.transform(X)
        
        if self.pca is not None:
            X_scaled = self.pca.transform(X_scaled)
        
        # Get predictions (-1 for anomaly, 1 for normal)
        predictions = self.model.predict(X_scaled)
        
        # Get anomaly scores (more negative = more anomalous)
        if hasattr(self.model, 'decision_function'):
            scores = self.model.decision_function(X_scaled)
        else:
            scores = self.model.score_samples(X_scaled)
        
        # Convert to risk scores (0-100, higher = riskier)
        risk_scores = self._calculate_risk_scores(scores, predictions)
        
        # Determine risk levels
        risk_levels = self._calculate_risk_levels(risk_scores)
        
        # Calculate confidence
        confidence = self._calculate_confidence(scores)
        
        return {
            'predictions': predictions,
            'anomaly_scores': scores,
            'risk_scores': risk_scores,
            'risk_levels': risk_levels,
            'confidence': confidence,
            'is_anomaly': predictions == -1
        }
    
    def _calculate_risk_scores(self, scores: np.ndarray, predictions: np.ndarray) -> np.ndarray:
        """Convert anomaly scores to 0-100 risk scores"""
        # Normalize scores to 0-100 range
        min_score, max_score = scores.min(), scores.max()
        
        if max_score == min_score:
            normalized = np.zeros_like(scores)
        else:
            # Invert so lower anomaly score = higher risk
            normalized = 100 * (max_score - scores) / (max_score - min_score)
        
        # Boost scores for predicted anomalies
        risk_scores = np.where(predictions == -1, 
                              np.clip(normalized * 1.2, 0, 100),
                              np.clip(normalized * 0.8, 0, 100))
        
        return risk_scores
    
    def _calculate_risk_levels(self, risk_scores: np.ndarray) -> np.ndarray:
        """Categorize risk scores into levels"""
        levels = np.empty(len(risk_scores), dtype=object)
        levels[risk_scores < 30] = 'Low'
        levels[(risk_scores >= 30) & (risk_scores < 60)] = 'Medium'
        levels[(risk_scores >= 60) & (risk_scores < 85)] = 'High'
        levels[risk_scores >= 85] = 'Critical'
        return levels
    
    def _calculate_confidence(self, scores: np.ndarray) -> np.ndarray:
        """Calculate prediction confidence (0-100)"""
        # Use distance from decision boundary as confidence proxy
        abs_scores = np.abs(scores)
        min_abs, max_abs = abs_scores.min(), abs_scores.max()
        
        if max_abs == min_abs:
            return np.full_like(scores, 50.0)
        
        confidence = 100 * (abs_scores - min_abs) / (max_abs - min_abs)
        return confidence
    
    def explain_prediction(self, df: pd.DataFrame, index: int) -> Dict:
        """
        Explain why a specific transaction was flagged
        
        Args:
            df: Transaction dataframe
            index: Index of transaction to explain
            
        Returns:
            Dictionary with explanation details
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before explanation")
        
        # Extract features for this transaction
        X = self.extract_features(df)
        transaction_features = X.iloc[index]
        
        # Get predictions
        results = self.predict(df.iloc[[index]])
        
        # Analyze feature contributions
        feature_importance = {}
        for feat_name, feat_value in transaction_features.items():
            # Calculate how unusual this feature value is
            all_values = X[feat_name]
            percentile = (all_values < feat_value).sum() / len(all_values) * 100
            
            # Flag extreme values
            if percentile < 5 or percentile > 95:
                feature_importance[feat_name] = {
                    'value': float(feat_value),
                    'percentile': float(percentile),
                    'unusual': True
                }
        
        return {
            'risk_score': float(results['risk_scores'][0]),
            'risk_level': results['risk_levels'][0],
            'confidence': float(results['confidence'][0]),
            'is_anomaly': bool(results['is_anomaly'][0]),
            'unusual_features': feature_importance,
            'top_reasons': self._generate_explanation_text(feature_importance, results)
        }
    
    def _generate_explanation_text(self, feature_importance: Dict, results: Dict) -> List[str]:
        """Generate human-readable explanation"""
        reasons = []
        
        # Sort by how unusual
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]['percentile'] - 50),
            reverse=True
        )
        
        for feat_name, feat_info in sorted_features[:3]:
            if feat_info['percentile'] > 95:
                reasons.append(f"Unusually high {feat_name.replace('_', ' ')} (top 5%)")
            elif feat_info['percentile'] < 5:
                reasons.append(f"Unusually low {feat_name.replace('_', ' ')} (bottom 5%)")
        
        if not reasons:
            reasons.append("Multiple minor deviations from normal behavior")
        
        return reasons
    
    def save(self, path: str):
        """Save model to disk"""
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'pca': self.pca,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'contamination': self.contamination,
            'is_trained': self.is_trained
        }
        joblib.dump(model_data, path)
        print(f"✓ Model saved to {path}")
    
    @classmethod
    def load(cls, path: str):
        """Load model from disk"""
        model_data = joblib.load(path)
        
        detector = cls(
            model_type=model_data['model_type'],
            contamination=model_data['contamination']
        )
        detector.model = model_data['model']
        detector.scaler = model_data['scaler']
        detector.pca = model_data['pca']
        detector.feature_names = model_data['feature_names']
        detector.is_trained = model_data['is_trained']
        
        print(f"✓ Model loaded from {path}")
        return detector


class EnsembleDetector:
    """
    Ensemble of multiple anomaly detection models for higher accuracy
    """
    
    def __init__(self, contamination: float = 0.1):
        self.models = [
            AnomalyDetector('isolation_forest', contamination),
            AnomalyDetector('one_class_svm', contamination)
        ]
        self.weights = [0.6, 0.4]  # IF gets more weight
    
    def train(self, df: pd.DataFrame):
        """Train all models in ensemble"""
        for model in self.models:
            model.train(df)
    
    def predict(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Ensemble prediction with weighted voting"""
        all_predictions = []
        all_scores = []
        
        for model, weight in zip(self.models, self.weights):
            results = model.predict(df)
            all_predictions.append(results['risk_scores'] * weight)
            all_scores.append(results['anomaly_scores'])
        
        # Weighted average of risk scores
        ensemble_risk_scores = np.sum(all_predictions, axis=0)
        
        # Ensemble anomaly scores (average)
        ensemble_anomaly_scores = np.mean(all_scores, axis=0)
        
        # Recalculate levels and confidence
        risk_levels = self.models[0]._calculate_risk_levels(ensemble_risk_scores)
        confidence = self.models[0]._calculate_confidence(ensemble_anomaly_scores)
        
        return {
            'predictions': (ensemble_risk_scores > 60).astype(int) * -1 + (ensemble_risk_scores <= 60).astype(int),
            'anomaly_scores': ensemble_anomaly_scores,
            'risk_scores': ensemble_risk_scores,
            'risk_levels': risk_levels,
            'confidence': confidence,
            'is_anomaly': ensemble_risk_scores > 60
        }
