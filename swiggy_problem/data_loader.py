import pandas as pd
from datetime import datetime, timedelta
from .config import Config

class DataLoader:
    @staticmethod
    def load_and_clean(filepath: str):
        print(f"Loading data from {filepath}...")
        df = pd.read_csv(filepath)
        
        # Normalize columns
        df.columns = [c.lower().strip() for c in df.columns]
        
        # Clean data
        df['weight_in_grams'] = df['weight_in_grams'].fillna(0).astype(float)
        df['dt'] = pd.to_datetime(df['dt'])
        base_date = datetime(2025, 8, 12).date()
        
        # Calculate Cutoffs
        df['abs_cutoff'] = df.apply(DataLoader._get_absolute_cutoff, axis=1)
        
        return df, base_date

    @staticmethod
    def _get_absolute_cutoff(row):
        prio = row.get('pod_priority', 'P9')
        time_str = Config.CUTOFF_MAP.get(prio, "11:00")
        
        cutoff_time = datetime.strptime(time_str, "%H:%M").time()
        order_dt = row['dt']
        base_date = order_dt.date()

        cutoff_dt = datetime.combine(base_date, cutoff_time)

        # Move early-morning cutoffs to the next day and ensure we never set a cutoff behind order time
        if cutoff_time.hour < 12 or cutoff_dt <= order_dt:
            cutoff_dt += timedelta(days=1)

        return cutoff_dt
