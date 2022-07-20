"""
批量回测任务
测试不同的参数在固定周期内（start_date & end_date）的表现，从而确定最优参数
    1 不同holding_num，[2, 3]
    2 不同trend_indicator_filter，[0, 1, 2, 3]
    3 不同trend_indicator_buffer，[0, 1]
"""

import concurrent.futures
import multiprocessing

import backtest.utils.bt_analysis_helper as bt_analysis_helper
import pandas as pd
from rqalpha import run
from backtest.utils import const

strategy_name = 'bs_voq_rs_smae_ind'

strategy_file_path = f'./backtest/bt/{strategy_name}/{strategy_name}.py'
report_save_path = f'./backtest/bt_report/{strategy_name}/param_optimize'

sma_period = 20
rank_indicator_buffer = 1

position_diff_threshold = 0.1
vo_period = 30
stock_position_multiples = 1

# 如果const.config中date修改了，此处需要一并修改
start_date='20140416'
end_date='20220701'

tasks = []

for holding_num in [2, 3]:
    for trend_indicator_filter in [0, 1, 2, 3]:
        for trend_indicator_buffer in [0, 1]:
                config = const.get_config(
                    report_save_path=report_save_path,
                    context_vars={
                        "sma_period": (sma_period,0),
                        "holding_num": (holding_num,0),
                        "trend_indicator_filter": (trend_indicator_filter,0),
                        "trend_indicator_buffer": (trend_indicator_buffer,0),
                        "rank_indicator_buffer": (rank_indicator_buffer,0),
                        "position_diff_threshold": position_diff_threshold,
                        "vo_period": vo_period,
                        "stock_position_multiples": stock_position_multiples,
                    }
                )
                config['base']['strategy_file'] = strategy_file_path
                config['mod']['sys_analyser']['output_file'] = f'{report_save_path}/{strategy_name}.{holding_num}.{trend_indicator_filter}.{trend_indicator_buffer}.pkl',
                config['mod']['sys_analyser']['report_save_path'] = None
                config['mod']['sys_analyser']['plot_save_file'] = None
                
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
