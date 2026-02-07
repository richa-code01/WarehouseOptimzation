import time
from datetime import datetime
from optimization_problem.config import Config
from optimization_problem.data_loader import DataLoader
from optimization_problem.parallel_engine import ScalableOptimizationEngine
from optimization_problem.scheduler import Scheduler
from optimization_problem.utils import save_results, print_metrics


def run_distributed_optimization_engine(input_file: str):
    perf_start = time.time()

    try:
        df, base_date = DataLoader.load_and_clean(input_file)
    except FileNotFoundError:
        print(f"Input file not found: {input_file}")
        return

    start_time = datetime.combine(base_date, datetime.strptime(Config.GLOBAL_START_TIME_STR, "%H:%M").time())

    print("Initiating scalable optimization engine...")
    engine = ScalableOptimizationEngine()
    picklists = engine.run_parallel_build(df, start_time)
    print(f"Generated {len(picklists)} candidate picklists.")

    print("Assigning to pickers...")
    pickers = Scheduler.create_pickers(base_date)
    assignments, wasted = Scheduler.assign_picklists(picklists, pickers, start_time)

    print(f"Successfully assigned: {len(assignments)}")
    print_metrics(assignments, wasted, base_date, perf_start)
    save_results(assignments, base_date)


if __name__ == "__main__":
    run_distributed_optimization_engine("input.csv")
