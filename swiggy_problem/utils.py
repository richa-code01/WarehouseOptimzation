import os
import pandas as pd
import numpy as np
from statistics import median
from .scheduler import Scheduler
from .config import Config
import time
from datetime import datetime, timedelta

def save_results(assignments, base_date):
    os.makedirs("output/picklists", exist_ok=True) 
    summary_rows = []
    
    for job in assignments:
        pl_no = job['picklist_no']
        items = job['items']
        
        # 1. Detail File
        detail_df = pd.DataFrame(items)
        
        # Ensure required columns exist
        out_cols = ['sku', 'store_id', 'bin', 'bin_rank']
        if 'bin' not in detail_df.columns:
            detail_df['bin'] = detail_df.get('bin_rank', detail_df.get('bin_rank', 0))
            
        detail_df = detail_df[[c for c in out_cols if c in detail_df.columns]].copy()
        rename_map = {'sku': 'SKU', 'store_id': 'Store', 'bin': 'Bin', 'bin_rank': 'Bin Rank'}
        detail_df = detail_df.rename(columns=rename_map)
        
        # Reorder columns
        ordered = [c for c in ['SKU', 'Store', 'Bin', 'Bin Rank'] if c in detail_df.columns]
        detail_df = detail_df[ordered]
        
        fname = f"output/picklists/{base_date}_{pl_no}.csv"
        detail_df.to_csv(fname, index=False)
        
        # 2. Summary Row
        skus = set(i['sku'] for i in items)
        zone = items[0]['zone'] if items else ''
        
        # Determine type
        if zone in Config.FRAGILE_ZONES:
            pl_type = "fragile"
        elif len(skus) == 1:
            pl_type = "bulk"
        else:
            pl_type = "multi order"
        
        stores = sorted(list(set(i['store_id'] for i in items)))
        
        summary_rows.append({
            "Picklist_date": base_date,
            "picklist_no": pl_no,
            "picklist_type": pl_type,
            "stores_in_picklist": ",".join(map(str, stores))
        })
    
    pd.DataFrame(summary_rows).to_csv("output/Summary.csv", index=False)
    print("Output generated in /output folder.")


def print_metrics(assignments, unassigned, base_date, perf_start=None):
    print("\n" + "-"*25)
    print("Evaluation Metrics")
    print("-"*25)
    
    # 1. Total units successfully picked before cutoff (Primary)
    total_units_picked = sum(sum(i['order_qty'] for i in a['items']) for a in assignments)
    total_units_available = total_units_picked + sum(sum(i['order_qty'] for i in u['items']) for u in unassigned)
    percentage = (total_units_picked / total_units_available * 100) if total_units_available > 0 else 0
    print(f"1. Total units successfully picked before cutoff: {total_units_picked:,} / {total_units_available:,} ({percentage:.1f}%)")
    
    # 2. Number of Completed Orders (Secondary)
    total_demand = {}
    picked_demand = {}
    
    # Calculate total demand
    for pl in assignments + unassigned:
        for item in pl['items']:
            oid = item['order_id']
            qty = item['order_qty']
            total_demand[oid] = total_demand.get(oid, 0) + qty
            
    # Calculate picked demand
    for pl in assignments:
        for item in pl['items']:
            oid = item['order_id']
            qty = item['order_qty']
            picked_demand[oid] = picked_demand.get(oid, 0) + qty
            
    completed_orders = 0
    for oid, total in total_demand.items():
        if picked_demand.get(oid, 0) >= total:
            completed_orders += 1
            
    print(f"2. Number of Completed Orders: {completed_orders:,} / {len(total_demand):,}")
    
    # 3. Wasted picking effort (late picklists)
    wasted_effort_sec = sum(a['duration_sec'] for a in assignments if a.get('status') != 'OnTime')
    print(f"3. Wasted picking effort (late picklists): {wasted_effort_sec:.2f} sec")
    
    # 4. Picker utilization
    total_worked_sec = sum(a['duration_sec'] for a in assignments)
    
    total_capacity_sec = 0
    for shift in Config.SHIFTS:
        start_s = shift[1]
        end_s = shift[2]
        count = shift[3]
        
        s = datetime.strptime(start_s, "%H:%M")
        e = datetime.strptime(end_s, "%H:%M")
        if e <= s:
            e += timedelta(days=1)
        duration = (e - s).total_seconds()
        total_capacity_sec += duration * count
        
    utilization = (total_worked_sec / total_capacity_sec * 100) if total_capacity_sec > 0 else 0
    print(f"4. Picker utilization: {utilization:.2f}%")
    
    # 5. Scalability and runtime
    runtime = time.time() - perf_start if perf_start else 0
    print(f"5. Scalability and runtime: {runtime:.2f} sec")
    print("="*40 + "\n")
