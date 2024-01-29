import re
import configparser
import pyotp
from jugaad_trader import Zerodha
import asyncio
from datetime import datetime, timedelta
import rms
import time
import pytz

# Set the timezone for India
india_timezone = pytz.timezone('Asia/Kolkata')

config = configparser.ConfigParser()
config.read('creds.ini')
user_id = config['DEFAULT']['user_id']
password = config['DEFAULT']['password']
totp_secret = config['DEFAULT']['totp_secret']
# Initialize TOTP with the secret key
otp_gen = pyotp.TOTP(totp_secret)

# Generate current OTP
current_otp = otp_gen.now()

# Initialize Zerodha class with credentials and OTP
kite = Zerodha(user_id=user_id, password=password, twofa=current_otp)

# Login to Zerodha
login_response = kite.login()
margins = kite.margins()
print(margins)
ltp = kite.ltp("NSE:POLYCAB")
print(ltp)
print(login_response)

instrument = "BANKNIFTY"
timeframe = "5minute"
lots = 1
strike = 500
token = 260105
if timeframe =="minute" :
    days = 5
    mult = 1
elif timeframe == "3minute" :
    days= 5
    mult =3
elif timeframe == "5minute" :
    days = 10
    mult = 5
elif timeframe == "10minute" :
    days =20
    mult = 10
elif timeframe == "15minute" :
    days = 35
    mult = 15
elif timeframe == "30minute" :
    days = 45
    mult = 30
elif timeframe == "60minute":
    days = 60
    mult = 60

def run_at_915():
    from datetime import datetime, timedelta
    import time
    while True:
    # Get the current time in UTC
        now_utc = datetime.utcnow()

        # Convert UTC time to India time
        now = now_utc.replace(tzinfo=pytz.utc).astimezone(india_timezone)

        # Print the India time
        print("India Time:", now.strftime('%Y-%m-%d %H:%M:%S %Z'))
        print(now)
        target_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
        
        if now >= target_time:
            fetch_nifty_data(kite)
            break

        time.sleep(1)        

def is_candle_close_above_supertrend(close_price, supertrend_value):
    return close_price > supertrend_value

def is_candle_close_below_supertrend(close_price, supertrend_value):
    return close_price < supertrend_value

def fetch_nifty_data(kite):
    import datetime
    import pandas as pd
    import pandas_ta as ta
    import time
    while True:
        current_time = datetime.datetime.now().time()
        # if current_time >= datetime.time(15,30):
        #      print("Current time is greater than 3:30 pm. Exiting the loop.")
        #      break
        #wait_time = (60 * mult) - (current_time.second % (60 * mult))+2
        #print(f"Current wait time is {wait_time}")
        #time.sleep(wait_time)
        current_time = datetime.datetime.now(india_timezone).time()
        minutes = current_time.minute
        seconds = current_time.second

        time_to_next_mult = (mult - (minutes % mult)) * 60 - seconds

        print(f"Current time (Indian Time): {current_time}, Waiting for {time_to_next_mult} seconds...")
    
        time.sleep(time_to_next_mult)
        to_date = pd.Timestamp.now().strftime('%Y-%m-%d')
        from_date = (pd.Timestamp.now() - pd.DateOffset(days=days)).strftime('%Y-%m-%d')
        instrument_token = token

        new_data = kite.historical_data(instrument_token, from_date=from_date, to_date=to_date, interval=timeframe)
        new_data_df = pd.DataFrame(new_data)
        print(new_data_df)
        st1 = ta.supertrend(new_data_df['high'], new_data_df['low'], new_data_df['close'], length=5, multiplier=1.5)
        st2 = ta.supertrend(new_data_df['high'], new_data_df['low'], new_data_df['close'], length=5, multiplier=1.3)
        latest_st1 = st1.iloc[-1]
        latest_st2 = st2.iloc[-1]
        combined_df = pd.concat([latest_st1, latest_st2], axis=1)
        print(combined_df)
        supertrend_values_st1 = latest_st1['SUPERT_5_1.5']
        supertrend_values_st2 = latest_st2['SUPERT_5_1.3']
        print(f"supertrend 1 is {supertrend_values_st1},supertrend 2 is {supertrend_values_st2}")
        # time.sleep(30)
        if (
        is_candle_close_above_supertrend(new_data_df['close'].iloc[-1], supertrend_values_st1) and
        is_candle_close_above_supertrend(new_data_df['close'].iloc[-1], supertrend_values_st2) and
        new_data_df['open'].iloc[-1] < supertrend_values_st2    
    ):  
            rms.fire(kite,"BUY",strike,lots,instrument,mult,token,days,timeframe)

        elif (
        is_candle_close_below_supertrend(new_data_df['close'].iloc[-1], supertrend_values_st1) and
        is_candle_close_below_supertrend(new_data_df['close'].iloc[-1], supertrend_values_st2) and
        new_data_df['open'].iloc[-1] > supertrend_values_st1     

        ):
            rms.fire(kite,"SELL",strike,lots,instrument,mult,token,days,timeframe)  


run_at_915()            
# fetch_nifty_data(kite)
