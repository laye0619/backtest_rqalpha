from rqalpha import run_file
import pandas as pd
from backtest.utils import const

strategy_name = 'rs_m_style_28'

start_date = "20140416"
# start_date = "20151001"
end_date = "20220701"

momentum_period = 20,
trend_indicator_filter = 0.0,
trend_indicator_buffer = 0.4,
check_date = pd.date_range(start_date, end_date, freq='d')

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
    }
)


run_file(strategy_file_path, config)
