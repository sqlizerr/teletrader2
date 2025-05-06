from telethon import TelegramClient, events
import re
import asyncio
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import time

load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
channel_username = os.getenv('CHANNEL_USERNAME')  # Use @channel or ID



mt5.initialize()
mt5.login(os.getenv('MT_LOGIN'), password=os.getenv('MT_PASS'),server='OctaFX-Demo')

def place_buy(lot: float, sl: float, tp: float, elow: float, ehigh: float, timeout_sec: int = 300):
    # Initialize MT5
    if not mt5.initialize():
        print("Failed to initialize MT5:", mt5.last_error())
        return None

    # Check symbol availability
    symbol = "XAUUSD"
    if not mt5.symbol_select(symbol, True):
        print(f"Symbol {symbol} not found.")
        mt5.shutdown()
        return None

    start_time = time.time()
    deviation = 20  # Max acceptable slippage (adjust if needed)

    while True:
        # Break if timeout reached
        if time.time() - start_time > timeout_sec:
            print("Timeout: Price did not enter the range within", timeout_sec, "seconds.")
            mt5.shutdown()
            return None

        # Get current ask price
        tick = mt5.symbol_info_tick(symbol)
        price = tick.ask

        # Check if price is in range
        if (elow-1.0) <= price <= (ehigh-1.0):
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": deviation,
                "magic": 234000,
                "comment": "xauusd execute BUY (Triggered)",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            result = mt5.order_send(request)
            mt5.shutdown()
            return result

        # Wait before next check (avoid excessive API calls)
        time.sleep(1)  # Adjust sleep time as needed (e.g., 0.5s for faster checks)

    
def place_sell(lot: float, sl: float, tp: float,elow:float,ehigh:float,timeout_sec: int =300):
    # Initialize MT5
    if not mt5.initialize():
        print("Failed to initialize MT5:", mt5.last_error())
        return

    # Check if symbol is available/
    symbol = "XAUUSD"
    if not mt5.symbol_select(symbol, True):
        print(f"Symbol {symbol} not found.")
        mt5.shutdown()
        return
    
    start_time = time.time()
    deviation = 20

    while True:
        # Break if timeout reached
        if time.time() - start_time > timeout_sec:
            print("Timeout: Price did not enter the range within", timeout_sec, "seconds.")
            mt5.shutdown()
            return None

        # Get current ask price
        tick = mt5.symbol_info_tick(symbol)
        price = tick.bid

        # Check if price is in range
        if (elow-1.0) <= price <= (ehigh-1.0):
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": deviation,
                "magic": 234000,
                "comment": "xauusd execute SELL (Triggered)",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            result = mt5.order_send(request)
            mt5.shutdown()
            return result

        # Wait before next check (avoid excessive API calls)
        time.sleep(1)
    
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage(chats=channel_username))
async def handler(event):
    message = event.message.message
    print(f"Received: {message}")
    entry_match_buy = re.search(r'Buy Gold *@(\d+\.?\d*)-(\d+\.?\d*)', message, re.IGNORECASE)
    entry_match_sell = re.search(r'Sell Gold *@(\d+\.?\d*)-(\d+\.?\d*)', message, re.IGNORECASE)
    sl_match = re.search(r'Sl *: *(\d+\.?\d*)', message, re.IGNORECASE)
    tp1_match = re.search(r'Tp1 *: *(\d+\.?\d*)', message, re.IGNORECASE)


    if(entry_match_buy and (entry_match_sell is None)):
        entry_high = float(entry_match_buy.group(1))
        entry_low = float(entry_match_buy.group(2))
    elif((entry_match_buy is None) and entry_match_sell):
        entry_low = float(entry_match_sell.group(1))
        entry_high = float(entry_match_sell.group(2))
    sl = float(sl_match.group(1))
    tp = float(tp1_match.group(1))
    entry_price = round((entry_low + entry_high) / 2, 2)

    print(entry_low)
    print(entry_high)
    print(sl)
    print(tp)
    print(entry_price)
    # print(entry_match_buy)
    # print(entry_match_sell)
    # Parse message and call trading logic
    if((entry_match_buy is None) and entry_match_sell is None):
        print("No call detected\n")

    elif(entry_match_buy and (entry_match_sell is None)):
        print("Buy call detected\n")
        result = place_buy(lot= 0.1, sl=sl,tp=tp,elow=entry_low,ehigh=entry_high)

        if(result is not None):
            print(result.retcode)
        elif(result is None):
            print("Failed to execute BUY!\n")

    elif((entry_match_buy is None) and entry_match_sell):
        print("Sell call detected\n")
        result = place_sell(lot=0.1,sl=sl,tp=tp,elow=entry_low,ehigh=entry_high)

        if(result is not None):
            print(result.retcode)
        elif(result is None):
            print("Failed to execute SELL!\n")



async def main():
    while True:
        await client.start()
        await client.run_until_disconnected()

asyncio.run(main())