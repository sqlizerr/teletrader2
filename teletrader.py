from telethon import TelegramClient, events
import re
import asyncio
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv()

api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
channel_username = os.getenv('CHANNEL_USERNAME')  # Use @channel or ID



mt5.initialize()
mt5.login(os.getenv('MT_LOGIN'), password=os.getenv('MT_PASS'),server='OctaFX-Demo')

def place_buy(lot: float, sl: float, tp: float,elow:float,ehigh:float):
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

    # Create pending Buy Limit order
    point = mt5.symbol_info(symbol).point
    price = mt5.symbol_info_tick(symbol).ask
    deviation = 20
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
        "comment": "xauusd execute BUY",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Send order
    if(elow<price<ehigh):
        result = mt5.order_send(request)
    else:
        result = None
    # Handle result
    return result
    
def place_sell(lot: float, sl: float, tp: float,elow:float,ehigh:float):
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

    # Create pending Buy Limit order
    point = mt5.symbol_info(symbol).point
    price = mt5.symbol_info_tick(symbol).ask
    deviation = 20
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
        "comment": "xauusd execute SELL",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_FOK,
    }

    # Send order
    if(elow<price<ehigh):
        result = mt5.order_send(request)
    else:
        result = None

    # Handle result
    return result
    
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