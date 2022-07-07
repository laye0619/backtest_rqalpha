from this import d
from rqalpha.apis import *
from backtest.bt_grid.grid import Grid
from rqalpha import run_func

PARAMS = {
    'target': '399006.XSHE',
    'grid_params': {
        'startpoint': 1750,
        'interval': 0.1,
        'size': 30
    },
    'transction': {
        'init_portion': 0.8,
        'grid_portion': 0.05
    },
    'fired': False
}

__config__ = {
    "base": {
        "accounts": {
            "STOCK": 1000 * 10000,
        },
        "start_date": "20130101",
        "end_date": "20201231",
    },
    "extra": {
        "log_level": "info",
    },
    "mod": {
        "sys_analyser": {
            'plot_save_file': './backtest/bt_grid/backtest_report/grid_result.png',
            "benchmark": "399006.XSHE",
            "report_save_path": './backtest/bt_grid/backtest_report/',
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
    context.params = PARAMS
    context.p_CHECK_DATE = pd.date_range(
        context.config.base.start_date, context.config.base.end_date, freq='d')


def handle_bar(context, bar_dict):
    if pd.to_datetime(context.now.date()) not in context.p_CHECK_DATE:
        return
    logger.info('Strategy executing...')
    if not context.params['fired']:  # 第一天运行，需要计算网格并建立初始仓位
        bar_list = history_bars(  # 获取当前价格
            order_book_id=context.params['target'],
            bar_count=1,
            frequency='1d',
            include_now=True
        )

        # 确定中轴是采用给定参数还是以当前价格为中轴
        context.params['grid_params']['startpoint'] = context.params['grid_params'].get(
            'startpoint', bar_list[0]['close'])

        # 建立网格
        context.grid = Grid(
            startpoint=context.params['grid_params']['startpoint'],
            interval=context.params['grid_params']['interval'],
            size=context.params['grid_params']['size'],
        )

        # 确定当前价格在网格中的游标
        context.grid.current_pointer = context.grid.grid_series[
            context.grid.grid_series > bar_list[0]['close']].index[0]

        # 根据参数确定每一网的投资金额
        context.grid_amount = context.config.base.accounts['STOCK'] * \
            context.params['transction']['grid_portion']

        # 根据参数下单初始仓位
        order_percent(context.params['target'],
                      context.params['transction']['init_portion'])
        context.params['fired'] = True
        return
    __trans_grid(context)


# 网格策略
def __trans_grid(context):
    bar_list = history_bars(
        order_book_id=context.params['target'],
        bar_count=1,
        frequency='1d',
        include_now=True
    )
    current_price = bar_list[0]['close']
    left_price = context.grid.grid_series[context.grid.current_pointer-1]
    right_price = context.grid.grid_series[context.grid.current_pointer+1]
    if current_price <= left_price:  # 触发买入条件
        order_value(context.params['target'], context.grid_amount)
        context.grid.current_pointer -= 1
    if current_price >= right_price:  # 触发卖出条件
        order_value(context.params['target'], context.grid_amount*-1)
        context.grid.current_pointer += 1


run_func(**globals())
