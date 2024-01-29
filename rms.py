def fire(kite,direction,strike,lot,instrument,mult,token,days,timeframe):
    square_off_all_positions(kite,"algo")
    exp = get_exp()
    print(exp)
    stk = get_stk(kite,strike,direction)
    long_stk = stk
    short_stk = (long_stk + strike) if direction == "BUY" else (long_stk-strike)
    option_type = "PE" if direction == "SELL" else "CE"
    long_leg = f"{instrument}{exp}{long_stk}{option_type}"
    short_leg = f"{instrument}{exp}{short_stk}{option_type}"
    lot = lot*15
    place_bull_call(long_leg,lot,kite,"BUY")
    place_bull_call(short_leg,lot,kite,"SELL")
    monitor(kite,direction,long_leg,short_leg,lot,mult,token,days,timeframe)



def monitor(kite,direction,long_leg,short_leg,lot,mult,token,days,timeframe):
    import datetime,time,pandas as pd,pandas_ta as ta
    import datetime
    import time
    import pytz
    indian_timezone = pytz.timezone('Asia/Kolkata')
    while True:
        current_time = datetime.datetime.now().time()
        if current_time >= datetime.time(15,25):
            print("Current time is greater than 3:25 pm. Exiting SL TRAIL.")
            cancel_orders(kite)
            square_off_all_positions(kite,"algo")
            break
        #wait_time = (60 * mult) - (current_time.second % (60 * mult))
        #time.sleep(wait_time)
        #print(f"sleeping for  {wait_time}")
        current_time = datetime.datetime.now(indian_timezone).time()
        minutes = current_time.minute
        seconds = current_time.second

        time_to_next_mult = (mult - (minutes % mult)) * 60 - seconds

        print(f"Current time (Indian Time): {current_time}, Waiting for {time_to_next_mult} seconds...")
    
        time.sleep(time_to_next_mult)
        to_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        from_date = (pd.Timestamp.now() - pd.DateOffset(days=days)).strftime('%Y-%m-%d')
        instrument_token = token

        # Fetch historical data for Bank Nifty within the specified date range
        raw_data = kite.historical_data(instrument_token, from_date=from_date, to_date=to_date, interval=timeframe)
        new_data_df = pd.DataFrame(raw_data)
        st1 = ta.supertrend(new_data_df['high'], new_data_df['low'], new_data_df['close'], length=5, multiplier=1.5)
        st2 = ta.supertrend(new_data_df['high'], new_data_df['low'], new_data_df['close'], length=5, multiplier=1.3)
        latest_st1 = st1.iloc[-1]
        latest_st2 = st2.iloc[-1]
        supertrend_values_st1 = latest_st1['SUPERT_5_1.5']
        supertrend_values_st2 = latest_st2['SUPERT_5_1.3']
        if direction == "BUY" and new_data_df['close'].iloc[-1] < supertrend_values_st1 :
            print("Square off buy position")
            # exit_bull_call(short_leg,lot,kite,"BUY")
            square_off_all_positions(kite,"algo")
        elif direction == "SELL" and  new_data_df['close'].iloc[-1] > supertrend_values_st2 :
            print("Square off sell position")   
            # exit_bull_call(long_leg,lot,kite,"SELL")
            square_off_all_positions(kite,"algo")

def cancel_orders(kite):
    orders = kite.orders()
    print(orders)
    for order in orders:
        if  order["pending_quantity"] > 0 and order["status"] == "TRIGGER PENDING" :
            order_id = order["order_id"]
            print(f"{order_id}is the order id to be cancelled")
            kite.cancel_order(kite.VARIETY_REGULAR, order_id)
            print(f"Order {order_id} cancelled")

def get_exp():
    from datetime import datetime, timedelta
        
    current_date = datetime.now()
    day_of_week = current_date.weekday()

    # If it's Tuesday or Wednesday, add 1 or 0 days respectively to get to the next Wednesday
    days_until_nearest_day = (2 - day_of_week + 7) % 7  # 2 corresponds to Wednesday

    nearest_day_date = current_date + timedelta(days=days_until_nearest_day)
    next_week_date = current_date + timedelta(days=7)

    # Check if the selected expiry is the last week of the month
    if nearest_day_date.month != next_week_date.month or (nearest_day_date.day + 7) > next_week_date.day:
        # If it is, return in the format "YYMON"
            month = nearest_day_date.strftime('%m').lstrip('0')  
            return nearest_day_date.strftime('%y{0}%d').format(month) + nearest_day_date.strftime('%y%m%d')[6:]
    else:
        # If it is the 4th Wednesday, return in the format "YYMON"
        return nearest_day_date.strftime('%y%b').upper()
    
def get_stk(kite,offset,direction):
    if direction == "BUY":
        banknifty_ltp = kite.ltp("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["last_price"]
        print(banknifty_ltp)
        strike_price = round(banknifty_ltp / 100) * 100 - offset
        print(f"{strike_price} is strike price")
        return strike_price
    if direction == "SELL":
        banknifty_ltp = kite.ltp("NSE:NIFTY BANK")["NSE:NIFTY BANK"]["last_price"]
        print(banknifty_ltp)
        strike_price = round(banknifty_ltp / 100) * 100 + offset
        print(f"{strike_price} is strike price")
        return strike_price
        



def place_bull_call(instrument, qty,kite,direction):
    print(instrument)
    kite.place_order(variety=kite.VARIETY_REGULAR, exchange="NFO",
                     tradingsymbol=instrument,
                     transaction_type=direction,
                     quantity=qty,
                     order_type="MARKET",
                     product="MIS",
                     validity="DAY",
                     price=0,
                     trigger_price=0,
                     tag = "algo")
    print("Position entered successfully")


# def exit_bull_call(instrument,qty,kite,direction) :
#     print(instrument)
#     kite.place_order(variety=kite.VARIETY_REGULAR, exchange="NFO",
#                      tradingsymbol=instrument,
#                      transaction_type=direction,
#                      quantity=qty,
#                      order_type="MARKET",
#                      product="NRML",
#                      validity="DAY",
#                      price=0,
#                      trigger_price=0)
#     print("Position Exited successfully")

# def square_off_all_positions(kite):
#     # Fetch current positions
#     positions = kite.positions()
#     print(positions)
#     # Iterate through each position type ('net', 'day')
#     for position_type in ['net']:
#         # Iterate through positions of the current type
#         for position in positions.get(position_type, []):
#             # Extract relevant information
#             tradingsymbol = position['tradingsymbol']
#             quantity = position['quantity']
#             if quantity > 0:
#                 # Place a market sell order to square off the position
#                 order_id = kite.place_order(variety=kite.VARIETY_REGULAR,
#                                             exchange=kite.EXCHANGE_NFO,
#                                             tradingsymbol=tradingsymbol,
#                                             transaction_type="BUY" if position['quantity'] < 0 else "SELL",
#                                             quantity=quantity,
#                                             product=kite.PRODUCT_NRML,
#                                             order_type=kite.ORDER_TYPE_MARKET,
#                                             tag="SquareOff")    
    

def square_off_all_positions(kite, tag):
    # Fetch current positions
    positions = kite.positions()
    print(positions)
    # Iterate through each position type ('net', 'day')
    for position_type in ['net']:
        # Iterate through positions of the current type
        for position in positions.get(position_type, []):
            # Check if the position has the specified tag
            if position['tag'] == tag:
                # Extract relevant information
                tradingsymbol = position['tradingsymbol']
                quantity = position['quantity']
                if quantity > 0:
                    # Place a market sell order to square off the position
                    order_id = kite.place_order(variety=kite.VARIETY_REGULAR,
                                                exchange=kite.EXCHANGE_NFO,
                                                tradingsymbol=tradingsymbol,
                                                transaction_type="BUY" if position['quantity'] < 0 else "SELL",
                                                quantity=quantity,
                                                product=kite.PRODUCT_MIS,
                                                order_type=kite.ORDER_TYPE_MARKET,
                                                tag="SquareOff") 
