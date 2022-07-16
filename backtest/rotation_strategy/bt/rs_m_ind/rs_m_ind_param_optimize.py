"""
批量回测任务
测试不同的参数在固定周期内（start_date & end_date）的表现，从而确定最优参数
    1 不同时间检查频率，每天检查，每3天检查，每周检查，半月检查等等
    2 不同momentum_period，range(10, 31, 5)
    3 不同trend_indicator_filter，range(-2, 3, 1)
    4 不同trend_indicator_buffer，range(0, 11, 2) /10
    5 不同holding_num，range(1, 4, 1)
    6 不同rank_indicator_buffer，range(0, 2, 1)
"""

import concurrent.futures
import multiprocessing

import backtest.utils.bt_analysis_helper as bt_analysis_helper
import pandas as pd
from rqalpha import run

strategy_name = 'rs_m_ind'


start_date = "20140416"
end_date = "20220701"
strategy_file_path = f'./backtest/rotation_strategy/bt/{strategy_name}/{strategy_name}.py'
report_save_path = f'./backtest/rotation_strategy/bt_report/{strategy_name}/param_optimize'

check_date_list = [
    pd.date_range(start_date, end_date, freq='d'),
    # pd.date_range(start_date, end_date, freq='3d'),
    # pd.date_range(start_date, end_date, freq='W-MON'),
    # pd.date_range(start_date, end_date, freq='SM'),
    # pd.date_range(start_date, end_date, freq='M'),
    # pd.date_range(start_date, end_date, freq='Q'),
]

tasks = []
for check_date in check_date_list:
    for momentum_period in [30]:
        for trend_indicator_filter in range(-2, 3, 1):
            for trend_indicator_buffer in range(0, 11, 2):
                for holding_num in range(1, 4, 1):
                    for rank_indicator_buffer in range(0, 2, 1):
                        config = {
                            "extra": {
                                "context_vars": {  # 未知原因，此处传进去的参数会数字显示，而不是tuple（XX，），而single file就会是tuple
                                    "check_date": check_date,
                                    "holding_num": (holding_num,),
                                    "momentum_period": (momentum_period,),
                                    "trend_indicator_filter": (trend_indicator_filter,),
                                    "trend_indicator_buffer": (trend_indicator_buffer/10,),
                                    "rank_indicator_buffer": (rank_indicator_buffer,)
                                },
                                "log_level": "ERROR",  # DEBUG, INFO, WARNING, ERROR
                            },
                            "base": {
                                "start_date": start_date,
                                "end_date": end_date,
                                "frequency": "1d",
                                "matching_type": "current_bar",
                                "accounts": {
                                    "STOCK": 1000 * 10000
                                },
                                "strategy_file": strategy_file_path
                            },
                            "mod": {
                                "sys_progress": {
                                    "enabled": False,
                                    "show": False,
                                },
                                "sys_analyser": {
                                    # 策略基准，该基准将用于风险指标计算和收益曲线图绘制
                                    #   若基准为单指数/股票，此处直接设置 order_book_id，如："000300.XSHG"
                                    #   若基准为复合指数，则需传入 order_book_id 和权重构成的字典，如：{"000300.XSHG": 0.2. "000905.XSHG": 0.8}
                                    "benchmark": "000300.XSHG",
                                    # 当不输出 csv/pickle/plot 等内容时，关闭该项可关闭策略运行过程中部分收集数据的逻辑，用以提升性能
                                    "record": True,
                                    # 回测结果输出的文件路径，该文件为 pickle 格式，内容为每日净值、头寸、流水及风险指标等；若不设置则不输出该文件
                                    "output_file": f'{report_save_path}/{strategy_name}.{check_date.freq.freqstr}.{momentum_period}.{trend_indicator_filter}.{trend_indicator_buffer}.{holding_num}.{rank_indicator_buffer}.pkl',
                                    # 回测报告的数据目录，报告为 csv 格式；若不设置则不输出报告
                                    "report_save_path": None,
                                    # 是否在回测结束后绘制收益曲线图
                                    'plot': False,
                                    # 收益曲线图路径，若设置则将收益曲线图保存为 png 文件
                                    'plot_save_file': None,
                                    # 收益曲线图设置
                                    'plot_config': {
                                        # 是否在收益图中展示买卖点
                                        'open_close_points': False,
                                        # 是否在收益图中展示周度指标和收益曲线
                                        'weekly_indicators': False
                                    },
                                },
                                'sys_simulation': {
                                    # 开启信号模式：该模式下，所有通过风控的订单将不进行撮合，直接产生交易
                                    "signal": False,
                                    # 撮合方式，其中：
                                    #   日回测的可选值为 "current_bar"|"vwap"（以当前 bar 收盘价｜成交量加权平均价撮合）
                                    #   分钟回测的可选值有 "current_bar"|"next_bar"|"vwap"（以当前 bar 收盘价｜下一个 bar 的开盘价｜成交量加权平均价撮合)
                                    #   tick 回测的可选值有 "last"|"best_own"|"best_counterparty"（以最新价｜己方最优价｜对手方最优价撮合）和 "counterparty_offer"（逐档撮合）
                                    "matching_type": "current_bar",
                                    # 开启对于处于涨跌停状态的证券的撮合限制
                                    "price_limit": True,
                                    # 开启对于对手盘无流动性的证券的撮合限制（仅在 tick 回测下生效）
                                    "liquidity_limit": False,
                                    # 开启成交量限制
                                    #   开启该限制意味着每个 bar 的累计成交量将不会超过该时间段内市场上总成交量的一定比值（volume_percent）
                                    #   开启该限制意味着每个 tick 的累计成交量将不会超过当前tick与上一个tick的市场总成交量之差的一定比值
                                    "volume_limit": False,  # 成交量限制，因为买指数，按指数成交，所有金额较大，关闭成交量限制
                                    # 每个 bar/tick 可成交数量占市场总成交量的比值，在 volume_limit 开启时生效
                                    "volume_percent": 0.25,
                                    # 滑点模型，可选值有 "PriceRatioSlippage"（按价格比例设置滑点）和 "TickSizeSlippage"（按跳设置滑点）
                                    #    亦可自己实现滑点模型，选择自己实现的滑点模型时，此处需传入包含包和模块的完整类路径
                                    #    滑点模型类需继承自 rqalpha.mod.rqalpha_mod_sys_simulation.slippage.BaseSlippage
                                    "slippage_model": "PriceRatioSlippage",
                                    # 设置滑点值，对于 PriceRatioSlippage 表示价格的比例，对于 TickSizeSlippage 表示跳的数量
                                    "slippage": 0,
                                    # 开启对于当前 bar 无成交量的标的的撮合限制（仅在日和分钟回测下生效）
                                    "inactive_limit": True,
                                    # 账户每日计提的费用，需按照(账户类型，费率)的格式传入，例如[("STOCK", 0.0001), ("FUTURE", 0.0001)]
                                    "management_fee": [],
                                },
                                'sys_transaction_cost': {
                                    # 股票最小手续费，单位元
                                    "cn_stock_min_commission": 0,  # ETF没有最小手续费
                                    # 佣金倍率，即在默认的手续费率基础上按该倍数进行调整，股票的默认佣金为万八，期货默认佣金因合约而异
                                    "commission_multiplier": 0.2,  # 默认是万8，实际上是万1.5
                                    # 印花倍率，即在默认的印花税基础上按该倍数进行调整，股票默认印花税为千分之一，单边收取
                                    "tax_multiplier": 0,  # ETF没有印花税
                                }
                            },
                        }
                        tasks.append(config)


def run_bt(config):
    run(config)


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        # with concurrent.futures.ProcessPoolExecutor(max_workers=1) as executor:
        for task in tasks:
            executor.submit(run_bt, task)
    bt_analysis_helper.get_analysis_result(
        start_date, end_date, report_save_path
    ).sort_values(by='sharpe', ascending=False).to_excel(
        f'{report_save_path}/{strategy_name}_param_optimize.xlsx', index=0)
