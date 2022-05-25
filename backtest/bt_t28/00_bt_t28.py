"""
在terminal中运行:
rqalpha run --plot-save result.png -f ./backtest/bt_t28/00_bt_t28.py
"""
from rqalpha.apis import *

PARAMS = {
    'tendency_28_backtest': {
        '000903.XSHG': '中证100',
        '399006.XSHE': '创业板指'
    }
}

__config__ = {
    "base": {
        "accounts": {
            "STOCK": 1000 * 10000,
        },
        # "data_1st-bundle-path": "/Users/i335644/.rqalpha/bundle",
        "start_date": "20130101",
        "end_date": "20220501",
    },
    "extra": {
        "log_level": "info",
    },
    "mod": {
        "sys_analyser": {
            "plot": True,
            # "benchmark": "000300.XSHG",
            "benchmark": "399006.XSHE",
            "report_save_path": './backtest/bt_t28/backtest_report/',
        },
        'sys_simulation': {
            'volume_limit': False,  # 成交量限制，因为买指数，按指数成交，所有金额较大，关闭成交量限制
        },
        'sys_transaction_cost': {
            'commission_multiplier': 0.2  # 默认是万8，实际上是万1.5
        }
    }
}


def init(context):
    context.params = PARAMS['tendency_28_backtest']
    p_t28_aim_list = list(context.params.keys())
    context.p_CHECK_DATE = pd.date_range(
        context.config.base.start_date, context.config.base.end_date, freq='d')

    # set tendency28 params
    context.p_t28_AIM1 = p_t28_aim_list[0]
    context.p_t28_AIM2 = p_t28_aim_list[1]
    context.p_t28_UP_THRESHOLD = 0.4
    context.p_t28_DIFF_THRESHOLD = 0.3
    context.p_t28_PREV = 20
    context.p_t28_STATUS = 0  # having status


def handle_bar(context, bar_dict):
    if pd.to_datetime(context.now.date()) not in context.p_CHECK_DATE:
        return
    logger.info('Strategy executing...')
    __trans_tendency28(context)


# 28轮动策略
def __trans_tendency28(context):
    df1 = pd.DataFrame(history_bars(
        context.p_t28_AIM1, bar_count=50, frequency='1d', fields=['datetime', 'close']))
    df1['datetime'] = pd.to_datetime(df1['datetime'], format="%Y%m%d%H%M%S")
    up1 = (
        (df1.iloc[-2].close - df1.iloc[-2 - context.p_t28_PREV].close)
        / df1.iloc[-2 - context.p_t28_PREV].close
        * 100
    )
    df2 = pd.DataFrame(history_bars(
        context.p_t28_AIM2, bar_count=50, frequency='1d', fields=['datetime', 'close']))
    df2['datetime'] = pd.to_datetime(df2['datetime'], format="%Y%m%d%H%M%S")
    up2 = (
        (df2.iloc[-2].close - df2.iloc[-2 - context.p_t28_PREV].close)
        / df2.iloc[-2 - context.p_t28_PREV].close
        * 100
    )
    if up1 < context.p_t28_UP_THRESHOLD and up2 < context.p_t28_UP_THRESHOLD:
        if context.p_t28_STATUS == 1:
            order_target_percent(context.p_t28_AIM1, 0)
            context.p_t28_STATUS = 0
        elif context.p_t28_STATUS == 2:
            order_target_percent(context.p_t28_AIM2, 0)
            context.p_t28_STATUS = 0
    elif up1 > context.p_t28_UP_THRESHOLD and up1 > up2:
        if context.p_t28_STATUS == 0:
            order_target_percent(context.p_t28_AIM1, 1)
            context.p_t28_STATUS = 1
        elif context.p_t28_STATUS == 2 and up1 - up2 > context.p_t28_DIFF_THRESHOLD:
            order_target_percent(context.p_t28_AIM2, 0)
            order_target_percent(context.p_t28_AIM1, 1)
            context.p_t28_STATUS = 1
    elif up2 > context.p_t28_UP_THRESHOLD and up2 > up1:
        if context.p_t28_STATUS == 0:
            order_target_percent(context.p_t28_AIM2, 1)
            context.p_t28_STATUS = 2
        elif context.p_t28_STATUS == 1 and up2 - up1 > context.p_t28_DIFF_THRESHOLD:
            order_target_percent(context.p_t28_AIM1, 0)
            order_target_percent(context.p_t28_AIM2, 1)
            context.p_t28_STATUS = 2
