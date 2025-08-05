"""
Carbon Calculator for Green Moment
Calculates carbon intensity from generation data using emission factors
"""
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os


class CarbonCalculator:
    def __init__(self):
        # Emission factors in kgCO2e/kWh
        # NOTE: Storage is excluded from calculations as it doesn't generate electricity
        self.emission_factors = {
            'Nuclear': 0,
            'Coal': 0.912,
            'Co-Gen': 1.111,
            'IPP-Coal': 0.91,
            'LNG': 0.389,
            'IPP-LNG': 0.378,
            'Oil': 0.818,
            'Diesel': 0.79,
            'Hydro': 0,
            'Wind': 0,
            'Solar': 0,
            'Other_Renewable': 0.176
        }
        
        # Fuel columns used for calculations (excludes Storage)
        self.fuel_columns = list(self.emission_factors.keys())
        
        # All fuel columns including Storage (for data reading)
        self.all_fuel_columns = self.fuel_columns + ['Storage']
    
    def calculate_current_intensity(self, regional_data: Dict[str, pd.DataFrame]) -> Tuple[float, Dict[str, float]]:
        """
        Calculate current national carbon intensity from latest generation data
        
        Args:
            regional_data: Dictionary of DataFrames with regional generation data
            
        Returns:
            Tuple of (national_intensity, details_dict)
        """
        total_generation_mw = 0
        total_emissions_kg = 0
        fuel_totals_mw = {fuel: 0 for fuel in self.fuel_columns}
        storage_mw = 0  # Track Storage separately
        
        # Initialize calculation log
        calc_log = {
            'timestamp': datetime.now().isoformat(),
            'fuel_details': {},
            'calculation_steps': []
        }
        
        # Sum generation across all regions
        for region, df in regional_data.items():
            if df.empty:
                print(f"Warning: No data for {region} region")
                continue
                
            # Get latest row
            latest_data = df.iloc[-1]
            
            # Process all fuel types (including Storage for logging)
            for fuel in self.all_fuel_columns:
                if fuel in latest_data:
                    generation_mw = float(latest_data[fuel])
                    if not pd.isna(generation_mw) and generation_mw >= 0:
                        # Only add to fuel_totals_mw if it's a calculation fuel (not Storage)
                        if fuel in self.fuel_columns:
                            fuel_totals_mw[fuel] += generation_mw
                            total_generation_mw += generation_mw
                        elif fuel == 'Storage':
                            storage_mw += generation_mw
                        
                        # Add regional breakdown to log (excluding Storage from calculations)
                        if fuel != 'Storage':  # Exclude Storage from calculation logs
                            if 'regional_breakdown' not in calc_log:
                                calc_log['regional_breakdown'] = {}
                            if region not in calc_log['regional_breakdown']:
                                calc_log['regional_breakdown'][region] = {}
                            calc_log['regional_breakdown'][region][fuel] = round(generation_mw, 2)
        
        # Calculate emissions for each fuel type
        fuel_emissions = {}
        for fuel, generation_mw in fuel_totals_mw.items():
            # Convert MW to kW: MW * 1000
            generation_kw = generation_mw * 1000
            emissions_kg = generation_kw * self.emission_factors[fuel]
            fuel_emissions[fuel] = emissions_kg
            total_emissions_kg += emissions_kg
            
            # Add to calculation log
            if generation_mw > 0:
                calc_log['fuel_details'][fuel] = {
                    'generation_mw': round(generation_mw, 2),
                    'conversion': f"{generation_mw:.2f} MW × 1000 = {generation_kw:.2f} kW",
                    'generation_kw': round(generation_kw, 2),
                    'emission_factor': self.emission_factors[fuel],
                    'emissions_calculation': f"{generation_kw:.2f} kW × {self.emission_factors[fuel]} = {emissions_kg:.2f} kg CO2e",
                    'emissions_kg': round(emissions_kg, 2)
                }
        
        # Add Storage to log as excluded
        if storage_mw > 0:
            storage_kw = storage_mw * 1000
            calc_log['fuel_details']['Storage'] = {
                'generation_mw': round(storage_mw, 2),
                'conversion': f"{storage_mw:.2f} MW × 1000 = {storage_kw:.2f} kW",
                'generation_kw': round(storage_kw, 2),
                'emission_factor': 0,
                'emissions_calculation': "EXCLUDED FROM CALCULATIONS",
                'emissions_kg': 0,
                'note': 'Storage is excluded from carbon intensity calculations'
            }
        
        # Calculate carbon intensity
        if total_generation_mw > 0:
            total_generation_kw = total_generation_mw * 1000
            carbon_intensity = total_emissions_kg / total_generation_kw
            
            # Add summary to log
            calc_log['summary'] = {
                'total_generation_mw': round(total_generation_mw, 2),
                'total_generation_kw': round(total_generation_kw, 2),
                'total_emissions_kg': round(total_emissions_kg, 2),
                'carbon_intensity_kg_per_kw': round(carbon_intensity, 6),
                'carbon_intensity_g_per_kw': round(carbon_intensity * 1000, 1),
                'calculation': f"{total_emissions_kg:.2f} kg CO2e ÷ {total_generation_kw:.2f} kW = {carbon_intensity:.6f} kg/kW = {carbon_intensity * 1000:.1f} g/kW",
                'storage_mw': round(storage_mw, 2),
                'note': 'Storage excluded from total generation for carbon intensity calculation'
            }
            
            # Save calculation log (replace previous)
            log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "carbon_calculation_log.json")
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, 'w') as f:
                json.dump(calc_log, f, indent=2)
        else:
            carbon_intensity = 0
            calc_log['error'] = "No generation data available"
        
        details = {
            'total_generation_mw': total_generation_mw,
            'total_generation_kw': total_generation_mw * 1000,
            'total_emissions_kg': total_emissions_kg,
            'carbon_intensity_kgco2_kw': carbon_intensity,
            'fuel_generation_mw': fuel_totals_mw,
            'fuel_emissions_kg': fuel_emissions,
            'storage_mw': storage_mw
        }
        
        return carbon_intensity, details
    
    def calculate_forecast_intensity(self, forecast_data: Dict[str, np.ndarray]) -> List[float]:
        """
        Calculate carbon intensity for 24-hour forecast
        
        Args:
            forecast_data: Dictionary with regional forecasts
                          {region: array of shape (144, 12)}
                          
        Returns:
            List of 144 carbon intensity values (kgCO2e/kWh)
        """
        forecast_intensities = []
        
        # Process each of the 144 time steps
        for t in range(144):
            total_generation_mw = 0
            total_emissions_kg = 0
            
            # Sum across all regions for this timestep
            for region, predictions in forecast_data.items():
                if predictions is None:
                    continue
                    
                # Get predictions for this timestep
                timestep_predictions = predictions[t, :]  # Shape: (12,) for 12 fuel types
                
                # Handle both 12 and 13 fuel predictions
                n_predicted_fuels = len(timestep_predictions)
                for i, fuel in enumerate(self.fuel_columns):
                    if i >= n_predicted_fuels:
                        # Skip fuels not in predictions (e.g., Storage)
                        continue
                    generation_mw = float(timestep_predictions[i])
                    if generation_mw > 0:  # Ignore negative predictions
                        total_generation_mw += generation_mw
                        
                        # Convert to kW and calculate emissions
                        generation_kw = generation_mw * 1000
                        emissions_kg = generation_kw * self.emission_factors[fuel]
                        total_emissions_kg += emissions_kg
            
            # Calculate intensity for this timestep
            if total_generation_mw > 0:
                total_generation_kw = total_generation_mw * 1000
                carbon_intensity = total_emissions_kg / total_generation_kw
            else:
                carbon_intensity = 0
                
            forecast_intensities.append(carbon_intensity)
        
        return forecast_intensities
    
    def get_generation_mix(self, regional_data: Dict[str, pd.DataFrame]) -> Dict[str, float]:
        """
        Get current generation mix as percentages
        """
        fuel_totals_mw = {fuel: 0 for fuel in self.fuel_columns}
        total_generation_mw = 0
        
        # Sum generation across all regions
        for region, df in regional_data.items():
            if df.empty:
                continue
                
            latest_data = df.iloc[-1]
            
            # Only process calculation fuels (excludes Storage)
            for fuel in self.fuel_columns:
                if fuel in latest_data:
                    generation_mw = float(latest_data[fuel])
                    if not pd.isna(generation_mw) and generation_mw >= 0:
                        fuel_totals_mw[fuel] += generation_mw
                        total_generation_mw += generation_mw
        
        # Calculate percentages
        generation_mix = {}
        if total_generation_mw > 0:
            for fuel, generation_mw in fuel_totals_mw.items():
                generation_mix[fuel] = (generation_mw / total_generation_mw) * 100
        
        return generation_mix