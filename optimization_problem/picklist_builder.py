import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional
from collections import defaultdict
from .config import Config
from .core_logic import LogicCore, ScoringStrategy, ATCScoringStrategy


class PicklistBuilder:
    def __init__(self, df: pd.DataFrame, start_time: datetime, strategy: Optional[ScoringStrategy] = None):
        self.df = df
        self.current_time = start_time
        self.strategy = strategy or ATCScoringStrategy()

    def generate_picklists(self) -> List[dict]:
        picklists = []
        pl_counter = 1
        
        # 1. Partition by Zone
        grouped = self.df.groupby(['zone'])
        
        for zone, group_df in grouped:
            # Convert to list of dicts
            items_pool = group_df.to_dict('records')
            
            # Track remaining qty for each (order_id, sku) pair
            remaining = defaultdict(int)
            order_remaining_qty = defaultdict(int)
            for item in items_pool:
                key = (item['order_id'], item['sku'])
                remaining[key] += item['order_qty']
                order_remaining_qty[item['order_id']] += item['order_qty']
            
            max_weight = Config.MAX_WEIGHT_FRAGILE if zone in Config.FRAGILE_ZONES else Config.MAX_WEIGHT_STD
            
            while any(qty > 0 for qty in remaining.values()):
                # Step 1: Score Items
                available_items = []
                for item in items_pool:
                    key = (item['order_id'], item['sku'])
                    remaining_qty = remaining[key]
                    if remaining_qty > 0:
                        item_for_score = {**item, 'order_qty': remaining_qty}
                        atc_score = self.strategy.calculate_score(item_for_score, self.current_time)
                        
                        # Check if picking this item completes the order
                        is_completing = (order_remaining_qty[item['order_id']] == remaining_qty)
                        
                        available_items.append({
                            **item_for_score, 
                            'atc_score': atc_score,
                            'is_completing': is_completing
                        })
                
                if not available_items:
                    break
                
                # Sort: ATC Score (Desc), Is Completing (Desc), Floor (Asc), Aisle (Asc), Rack (Asc), Bin Rank (Asc)
                available_items.sort(key=lambda x: (
                    -x['atc_score'], 
                    -int(x['is_completing']),
                    str(x.get('floor', '')), 
                    str(x.get('aisle', '')), 
                    str(x.get('rack', '')), 
                    x.get('bin_rank', 0)
                ))
                
                # Step 2: Seed Selection
                seed = available_items[0]
                seed_key = (seed['order_id'], seed['sku'])
                
                # Calculate max pickable quantity
                max_qty_by_weight = max_qty_by_limit = Config.MAX_ITEMS_PER_PICKLIST
                if seed['weight_in_grams'] > 0:
                    max_qty_by_weight = max_weight // seed['weight_in_grams']
                
                seed_qty = min(remaining[seed_key], max_qty_by_limit, max_qty_by_weight)
                
                if seed_qty <= 0:
                    remaining[seed_key] = 0
                    continue
                
                current_picklist_items = [{
                    **seed,
                    'order_qty': seed_qty,
                    'picked_qty': seed_qty
                }]
                remaining[seed_key] -= seed_qty
                order_remaining_qty[seed['order_id']] -= seed_qty
                
                # Track Picklist State
                current_weight = seed_qty * seed['weight_in_grams']
                current_units = seed_qty
                current_stores = {seed['store_id']}
                
                # Cutoff constraint
                min_cutoff = seed['abs_cutoff']
                max_pods = seed['pods_per_picklist_in_that_zone']
                
                # Step 3: Grow Picklist
                for item in available_items[1:]:
                    item_key = (item['order_id'], item['sku'])
                    if remaining[item_key] <= 0:
                        continue
                    
                    # Check store constraint
                    if len(current_stores) >= max_pods and item['store_id'] not in current_stores:
                        continue
                    
                    # Calculate max quantity
                    max_qty_by_weight = max_qty_by_items = Config.MAX_ITEMS_PER_PICKLIST - current_units
                    
                    if item['weight_in_grams'] > 0:
                        max_qty_by_weight = (max_weight - current_weight) // item['weight_in_grams']

                    pick_qty = min(remaining[item_key], max_qty_by_items, max_qty_by_weight)
                    
                    if pick_qty <= 0:
                        continue
                    
                    # Create item
                    picked_item = {
                        **item,
                        'order_qty': pick_qty,
                        'picked_qty': pick_qty
                    }
                    
                    # Time Validity Check
                    proposed_min_cutoff = min(min_cutoff, item['abs_cutoff'])
                    temp_picklist = current_picklist_items + [picked_item]
                    duration = LogicCore.estimate_picklist_duration(temp_picklist)
                    finish_time = self.current_time + timedelta(seconds=duration)
                    
                    if finish_time <= proposed_min_cutoff:
                        # Add item
                        current_picklist_items.append(picked_item)
                        current_weight += pick_qty * item['weight_in_grams']
                        current_units += pick_qty
                        current_stores.add(item['store_id'])
                        min_cutoff = proposed_min_cutoff
                        remaining[item_key] -= pick_qty
                        order_remaining_qty[item['order_id']] -= pick_qty
                
                # Finalize Picklist
                final_duration = LogicCore.estimate_picklist_duration(current_picklist_items)
                picklists.append({
                    "picklist_no": f"PL_{pl_counter:06d}",
                    "zone": zone,
                    "type": "Fragile" if zone in Config.FRAGILE_ZONES else "Standard",
                    "items": current_picklist_items,
                    "duration_sec": final_duration,
                    "deadline": min_cutoff,
                    "total_units": current_units,
                    "store_count": len(current_stores)
                })
                pl_counter += 1
                
        return picklists
