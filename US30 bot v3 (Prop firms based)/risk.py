import MetaTrader5 as mt5
import config

def calculate_position_size(entry_price, sl_price, account_size, risk_percent=config.RISK_PERCENT):

    risk_amount = account_size * (risk_percent / 100.0)
    
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
    
    return round(lot_size, 2)
