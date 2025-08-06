from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path
import json
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


@router.get("/latest")
async def get_latest_carbon_data():
    """
    Get the latest carbon intensity (CO2e) data including current and 24hr forecast
    This endpoint serves the pre-generated JSON file
    """
    json_path = Path("data/carbon_intensity.json")
    
    if not json_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Carbon intensity data not available. Generator may be initializing."
        )
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Add cache headers to allow 10-minute caching
        return data
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading carbon intensity (CO2e) data: {str(e)}"
        )


@router.get("/current")
async def get_current_intensity():
    """Get only the current carbon intensity"""
    json_path = Path("data/carbon_intensity.json")
    
    if not json_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Carbon intensity data not available"
        )
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if 'current_intensity' in data and data['current_intensity']:
            return data['current_intensity']
        else:
            raise HTTPException(
                status_code=503,
                detail="Current carbon intensity not available"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading carbon intensity (CO2e) data: {str(e)}"
        )


@router.get("/forecast")
async def get_forecast():
    """Get only the 24-hour carbon intensity forecast"""
    json_path = Path("data/carbon_intensity.json")
    
    if not json_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Carbon intensity data not available"
        )
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        if 'forecast' in data:
            return data['forecast']
        else:
            raise HTTPException(
                status_code=503,
                detail="Forecast data not available"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading carbon intensity (CO2e) data: {str(e)}"
        )


@router.get("/status")
async def get_generator_status():
    """Get the status of the carbon intensity generator"""
    json_path = Path("data/carbon_intensity.json")
    
    if not json_path.exists():
        return {
            "status": "not_initialized",
            "message": "Generator has not run yet"
        }
    
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        last_updated = datetime.fromisoformat(data['last_updated'])
        age_minutes = (datetime.now() - last_updated).total_seconds() / 60
        
        return {
            "status": "running" if age_minutes < 15 else "stale",
            "last_updated": data['last_updated'],
            "age_minutes": round(age_minutes, 1),
            "forecast_hours": len(data.get('forecast', [])),
            "current_intensity": data.get('current_intensity', {}).get('gCO2e_kWh', 0)
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }