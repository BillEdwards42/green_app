"""
ML Inference Service for Carbon Intensity Forecasting
Handles model loading, preprocessing, and predictions
"""
import os
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
import pickle
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class MLInferenceService:
    def __init__(self, models_dir: str = None):
        if models_dir is None:
            # Use absolute path based on script location
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.models_dir = os.path.join(base_dir, "data", "models")
        else:
            self.models_dir = models_dir
        self.models = {}
        self.scalers = {}
        self.regions = ['North', 'Central', 'South', 'East', 'Other']
        self.fuel_columns = ['Nuclear', 'Coal', 'Co-Gen', 'IPP-Coal', 'LNG', 'IPP-LNG',
                            'Oil', 'Diesel', 'Hydro', 'Wind', 'Solar', 'Other_Renewable']
        self._load_models()
        self._initialize_scalers()
    
    def _load_models(self):
        """Load all regional models"""
        for region in self.regions:
            model_path = os.path.join(self.models_dir, f'model_{region.lower()}.h5')
            if os.path.exists(model_path):
                try:
                    # Load with custom objects for compatibility
                    custom_objects = {
                        'mse': tf.keras.losses.MeanSquaredError(),
                        'mae': tf.keras.losses.MeanAbsoluteError()
                    }
                    self.models[region] = tf.keras.models.load_model(model_path, custom_objects=custom_objects)
                    print(f"Loaded model for {region} region")
                except Exception as e:
                    print(f"Error loading model for {region}: {e}")
                    self.models[region] = None
            else:
                print(f"Model not found for {region} at {model_path}")
                self.models[region] = None
    
    def _initialize_scalers(self):
        """Initialize scalers for each region - will be fitted on first use"""
        scaler_cache_path = "cache/scalers.pkl"
        
        if os.path.exists(scaler_cache_path):
            try:
                with open(scaler_cache_path, 'rb') as f:
                    self.scalers = pickle.load(f)
                print("Loaded existing scalers from cache")
            except Exception as e:
                print(f"Error loading scalers: {e}. Creating new ones.")
                self._create_new_scalers()
        else:
            self._create_new_scalers()
    
    def _create_new_scalers(self):
        """Create new scalers for each region"""
        for region in self.regions:
            self.scalers[region] = {
                'X': StandardScaler(),
                'y': StandardScaler(),
                'fitted': False
            }
    
    def _save_scalers(self):
        """Save fitted scalers to cache"""
        os.makedirs("cache", exist_ok=True)
        with open("cache/scalers.pkl", 'wb') as f:
            pickle.dump(self.scalers, f)
    
    def preprocess_data(self, cache_data: List[Dict], region: str) -> Optional[np.ndarray]:
        """
        Preprocess cached data for model input
        Matches the preprocessing from training script
        """
        if not cache_data or len(cache_data) != 6:
            print(f"Insufficient cache data for {region}: {len(cache_data) if cache_data else 0}/6")
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(cache_data)
        
        # Extract datetime features from Timestamp
        if 'Timestamp' in df.columns:
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['Year'] = df['Timestamp'].dt.year
            df['Month'] = df['Timestamp'].dt.month
            df['Day'] = df['Timestamp'].dt.day
            df['DayOfWeek'] = df['Timestamp'].dt.dayofweek
            df['Hour'] = df['Timestamp'].dt.hour
            df['Minute'] = df['Timestamp'].dt.minute
            
            # Drop Timestamp column
            df = df.drop('Timestamp', axis=1)
        
        # Define expected features based on region
        if region == 'Other':
            # Other region doesn't have weather features
            expected_features = self.fuel_columns + ['Year', 'Month', 'Day', 'DayOfWeek', 'Hour', 'Minute']
            # Remove weather columns if present
            weather_columns = ['AirTemperature', 'WindSpeed', 'SunshineDuration', 'Precipitation']
            for col in weather_columns:
                if col in df.columns:
                    df = df.drop(col, axis=1)
        else:
            # North, South, Central, East have weather features
            expected_features = self.fuel_columns + ['AirTemperature', 'WindSpeed', 'SunshineDuration', 'Precipitation',
                                                    'Year', 'Month', 'Day', 'DayOfWeek', 'Hour', 'Minute']
        
        # Drop Total_Generation if present (we predict individual fuels)
        if 'Total_Generation' in df.columns:
            df = df.drop('Total_Generation', axis=1)
        
        # Remove Storage column if present (new models don't predict it)
        if 'Storage' in df.columns:
            df = df.drop('Storage', axis=1)
        
        # Drop cache_timestamp if present
        if 'cache_timestamp' in df.columns:
            df = df.drop('cache_timestamp', axis=1)
        
        # Separate fuel columns and feature columns
        fuel_cols_in_df = [col for col in self.fuel_columns if col in df.columns]
        feature_cols_in_df = [col for col in df.columns if col not in self.fuel_columns]
        
        # Create ordered column list based on model expectations
        if region == 'Other':
            # Other: fuels + time features (no weather)
            ordered_columns = fuel_cols_in_df + ['Year', 'Month', 'Day', 'DayOfWeek', 'Hour', 'Minute']
        else:
            # Others: fuels + weather + time features
            ordered_columns = fuel_cols_in_df + ['AirTemperature', 'WindSpeed', 'SunshineDuration', 'Precipitation',
                                                'Year', 'Month', 'Day', 'DayOfWeek', 'Hour', 'Minute']
        
        # Ensure all expected columns are present
        for col in ordered_columns:
            if col not in df.columns:
                df[col] = 0  # Fill missing columns with 0
        
        # Reorder columns to match training
        df = df[ordered_columns]
        
        # Convert to numpy array
        features = df.values  # Shape: (6, n_features)
        
        # Scale features
        n_features = features.shape[1]
        
        if not self.scalers[region]['fitted']:
            # Fit scaler on first use
            self.scalers[region]['X'].fit(features.reshape(-1, n_features))
            
            # Fit y scaler on fuel columns only (assuming similar range)
            fuel_data = df[self.fuel_columns].values
            self.scalers[region]['y'].fit(fuel_data.reshape(-1, len(self.fuel_columns)))
            
            self.scalers[region]['fitted'] = True
            self._save_scalers()
        
        # Transform features
        features_scaled = self.scalers[region]['X'].transform(features.reshape(-1, n_features))
        features_scaled = features_scaled.reshape(1, 6, n_features)  # Shape: (1, 6, n_features)
        
        return features_scaled
    
    def predict_region(self, cache_data: List[Dict], region: str) -> Optional[np.ndarray]:
        """
        Make predictions for a single region
        Returns array of shape (144, 12) for 144 timesteps, 12 fuel types
        """
        if region not in self.models or self.models[region] is None:
            print(f"No model available for {region}")
            return None
        
        # Preprocess data
        features = self.preprocess_data(cache_data, region)
        if features is None:
            return None
        
        try:
            # Make prediction
            predictions_scaled = self.models[region].predict(features, verbose=0)
            
            # Reshape and inverse transform
            predictions_reshaped = predictions_scaled.reshape(-1, len(self.fuel_columns))
            predictions = self.scalers[region]['y'].inverse_transform(predictions_reshaped)
            predictions = predictions.reshape(144, len(self.fuel_columns))
            
            # Ensure non-negative values
            predictions = np.maximum(predictions, 0)
            
            return predictions
            
        except Exception as e:
            print(f"Error making prediction for {region}: {e}")
            return None
    
    def predict_all_regions(self, cache_manager) -> Dict[str, np.ndarray]:
        """
        Make predictions for all regions
        Returns dictionary with regional predictions
        """
        predictions = {}
        
        for region in self.regions:
            cache_data = cache_manager.get_region_cache(region)
            if cache_data and len(cache_data) == 6:
                region_predictions = self.predict_region(cache_data, region)
                if region_predictions is not None:
                    predictions[region] = region_predictions
                    print(f"Generated predictions for {region}: shape {region_predictions.shape}")
                else:
                    print(f"Failed to generate predictions for {region}")
            else:
                print(f"Insufficient cache data for {region}")
        
        return predictions
    
    def get_model_status(self) -> Dict[str, bool]:
        """Get status of loaded models"""
        return {region: (model is not None) for region, model in self.models.items()}