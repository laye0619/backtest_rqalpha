from rqalpha import run_file
import pandas as pd
from backtest.utils import const

strategy_name = 'bs_vaq_rs_smae_style_28'

sma_period = 20,
trend_indicator_filter = 2.0,
trend_indicator_buffer = 0.0,

position_diff_threshold = 0.1
pct_period = 'y5'
va_method = 'median'
stock_position_multiples = 1

strategy_file_path = f'./backtest/bt/{strategy_name}/{strategy_name}.py'
report_save_path = f'./backtest/bt_report/{strategy_name}/single_run'

config = const.get_config(
    report_save_path=report_save_path,
    context_vars={
        "sma_period": sma_period,
        "trend_indicator_filter": trend_indicator_filter,
        "trend_indicator_buffer": trend_indicator_buffer,
        "position_diff_threshold": position_diff_threshold,
        "pct_period": pct_period,
        "va_method": va_method,
        "stock_position_multiples": stock_position_multiples
    }
)

run_file(strategy_file_path, config)
