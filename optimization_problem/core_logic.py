from abc import ABC, abstractmethod
import math
from datetime import datetime
from typing import Dict, List
from .config import Config


class ScoringStrategy(ABC):
    @abstractmethod
    def calculate_score(self, item: Dict, current_time: datetime) -> float:
        pass


class ATCScoringStrategy(ScoringStrategy):
    def calculate_score(self, item: Dict, current_time: datetime) -> float:
        qty = item['order_qty']

        process_time = Config.TIME_BIN_TO_BIN + (qty * Config.TIME_PICK_PER_UNIT)
        pick_density = qty / process_time

        time_until_cutoff = (item['abs_cutoff'] - current_time).total_seconds()
        overhead = Config.TIME_START_TO_ZONE + Config.TIME_ZONE_TO_STAGING
        slack = (time_until_cutoff - process_time - overhead)

        if slack < 0:
            return 0.0

        exponent = - (max(slack, 0)) / Config.ATC_K
        urgency = math.exp(exponent)

        return pick_density * urgency


class LogicCore:
    @staticmethod
    def estimate_picklist_duration(items: List[dict]) -> float:
        if not items:
            return 0.0

        unique_bins = set(i.get('bin_rank', 0) for i in items)
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
