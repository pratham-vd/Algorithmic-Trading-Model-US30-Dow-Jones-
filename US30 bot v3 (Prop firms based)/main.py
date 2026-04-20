import MetaTrader5 as mt5
import time
import config
from utils import get_ist_time, get_seconds_until_target, print_status
from execution import place_pending_orders, monitor_and_manage

def main():
    print_status("US30 Strategic Execution Engine Initializing...")
    

    print_status("Establishing Connection to MetaTrader 5 Terminal...")
    if not mt5.initialize():
        print_status(f"Startup Failed: MT5 initialize() failed, error={mt5.last_error()}")
        return


    print_status("Authenticating Trading Account...")
    authorized = mt5.login(login=config.MT5_LOGIN, password=config.MT5_PASSWORD, server=config.MT5_SERVER)
    
    if authorized:
        print_status(f"Account Authorized: {config.MT5_LOGIN}")
    else:
        print_status(f"Login Failed: Error Code = {mt5.last_error()}")
        return


    account = mt5.account_info()
    if not account:
        print_status("[WARN] Connection Warning: Could not retrieve account info. Ensure Terminal is logged in.")

    else:
        print_status(f"[INFO] Connected to Account: {account.login}, Equity: {account.equity}")
        print_status(f"[INFO] Using MANUAL_ACCOUNT_SIZE: {config.MANUAL_ACCOUNT_SIZE} (Risk: {config.RISK_PERCENT}%)")


    while True:
        seconds_left = get_seconds_until_target(
            config.TARGET_HOUR_IST, 
            config.TARGET_MINUTE_IST, 
            config.TARGET_SECOND_IST, 
            config.TRIGGER_OFFSET_SECONDS
        )
        
        hours = int(seconds_left // 3600)
        minutes = int((seconds_left % 3600) // 60)
        
        print_status(f"Targeted Execution Time: {config.TARGET_HOUR_IST}:{config.TARGET_MINUTE_IST:02d} IST (Time Remaining: {hours} hours {minutes} mins)")
        

        while seconds_left > 0.1:
            time.sleep(1) # Check every second to be safe and responsive to interrupts
            seconds_left = get_seconds_until_target(
                config.TARGET_HOUR_IST, 
                config.TARGET_MINUTE_IST, 
                config.TARGET_SECOND_IST, 
                config.TRIGGER_OFFSET_SECONDS
            )

        

        # print_status("Trigger Time Reached. Initiating Strategy...")
        orders, buy_entry, sell_entry = place_pending_orders()
        
        if orders:
            # print_status(f"Orders Placed: {orders}")
            try:
                monitor_and_manage(orders, buy_entry, sell_entry)
            except Exception as e:
                print_status(f"Monitoring Failed: {e}")
                # For now just log it.
            print_status("Strategy Execution Complete for today.")

            print_status("Waiting for next cycle...")
            time.sleep(60) # Prevent double trigger
        else:
            print_status("Order Placement Failed.")
            time.sleep(60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_status("Bot stopped by user.")
        mt5.shutdown()
