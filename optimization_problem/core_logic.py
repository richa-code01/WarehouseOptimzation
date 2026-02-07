import math
from datetime import datetime
from typing import List
from .config import Config

class LogicCore:
    @staticmethod
    def estimate_picklist_duration(items: List[dict]) -> float:
        if not items:
            return 0.0
            
        unique_bins = set(i['bin_rank'] for i in items)
        unique_orders = set(i['order_id'] for i in items)
        total_units = sum(i['order_qty'] for i in items)
        
        duration = (
            Config.TIME_START_TO_ZONE +
            (len(unique_bins) * Config.TIME_BIN_TO_BIN) +
            (total_units * Config.TIME_PICK_PER_UNIT) +
            (len(unique_orders) * Config.TIME_UNLOAD_PER_ORDER) +
            Config.TIME_ZONE_TO_STAGING
        )
        return duration

    @staticmethod
    def calculate_atc_score(item: dict, current_time: datetime) -> float:
        # Priority Score = Pick Density * Urgency

        # 1. SKU Qty
        qty = item['order_qty']
        
        # Processing Time: Walk + Pick
        process_time = Config.TIME_BIN_TO_BIN + (qty * Config.TIME_PICK_PER_UNIT)
        pick_density = qty / process_time
        
        # 2. Slack Term
        time_until_cutoff = (item['abs_cutoff'] - current_time).total_seconds()
        overhead = Config.TIME_START_TO_ZONE + Config.TIME_ZONE_TO_STAGING
        slack = (time_until_cutoff - process_time - overhead)

        # Normalize slack
        slack = slack / time_until_cutoff
        
        if slack < 0:
            return 0.0 
            
        exponent = - (max(slack, 0)) / Config.ATC_K
        urgency = math.exp(exponent)
        
        return pick_density * urgency
