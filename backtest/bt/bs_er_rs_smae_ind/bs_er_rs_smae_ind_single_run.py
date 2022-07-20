from rqalpha import run_file
import pandas as pd
from backtest.utils import const

strategy_name = 'bs_er_rs_smae_ind'

start_date = "20140416"
# start_date = "20151001"
end_date = "20220701"

holding_num = 2
sma_period = 20,
trend_indicator_filter = 1.0,
trend_indicator_buffer = 0.0,
rank_indicator_buffer = 1
check_date = pd.date_range(start_date, end_date, freq='d')

position_diff_threshold = 0.1
va_pct_period = 'y5'
va_method = 'median'
vo_period = 30
stock_position_multiples = 1.05

strategy_file_path = f'./backtest/bt/{strategy_name}/{strategy_name}.py'
report_save_path = f'./backtest/bt_report/{strategy_name}/single_run'

config = const.get_config(
    start_date=start_date,
    end_date=end_date,
    report_save_path=report_save_path,
    context_vars={
        "check_date": check_date,
        "sma_period": sma_period,
        "holding_num": holding_num,
        "trend_indicator_filter": trend_indicator_filter,
        "trend_indicator_buffer": trend_indicator_buffer,
        "rank_indicator_buffer": rank_indicator_buffer,
        "position_diff_threshold": position_diff_threshold,
        "va_pct_period": va_pct_period,
        "va_method": va_method,
        "vo_period": vo_period,
        "stock_position_multiples": stock_position_multiples,
    }
)

run_file(strategy_file_path, config)
