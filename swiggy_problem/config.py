class Config:
    # Constraints
    MAX_ITEMS_PER_PICKLIST = 2000
    MAX_WEIGHT_STD = 200_000  # 200kg
    MAX_WEIGHT_FRAGILE = 50_000  # 50kg
    FRAGILE_ZONES = {"FRAGILE_FD"}
    
    # Time Estimates (Seconds)
    TIME_START_TO_ZONE = 120
    TIME_BIN_TO_BIN = 30
    TIME_PICK_PER_UNIT = 5
    TIME_ZONE_TO_STAGING = 120
    TIME_UNLOAD_PER_ORDER = 30
    
    # ATC Lookahead Factor
    ATC_K = 2.0 
    
    # Shift Definitions: (Name, Start, End, Count, DayOffset)
    SHIFTS = [
        ("Night_1", "20:00", "05:00", 45, 0),
        ("Night_2", "21:00", "07:00", 35, 0),
        ("Morning", "08:00", "17:00", 40, 1),
        ("General", "10:00", "19:00", 30, 1),
    ]

    # Priority Cutoffs
    CUTOFF_MAP = {
        "P1": "23:30", "P2": "02:00", "P3": "04:00",
        "P4": "06:00", "P5": "07:00", "P6": "09:00", "P9": "11:00"
    }
    
    GLOBAL_START_TIME_STR = "21:00"
