import pandas as pd
from rqalpha import run_file
from backtest.utils import const

strategy_name = 'rs_smae_ind'

start_date = "20140416"
# start_date = "20151001"
end_date = "20220701"

holding_num = 2
sma_period = 20,
trend_indicator_filter = 2.0,
trend_indicator_buffer = 1.0,
rank_indicator_buffer = 1
check_date = pd.date_range(start_date, end_date, freq='d')

strategy_file_path = f'./backtest/bt/{strategy_name}/{strategy_name}.py'
report_save_path = f'./backtest/bt_report/{strategy_name}/single_run'

config = const.get_config(
    start_date=start_date,
    end_date=end_date,
    report_save_path=report_save_path,
    context_vars={
        "check_date": check_date,
        "holding_num": (holding_num,),
        "sma_period": sma_period,
        "trend_indicator_filter": trend_indicator_filter,
        "trend_indicator_buffer": trend_indicator_buffer,
        "rank_indicator_buffer": (rank_indicator_buffer,)
    }
)


run_file(strategy_file_path, config)
