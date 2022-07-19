from rqalpha import run_file
import pandas as pd
from backtest.utils import const

strategy_name = 'bs_vaq_rs_m_style_28'

start_date = "20140416"
# start_date = "20151001"
end_date = "20220701"

momentum_period = 20,
trend_indicator_filter = 0.0,
trend_indicator_buffer = 0.4,
check_date = pd.date_range(start_date, end_date, freq='d')

position_diff_threshold = 0.1
pct_period = 'y5'
va_method = 'median'

strategy_file_path = f'./backtest/bt/{strategy_name}/{strategy_name}.py'
report_save_path = f'./backtest/bt_report/{strategy_name}/single_run'

config = const.get_config(
    start_date=start_date,
    end_date=end_date,
    report_save_path=report_save_path,
    context_vars={
        "check_date": check_date,
        "momentum_period": momentum_period,
        "trend_indicator_filter": trend_indicator_filter,
        "trend_indicator_buffer": trend_indicator_buffer,
        "position_diff_threshold": position_diff_threshold,
        "pct_period": pct_period,
        "va_method": va_method
    }
)


run_file(strategy_file_path, config)
