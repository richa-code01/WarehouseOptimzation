import time
from datetime import datetime
from swiggy_problem.config import Config
from swiggy_problem.data_loader import DataLoader
from swiggy_problem.picklist_builder import PicklistBuilder
from swiggy_problem.scheduler import Scheduler
from swiggy_problem.utils import save_results, print_metrics

def run_optimization_engine(input_file: str):
    perf_start = time.time()
    
    # Load data
    try:
        df, base_date = DataLoader.load_and_clean(input_file)
    except FileNotFoundError:
        print("Input file not found.")
        return

    # Set start time (9 PM on base date)
    start_time = datetime.combine(base_date, datetime.strptime(Config.GLOBAL_START_TIME_STR, "%H:%M").time())
    
    # Build picklists
    print("Building optimal picklists...")
    builder = PicklistBuilder(df, start_time)
    picklists = builder.generate_picklists()
    print(f"Generated {len(picklists)} potential picklists.")
    
    # Schedule pickers
    print("Assigning to pickers...")
    pickers = Scheduler.create_pickers(base_date)
    assignments, wasted = Scheduler.assign_picklists(picklists, pickers, start_time)
    
    print(f"Successfully assigned: {len(assignments)}")
    print_metrics(assignments, wasted, base_date, perf_start)
    
    # Save results
    save_results(assignments, base_date)

if __name__ == "__main__":
    run_optimization_engine("input.csv")
