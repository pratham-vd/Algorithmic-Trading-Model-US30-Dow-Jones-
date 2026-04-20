import MetaTrader5 as mt5
import config

def calculate_position_size(entry_price, sl_price, account_info, risk_percent=config.RISK_PERCENT, suppress_log=False):
    account_balance = account_info.balance
    risk_amount = account_balance * (risk_percent / 100.0)
    
    # Calculate distance in points
    symbol_info = mt5.symbol_info(config.SYMBOL)
    if not symbol_info:
        print(f"Failed to get symbol info for {config.SYMBOL}")
        return 0.01

    tick_size = symbol_info.trade_tick_size
    tick_value = symbol_info.trade_tick_value
    contract_size = symbol_info.trade_contract_size
    

    if tick_size == 0 or tick_value == 0:
        print(f"Error: Symbol {config.SYMBOL} has zero tick size or value.")
        return 0.01


    price_diff = abs(entry_price - sl_price)
    

    loss_per_lot = (price_diff / tick_size) * tick_value
    
    if loss_per_lot == 0:
        return 0.01

    lot_size = risk_amount / loss_per_lot
    

    step = symbol_info.volume_step
    lot_size = round(lot_size / step) * step
    

    lot_size = max(lot_size, symbol_info.volume_min)
    lot_size = min(lot_size, symbol_info.volume_max)
    
    # --- MARGIN CHECK LOGIC ---
    # Calculate margin required for 1 lot
    margin_for_one_lot = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, config.SYMBOL, 1.0, entry_price)
    
    if margin_for_one_lot is None:
         print(f"Error: Could not calculate margin for {config.SYMBOL}. error={mt5.last_error()}")
         # Fallback: if we can't calculate margin, we just proceed with risk-based (or could return min)
         return round(lot_size, 2)
         
    if margin_for_one_lot > 0:
        max_lot_by_margin = (account_info.margin_free * config.MARGIN_BUFFER) / margin_for_one_lot
        
        # Round down to step
        max_lot_by_margin = int(max_lot_by_margin / step) * step
        
        if lot_size > max_lot_by_margin:
            if not suppress_log:
                print(f"[MARGIN ALERT] Risk-based Lot ({lot_size}) exceeds Margin Limit ({max_lot_by_margin:.2f}). Reducing to {max_lot_by_margin:.2f}")
            lot_size = max_lot_by_margin
            
    # Ensure we are still within min/max after margin check
    lot_size = max(lot_size, symbol_info.volume_min)
    lot_size = min(lot_size, symbol_info.volume_max)
    
    return round(lot_size, 2)
