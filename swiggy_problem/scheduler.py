import heapq
from datetime import datetime, timedelta, date
from typing import List
from .config import Config
from .core_logic import LogicCore

class Scheduler:
    @staticmethod
    def create_pickers(base_date: date):
        pickers = []
        pid = 1
        for shift_name, start_s, end_s, count, day_offset in Config.SHIFTS:

            start_dt = datetime.combine(base_date + timedelta(days=day_offset), datetime.strptime(start_s, "%H:%M").time())
            end_dt = datetime.combine(base_date + timedelta(days=day_offset), datetime.strptime(end_s, "%H:%M").time())
            
            # Handle overnight shifts
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            
            for _ in range(count):
                # Using a heap to always pick the earliest available picker
                heapq.heappush(pickers, (start_dt, f"{shift_name}_{pid}", end_dt))
                pid += 1
        return pickers

    @staticmethod
    def build_picker_shifts(base_date: date):
        picker_windows = {}
        pid = 1
        for shift_name, start_s, end_s, count, day_offset in Config.SHIFTS:

            start_dt = datetime.combine(base_date + timedelta(days=day_offset), datetime.strptime(start_s, "%H:%M").time())
            end_dt = datetime.combine(base_date + timedelta(days=day_offset), datetime.strptime(end_s, "%H:%M").time())
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)

            for _ in range(count):
                picker_windows[f"{shift_name}_{pid}"] = (start_dt, end_dt)
                pid += 1
        return picker_windows

    @staticmethod
    def assign_picklists(picklists: List[dict], pickers: list, global_op_start_time: datetime):
        assignments = []
        unassigned = []
        split_counter = 1
        
        idx = 0
        while idx < len(picklists):
            pl = picklists[idx]
            assigned = False
            
            while pickers:
                avail_time, pid, shift_end = heapq.heappop(pickers)
                
                # Determine start time
                start_time = max(avail_time, global_op_start_time)
                
                finish_time = start_time + timedelta(seconds=pl['duration_sec'])
                remaining_shift = (shift_end - start_time).total_seconds()
                
                # Check 1: Does it fit in shift
                if finish_time > shift_end:
                    # split picklist to use remaining shift
                    if remaining_shift > 0:
                        truncated = Scheduler._truncate_picklist_to_time(pl['items'], remaining_shift)
                        if truncated:
                            partial_duration = LogicCore.estimate_picklist_duration(truncated)
                            partial_finish = start_time + timedelta(seconds=partial_duration)
                            partial_deadline = min(i['abs_cutoff'] for i in truncated if 'abs_cutoff')
                            
                            # Deadline check for partial
                            if partial_finish <= partial_deadline:
                                assignments.append({
                                    "picklist_no": f"{pl['picklist_no']}_S{split_counter}",
                                    "picker_id": pid,
                                    "start_time": start_time,
                                    "end_time": partial_finish,
                                    "duration_sec": partial_duration,
                                    "items": truncated,
                                    "status": "OnTime"
                                })
                                heapq.heappush(pickers, (partial_finish, pid, shift_end))
                                
                                # Build remainder and requeue
                                remainder_items = Scheduler._build_remainder(pl['items'], truncated)
                                if remainder_items:
                                    remainder = Scheduler._rebuild_picklist(pl, remainder_items, suffix=split_counter)
                                    # Insert remainder to keep ordering
                                    picklists.insert(idx + 1, remainder)
                                    
                                split_counter += 1
                                assigned = True
                                break
                    # Shift done -> drop this picker for this picklist
                    continue
                
                # Check 2: Deadline
                if finish_time <= pl['deadline']:
                    assignments.append({
                        "picklist_no": pl['picklist_no'],
                        "picker_id": pid,
                        "start_time": start_time,
                        "end_time": finish_time,
                        "duration_sec": pl['duration_sec'],
                        "items": pl['items'],
                        "status": "OnTime"
                    })
                    heapq.heappush(pickers, (finish_time, pid, shift_end))
                    assigned = True
                    break
                else:
                    assignments.append({
                        "picklist_no": pl['picklist_no'],
                        "picker_id": pid,
                        "start_time": start_time,
                        "end_time": finish_time,
                        "duration_sec": pl['duration_sec'],
                        "items": pl['items'],
                        "status": "Late"
                    })
                    heapq.heappush(pickers, (finish_time, pid, shift_end))
                    assigned = True
                    break
            
            # Restore popped pickers that were skipped due to shift end
            if not assigned:
                unassigned.append(pl)
            
            idx += 1
            
        return assignments, unassigned

    @staticmethod
    def _truncate_picklist_to_time(items, max_seconds):
        """
        Greedily take items until duration exceeds max_seconds.
        """
        subset = []
        for item in items:
            subset.append(item)
            if LogicCore.estimate_picklist_duration(subset) > max_seconds:
                subset.pop()
                break
        return subset

    @staticmethod
    def _build_remainder(original_items, taken_items):
        # Simple diff based on some ID or object identity if possible.
        # Since items are dicts, we can use a unique key or just list slicing if order preserved.
        # Order is preserved.
        taken_count = len(taken_items)
        return original_items[taken_count:]

    @staticmethod
    def _rebuild_picklist(original_pl, items, suffix):
        duration = LogicCore.estimate_picklist_duration(items)
        # Recalculate deadline
        deadline = min(i['abs_cutoff'] for i in items)
        return {
            "picklist_no": f"{original_pl['picklist_no']}_R{suffix}",
            "zone": original_pl['zone'],
            "type": original_pl['type'],
            "items": items,
            "duration_sec": duration,
            "deadline": deadline,
            "total_units": sum(i['picked_qty'] for i in items),
            "store_count": len(set(i['store_id'] for i in items))
        }
