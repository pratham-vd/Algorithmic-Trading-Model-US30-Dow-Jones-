import MetaTrader5 as mt5
import time
import config
from risk import calculate_position_size
from utils import print_status, log_trade_to_csv

def place_pending_orders():

    if not mt5.initialize():
        print_status("[ERROR] MT5 Initialization Failed during order placement, error code =", mt5.last_error())
        return None

    tick = mt5.symbol_info_tick(config.SYMBOL)
    if tick is None:
        print_status(f"[ERROR] Failed to retrieve tick data for {config.SYMBOL}")
        return None
        
    current_price = tick.ask 
    ref_price = tick.last if tick.last > 0 else (tick.bid + tick.ask) / 2
    ref_price = tick.last if tick.last > 0 else (tick.bid + tick.ask) / 2
    
    # Calculate Levels

    
    buy_entry = ref_price + config.PIPS_DISTANCE
    sell_entry = ref_price - config.PIPS_DISTANCE
    
    # Calculate SL/TP
    # Buy Order
    buy_sl = sell_entry
    buy_tp = buy_entry + config.TP_PIPS
    
    # Sell Order
    sell_sl = buy_entry
    sell_tp = sell_entry - config.TP_PIPS
    
    # Calculate Position Size
    account_info = mt5.account_info()
    if not account_info:
        print_status("[ERROR] Failed to retrieve account information for sizing.")
        return None
        
    # equity = account_info.equity  <-- No longer needed independently
    
    # Pass the full account_info object
    buy_lot = calculate_position_size(buy_entry, buy_sl, account_info)
    sell_lot = calculate_position_size(sell_entry, sell_sl, account_info, suppress_log=True)
    
    print_status(f"Ref: {ref_price:.1f} | Buy Stop: {buy_entry:.1f} (Lot: {buy_lot}) | Sell Stop: {sell_entry:.1f} (Lot: {sell_lot})")

    # Send Orders
    
    orders = []
    
    # Buy Request
    buy_request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": config.SYMBOL,
        "volume": buy_lot,
        "type": mt5.ORDER_TYPE_BUY_STOP, 
        "price": buy_entry,
        "sl": buy_sl,
        "tp": buy_tp,
        "magic": config.MAGIC_NUMBER,
        "comment": "US30 Straddle Buy",
        "type_time": mt5.ORDER_TIME_DAY, 
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    # Sell Request
    sell_request = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": config.SYMBOL,
        "volume": sell_lot,
        "type": mt5.ORDER_TYPE_SELL_STOP,
        "price": sell_entry,
        "sl": sell_sl,
        "tp": sell_tp,
        "magic": config.MAGIC_NUMBER,
        "comment": "US30 Straddle Sell",
        "type_time": mt5.ORDER_TIME_DAY,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    
    # Execute
    res_buy = mt5.order_send(buy_request)
    if res_buy.retcode != mt5.TRADE_RETCODE_DONE:
        print_status(f"Buy Order Failed: {res_buy.comment}")
    else:
        orders.append(res_buy.order)
        # print_status(f"[SUCCESS] Buy Order Submitted Successfully: Ticket {res_buy.order}")

    res_sell = mt5.order_send(sell_request)
    if res_sell.retcode != mt5.TRADE_RETCODE_DONE:
        print_status(f"Sell Order Failed: {res_sell.comment}")
    else:
        orders.append(res_sell.order)
        # print_status(f"[SUCCESS] Sell Order Submitted Successfully: Ticket {res_sell.order}")
        
    return orders, buy_entry, sell_entry

def monitor_and_manage(order_tickets, buy_entry_price, sell_entry_price):

    if not order_tickets:
        return

    print_status("Monitoring for Order Execution...")
    
    # Phase 1: Monitor for Entry
    active_position_ticket = None
    position_type = None # 0 for Buy, 1 for Sell
    
    while True:
        # Check status of orders
        triggered_order = None
        
        positions = mt5.positions_get(symbol=config.SYMBOL)
        if positions:
            for pos in positions:
                if pos.magic == config.MAGIC_NUMBER:
                    triggered_order = pos.ticket
                    active_position_ticket = pos.ticket
                    position_type = pos.type
                    
                    # --- SPREAD CALCULATION (ENTRY) ---
                    requested_price = buy_entry_price if pos.type == mt5.ORDER_TYPE_BUY else sell_entry_price
                    filled_price = pos.price_open
                    spread = abs(filled_price - requested_price)
                    
                    p_type_str = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"
                    print_status(f"=== ENTRY EXECUTION REPORT ===")
                    print_status(f"Type: {p_type_str}")
                    print_status(f"Stop Order Price: {requested_price:.5f}")
                    print_status(f"Executed Price:   {filled_price:.5f}")
                    print_status(f"Entry Spread:     {spread:.5f}")
                    print_status(f"==============================")
                    # ----------------------------------
                    
                    print_status(f"Pending Order Triggered! Position Active (Ticket: {pos.ticket})")
                    break
        
        if triggered_order:
            orders = mt5.orders_get(symbol=config.SYMBOL)
            if orders:
                for o in orders:
                    if o.magic == config.MAGIC_NUMBER:
                        print_status(f"Cancelling Opposing Pending Order: {o.ticket}")
                        req = {
                            "action": mt5.TRADE_ACTION_REMOVE,
                            "order": o.ticket,
                        }
                        mt5.order_send(req)
            break
        
        time.sleep(0.5)

    # Phase 2: Monitor for Exit
    if active_position_ticket:
        print_status(f"Monitoring Position {active_position_ticket} for Exit...")
        
        # Capture initial TP/SL from the active position for reference
        # We need to loop briefly to ensure we get the position details if they update securely
        # But commonly the position object from the previous loop 'pos' is a snapshot. 
        # Let's get a fresh snapshot.
        pos_snapshot_list = mt5.positions_get(ticket=active_position_ticket)
        initial_sl = 0.0
        initial_tp = 0.0
        
        if pos_snapshot_list:
             initial_sl = pos_snapshot_list[0].sl
             initial_tp = pos_snapshot_list[0].tp
             print_status(f"Targeting -> TP: {initial_tp:.5f} | SL: {initial_sl:.5f}")

        # Wait for position to close
        while True:
            # Check if position still exists
            active_pos = mt5.positions_get(ticket=active_position_ticket)
            if not active_pos:
                # Position is gone, it has closed.
                print_status("Position Closed. Calculating Exit Spreads...")
                break
            time.sleep(1)
            
        # --- SPREAD CALCULATION (EXIT) ---
        # Retrieve history to find the dealing entry out
        # We look back quite a bit to be safe, e.g., last 24 hours or just specific ticket if possible.
        # history_deals_get can filter by position ticket.
        
        deals = mt5.history_deals_get(position=active_position_ticket)
        
        if deals:
            # Find the exit deal (ENTRY_OUT)
            exit_deal = None
            for d in deals:
                if d.entry == mt5.DEAL_ENTRY_OUT:
                    exit_deal = d
                    break
            
            if exit_deal:
                exit_price = exit_deal.price
                
                # Determine which level was hit (roughly)
                # We calculate spreads for both just in case, or Exit Spread vs closest level.
                
                diff_sl = abs(exit_price - initial_sl) if initial_sl > 0 else 0
                diff_tp = abs(exit_price - initial_tp) if initial_tp > 0 else 0
                
                exit_type = "UNKNOWN"
                exit_spread = 0.0
                
                # Heuristic to say which one was likely hit
                if initial_tp > 0 and initial_sl > 0:
                    if diff_tp < diff_sl:
                        print_status(f"Result: Likely TP Hit (Slippage: {diff_tp:.5f})")
                        exit_type = "TP"
                        exit_spread = diff_tp
                    else:
                        print_status(f"Result: Likely SL Hit (Slippage: {diff_sl:.5f})")
                        exit_type = "SL"
                        exit_spread = diff_sl
                elif initial_tp > 0:
                     print_status(f"TP Slippage: {diff_tp:.5f}")
                     exit_type = "TP"
                     exit_spread = diff_tp
                elif initial_sl > 0:
                     print_status(f"SL Slippage: {diff_sl:.5f}")
                     exit_type = "SL"
                     exit_spread = diff_sl
                     
                print_status(f"Profit: {exit_deal.profit}")
                print_status(f"=============================")
                
                # --- LOG TO CSV ---
                import datetime
                trade_data = {
                    "Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Ticket": active_position_ticket,
                    "Type": "BUY" if position_type == mt5.ORDER_TYPE_BUY else "SELL",
                    "Requested Entry": f"{requested_price:.5f}", # captured from entry phase
                    "Filled Entry": f"{filled_price:.5f}",       # captured from entry phase
                    "Entry Spread": f"{spread:.5f}",             # captured from entry phase
                    "Original TP": f"{initial_tp:.5f}",
                    "Original SL": f"{initial_sl:.5f}",
                    "Exit Price": f"{exit_price:.5f}",
                    "Exit Spread": f"{exit_spread:.5f}",
                    "Exit Type": exit_type,
                    "Profit": exit_deal.profit
                }
                log_trade_to_csv(trade_data, filename="trade_history.csv")
                # ------------------
                
            else:
                 print_status("[WARN] Could not find Exit Deal for spread calculation.")
        else:
            print_status("[WARN] Could not retrieve deal history for position.")
