"""
Cache Manager for Carbon Intensity Generator
Manages rolling 6-timestep cache for ML model input
"""
import pickle
import os
from collections import deque
from datetime import datetime
from typing import Dict, Optional, Any
import pandas as pd


class CacheManager:
    def __init__(self, cache_path: str = "cache/generation_cache.pkl"):
        self.cache_path = cache_path
        self.cache_data = self._load_cache()
        self.regions = ['North', 'Central', 'South', 'East', 'Other']  # Islands excluded - separate grid
        
    def _load_cache(self) -> Dict[str, deque]:
        """Load existing cache or create new one"""
        if os.path.exists(self.cache_path):
            try:
                with open(self.cache_path, 'rb') as f:
                    cache = pickle.load(f)
                print(f"Loaded existing cache from {self.cache_path}")
                return cache
            except Exception as e:
                print(f"Error loading cache: {e}. Creating new cache.")
        
        # Create new cache with deques of max length 6
        cache = {
            'North': deque(maxlen=6),
            'Central': deque(maxlen=6),
            'South': deque(maxlen=6),
            'East': deque(maxlen=6),
            'Other': deque(maxlen=6),
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'last_update': None,
                'total_updates': 0
            }
        }
        return cache
    
    def add_timestep_data(self, timestamp: str, regional_data: Dict[str, Any]):
        """Add new timestep data to cache for all regions"""
        self.cache_data['metadata']['last_update'] = datetime.now().isoformat()
        self.cache_data['metadata']['total_updates'] += 1
        
        for region in self.regions:
            if region in regional_data:
                # Handle both DataFrame and dict inputs
                if isinstance(regional_data[region], pd.DataFrame):
                    # Extract the last row of data (most recent)
                    latest_data = regional_data[region].iloc[-1].to_dict()
                elif isinstance(regional_data[region], dict):
                    # Already a dict, use as is
                    latest_data = regional_data[region].copy()
                else:
                    print(f"Warning: Unexpected data type for {region}")
                    continue
                
                latest_data['cache_timestamp'] = timestamp
                
                # Add to deque (automatically removes oldest if at capacity)
                self.cache_data[region].append(latest_data)
                print(f"Added data for {region}: {len(self.cache_data[region])}/6 timesteps cached")
            else:
                print(f"Warning: No data available for {region} region")
        
        self._save_cache()
    
    def get_region_cache(self, region: str) -> Optional[list]:
        """Get cached data for a specific region"""
        if region in self.cache_data and len(self.cache_data[region]) > 0:
            return list(self.cache_data[region])
        return None
    
    def is_cache_ready(self) -> bool:
        """Check if all regions have 6 timesteps cached"""
        for region in self.regions:
            if region not in self.cache_data or len(self.cache_data[region]) < 6:
                return False
        return True
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get detailed cache status"""
        status = {
            'ready': self.is_cache_ready(),
            'regions': {},
            'metadata': self.cache_data.get('metadata', {})
        }
        
        for region in self.regions:
            if region in self.cache_data:
                status['regions'][region] = {
                    'count': len(self.cache_data[region]),
                    'ready': len(self.cache_data[region]) == 6
                }
            else:
                status['regions'][region] = {
                    'count': 0,
                    'ready': False
                }
        
        return status
    
    def _save_cache(self):
        """Save cache to pickle file"""
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        with open(self.cache_path, 'wb') as f:
            pickle.dump(self.cache_data, f)
        print(f"Cache saved to {self.cache_path}")
    
    def clear_cache(self):
        """Clear all cached data"""
        for region in self.regions:
            if region in self.cache_data:
                self.cache_data[region].clear()
        self.cache_data['metadata']['last_update'] = datetime.now().isoformat()
        self._save_cache()
        print("Cache cleared")
    
    def get_ml_input_data(self, region: str) -> Optional[pd.DataFrame]:
        """Get cached data formatted for ML model input"""
        cache = self.get_region_cache(region)
        if not cache or len(cache) < 6:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(cache)
        
        # Ensure proper ordering (oldest to newest)
        # The deque maintains order, so this should already be correct
        return df