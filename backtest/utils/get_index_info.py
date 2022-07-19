from rqalpha.apis import *
from rqalpha import run_func
import pandas as pd
from numpy import *


# result = history_bars('000891.XSHG', 1000, '1d',['datetime','close'])
# result = history_bars('000002.XSHE', 5, '1d', 'close')
# print()

target = {
    '399975': '',
    '000819': '',
    '000993': '',
    '399971': '',
    '399932': '',
    '399913': '',
    
}

def init(context):   
    pass

def handle_bar(context, bar_dict):
    # result = pd.DataFrame(history_bars('000891.XSHG', 5, '1d', ['datetime','close']))
    temp = all_instruments(type='INDX', date=None)
    # result_dict = {}
    # for code in target.keys():
    #     picked_series = temp.loc[temp['order_book_id'].str.contains(code)]
    #     if not picked_series.empty:
    #         result_dict[picked_series['order_book_id'].iloc[0]] = pd.to_datetime(picked_series['listed_date'].iloc[0]).strftime('%Y%m%d')


    
    price = pd.DataFrame(history_bars('000300.XSHG', 50, '1d',['datetime','close']))
    result = std(diff(price['close']) / price['close'][:-1])
    print()
    
    # result = order_target_value('H11001.XSHG',100000000)
    # result = order_target_percent('000012.XSHG',0.3)
    # result = order_target_percent('000891.XSHG',0.5)
    print()

__config__ = {
    "base": {
        "start_date": "20150501",
        "end_date": "20220630",
        "frequency": "1d",
        "matching_type": "current_bar",
        "benchmark": None,
        "accounts": {
            "stock": 1000000
        }
    },
    "extra": {
        "log_level": "error",
    },
    "mod": {
        "sys_progress": {
            "enabled": True,
            "show": True,
        },
    },
}

run_func(**globals())
