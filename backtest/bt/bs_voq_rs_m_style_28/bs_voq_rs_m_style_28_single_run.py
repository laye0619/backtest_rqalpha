from rqalpha import run_file
import pandas as pd
from backtest.utils import const

strategy_name = 'bs_voq_rs_m_style_28'

momentum_period = 20,
trend_indicator_filter = 0.0,
trend_indicator_buffer = 0.4,

position_diff_threshold = 0.1
vo_period = 30
stock_position_multiples = 1

strategy_file_path = f'./backtest/bt/{strategy_name}/{strategy_name}.py'
report_save_path = f'./backtest/bt_report/{strategy_name}/single_run'

config = const.get_config(
    report_save_path=report_save_path,
    context_vars={
        "momentum_period": momentum_period,
        "trend_indicator_filter": trend_indicator_filter,
        "trend_indicator_buffer": trend_indicator_buffer,
        "position_diff_threshold": position_diff_threshold,
        "vo_period": vo_period,
        "stock_position_multiples": stock_position_multiples
    }
)

run_file(strategy_file_path, config)
