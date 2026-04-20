import datetime
import pytz
import sys

def get_ist_time():

    ist_zone = pytz.timezone('Asia/Kolkata')
    return datetime.datetime.now(ist_zone)

def get_seconds_until_target(target_hour, target_minute, target_second, offset_seconds):

    now = get_ist_time()
    target_time = now.replace(hour=target_hour, minute=target_minute, second=target_second, microsecond=0)
    
    trigger_time = target_time - datetime.timedelta(seconds=offset_seconds)
    
    threshold = datetime.timedelta(seconds=60)
    
    if now > (trigger_time + threshold):
        trigger_time += datetime.timedelta(days=1)
        
    delta = trigger_time - now
    return delta.total_seconds()


def print_status(message):
    print(f"{get_ist_time().strftime('%H:%M:%S')} | {message}")
    sys.stdout.flush()

def log_trade_to_csv(data_dict, filename="trade_history.csv"):
    import csv
    import os
    
    # Define the order of columns
    fieldnames = [
        "Time", "Ticket", "Type", 
        "Requested Entry", "Filled Entry", "Entry Spread", 
        "Original TP", "Original SL", 
        "Exit Price", "Exit Spread", "Exit Type", "Profit"
    ]
    
    file_exists = os.path.isfile(filename)
    
    try:
        with open(filename, mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerow(data_dict)
            print_status(f"Trade logged to {filename}")
    except Exception as e:
        print_status(f"[ERROR] Failed to log trade to CSV: {e}")
