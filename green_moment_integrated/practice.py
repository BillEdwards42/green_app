import pandas as pd
import numpy as np
import requests, re, pytz, time
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).parent
TEST_DIR = BASE_DIR / "test"

DEMAND_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/loadpara.json"
TAIWAN_TZ = pytz.timezone("Asia/Taipei")

def fetch_demand():
    timestamp_suffix = int(time.time())
    url = f"{DEMAND_URL}?_={timestamp_suffix}"
    try:
        resp = requests.get(url, timeout = 20)
        resp.raise_for_status()
        holder = resp.json()
        record_list = holder.get("records", [])
        if not record_list:
            print("No record list from requests to the url.\n")
            return None, None
        demand_str = record_list[0].get("curr_load")
        if not demand_str:
            print("No demand data in record list.\n")
            return None, None
        demand = float(demand_str.replace(",", "")) * 10
        
        dt = datetime.now(TAIWAN_TZ)
        updated_minute = (dt.minute//10)*10
        current_time = dt.replace(minute = updated_minute, second = 0, microsecond = 0)
        return demand, current_time
    
    except Exception as e:
        print(f"{e}")
        return None, None

def append_to_csv(demand, update_time):
    if demand:
        TEST_DIR.mkdir(parents = True, exist_ok = True)
        writing_path = TEST_DIR / "demand_record.csv"

        new_data_df = pd.DataFrame([{"TimeStamp": update_time, "Demand MW": demand}])
        new_data_df.to_csv(
            writing_path,
            mode = "a",
            header = not writing_path.exists(),
            index = False
        )
        print(f"The data for {update_time} is {int(demand)} MW, updated to {writing_path}.")
    else:
        print("Your fetching fetched none.")

    


if __name__ == "__main__":
    demand, update_time = fetch_demand()
    if not demand or not update_time:
        print(f"The demand or update time is false,\nupdate time: {update_time}\ndemand: {demand}")
    append_to_csv(demand, update_time)
