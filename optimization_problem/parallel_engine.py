import multiprocessing
import pandas as pd
from datetime import datetime
from typing import List
from .picklist_builder import PicklistBuilder
from .core_logic import ATCScoringStrategy


class ScalableOptimizationEngine:
    def __init__(self, n_workers: int = None):
        self.n_workers = n_workers or multiprocessing.cpu_count()

    def run_parallel_build(self, df: pd.DataFrame, start_time: datetime) -> List[dict]:
        zones = df['zone'].unique()
        tasks = []

        for zone in zones:
            zone_df = df[df['zone'] == zone].copy()
            tasks.append((zone_df, start_time))

        print(f"Parallelizing optimization across {len(zones)} zones using {self.n_workers} workers...")

        with multiprocessing.Pool(self.n_workers) as pool:
            results = pool.starmap(self._process_zone, tasks)

        return [pl for zone_results in results for pl in zone_results]

    @staticmethod
    def _process_zone(zone_df: pd.DataFrame, start_time: datetime) -> List[dict]:
        builder = PicklistBuilder(zone_df, start_time, strategy=ATCScoringStrategy())
        return builder.generate_picklists()
