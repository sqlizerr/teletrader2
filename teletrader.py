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
    # Initialize MT5 (retry if connection drops)
    def init_mt5():
        if not mt5.initialize():
            print("❌ MT5 Initialize Failed:", mt5.last_error())
            return False
        return True

    if not init_mt5():
        return None

    symbol = "XAUUSD"
    deviation = 20  # Max slippage
    last_valid_tick_time = 0  # Track freshest tick timestamp

    start_time = time.time()
    price_entered_range = False

    while time.time() - start_time <= timeout_sec:
        # Refresh MT5 connection every 30 sec to avoid stale data
        if int(time.time() - start_time) % 30 == 0:
            mt5.shutdown()
            if not init_mt5():
                break

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print("⚠️ No tick data. Retrying...")
            time.sleep(0.1)
            continue

        # Skip stale ticks (older than 2 seconds)
        current_time_msc = int(time.time() * 1000)
        if (current_time_msc - tick.time_msc) > 2000:
            print(f"⚠️ Stale tick (Age: {current_time_msc - tick.time_msc}ms). Skipping...")
            time.sleep(0.05)
            continue

        price = tick.ask
        print(f"Price: {price} (Range: {elow}-{ehigh}) | Time Left: {int(timeout_sec - (time.time() - start_time))}s")

        # Dynamic timeout extension if price is "close" to range
        # if abs(price - elow) < 1.0 or abs(price - ehigh) < 1.0:
        #     timeout_sec += 10  # Add 10 sec if nearing range

        # Execute if price is in range
        if elow <= price <= ehigh:
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
                "comment": "xauusd BUY (Auto-Triggered)",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,  # Allow partial fills
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ BUY Executed! Ticket: {result.order}")
                mt5.shutdown()
                return result
            else:
                print(f"❌ Order Failed: {getattr(result, 'comment', 'No response')}")

        time.sleep(0.05)  # Check 20x/sec

    print("⚠️ Timeout: Price never entered range.")
    mt5.shutdown()
    return None

    
def place_sell(lot: float, sl: float, tp: float,elow:float,ehigh:float,timeout_sec: int =300):
    # Initialize MT5 (retry if connection drops)
    def init_mt5():
        if not mt5.initialize():
            print("❌ MT5 Initialize Failed:", mt5.last_error())
            return False
        return True

    if not init_mt5():
        return None

    symbol = "XAUUSD"
    deviation = 20  # Max slippage
    last_valid_tick_time = 0  # Track freshest tick timestamp

    start_time = time.time()
    price_entered_range = False

    while time.time() - start_time <= timeout_sec:
        # Refresh MT5 connection every 30 sec to avoid stale data
        if int(time.time() - start_time) % 30 == 0:
            mt5.shutdown()
            if not init_mt5():
                break

        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print("⚠️ No tick data. Retrying...")
            time.sleep(0.1)
            continue

        # Skip stale ticks (older than 2 seconds)
        current_time_msc = int(time.time() * 1000)
        if (current_time_msc - tick.time_msc) > 2000:
            print(f"⚠️ Stale tick (Age: {current_time_msc - tick.time_msc}ms). Skipping...")
            time.sleep(0.05)
            continue

        price = tick.bid
        print(f"Price: {price} (Range: {elow}-{ehigh}) | Time Left: {int(timeout_sec - (time.time() - start_time))}s")

        # Dynamic timeout extension if price is "close" to range
        # if abs(price - elow) < 1.0 or abs(price - ehigh) < 1.0:
        #     timeout_sec += 10  # Add 10 sec if nearing range

        # Execute if price is in range
        if elow <= price <= ehigh:
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
                "comment": "xauusd SELL (Auto-Triggered)",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,  # Allow partial fills
            }

            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ BUY Executed! Ticket: {result.order}")
                mt5.shutdown()
                return result
            else:
                print(f"❌ Order Failed: {getattr(result, 'comment', 'No response')}")

        time.sleep(0.05)  # Check 20x/sec

    print("⚠️ Timeout: Price never entered range.")
    mt5.shutdown()
    return None
    
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
        entry_high = max(float(entry_match_buy.group(1)),float(entry_match_buy.group(2)))
        entry_low = min(float(entry_match_buy.group(1)),float(entry_match_buy.group(2)))
        sl = float(sl_match.group(1))
        tp = float(tp1_match.group(1))
        print("Buy call detected\n")
        result = place_buy(lot= 0.2, sl=sl,tp=tp,elow=entry_low,ehigh=entry_high)

        if(result is not None):
            print(result.retcode)
        elif(result is None):
            print("Failed to execute BUY!\n")

    elif((entry_match_buy is None) and entry_match_sell):
        entry_high = max(float(entry_match_sell.group(1)),float(entry_match_sell.group(2)))
        entry_low = min(float(entry_match_sell.group(1)),float(entry_match_sell.group(2)))
        sl = float(sl_match.group(1))
        tp = float(tp1_match.group(1))
        print("Sell call detected\n")
        result = place_sell(lot=0.2,sl=sl,tp=tp,elow=entry_low,ehigh=entry_high)

        if(result is not None):
            print(result.retcode)
        elif(result is None):
            print("Failed to execute SELL!\n")

    elif((entry_match_buy is None) and entry_match_sell is None):
        print("No call detected\n")

    print(entry_low)
    print(entry_high)
    print(sl)
    print(tp)
    # print(entry_match_buy)
    # print(entry_match_sell)
    # Parse message and call trading logic
        

async def main():
    while True:
        await client.start()
        await client.run_until_disconnected()

asyncio.run(main())