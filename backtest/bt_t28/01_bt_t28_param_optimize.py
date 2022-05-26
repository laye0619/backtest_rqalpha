"""
批量回测任务
测试不同的参数在固定周期内（start_date & end_date）的表现，从而确定最优参数
    1 不同时间检查频率，每天检查，每3天检查，每周检查，半月检查等等
    2 不同回溯天数，默认是20天，即4周
    3 28轮动调仓标准：正涨幅具体幅度，现结果为0.4%
    4 28轮动调仓标准：两候选标的差值
"""
import concurrent.futures
import multiprocessing
import glob
import pandas as pd

from rqalpha import run

start_date = "20130101"
end_date = "20220501"

p_CHECK_DATE_list = [
    pd.date_range(start_date, end_date, freq='d'),
    # pd.date_range(start_date, end_date, freq='3d'),
    # pd.date_range(start_date, end_date, freq='W-MON'),
    # pd.date_range(start_date, end_date, freq='SM'),
    # pd.date_range(start_date, end_date, freq='M'),
    # pd.date_range(start_date, end_date, freq='Q'),
]

tasks = []
for p_CHECK_DATE in p_CHECK_DATE_list:
    for p_t28_PREV in range(15, 31, 5):
        for p_t28_UP_THRESHOLD in range(0, 11, 2):
            for p_t28_DIFF_THRESHOLD in range(0, 11, 2):
                config = {
                    "extra": {
                        "context_vars": {
                            "p_CHECK_DATE": p_CHECK_DATE,
                            "p_t28_PREV": p_t28_PREV,
                            "p_t28_UP_THRESHOLD": p_t28_UP_THRESHOLD / 10,
                            "p_t28_DIFF_THRESHOLD": p_t28_DIFF_THRESHOLD / 10,
                        },
                        "log_level": "error",
                    },
                    "base": {
                        "accounts": {
                            "STOCK": 1000 * 10000,
                        },
                        # "data_1st-bundle-path": "/Users/i335644/.rqalpha/bundle",
                        "start_date": start_date,
                        "end_date": end_date,
                        "strategy_file": "./backtest/bt_t28/00_bt_t28.py",
                    },
                    "mod": {
                        "sys_progress": {
                            "enabled": True,
                            "show": True,
                        },
                        "sys_analyser": {
                            "enabled": True,
                            "plot": False,
                            "output_file": "./backtest/bt_t28/param_optimize_result/t_28_out-{p_CHECK_DATE}-{p_t28_PREV}-{p_t28_UP_THRESHOLD}-{p_t28_DIFF_THRESHOLD}.pkl".format(
                                p_CHECK_DATE=p_CHECK_DATE.freq.freqstr,
                                p_t28_PREV=p_t28_PREV,
                                p_t28_UP_THRESHOLD=p_t28_UP_THRESHOLD,
                                p_t28_DIFF_THRESHOLD=p_t28_DIFF_THRESHOLD,
                            )
                        },
                        'sys_simulation': {
                            'volume_limit': False,  # 成交量限制，因为买指数，按指数成交，所有金额较大，关闭成交量限制
                        },
                        'sys_transaction_cost': {
                            'commission_multiplier': 0.2  # 默认是万8，实际上是万1.5
                        }
                    },
                }

                tasks.append(config)


def run_bt(config):
    run(config)


def get_analysis_result():
    years = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365
    results = []

    for name in glob.glob("./backtest/bt_t28/param_optimize_result/*.pkl"):
        result_dict = pd.read_pickle(name)
        summary = result_dict["summary"]
        trades = result_dict['trades']
        results.append({
            "name": name,
            "annualized_returns": summary["annualized_returns"],
            "sharpe": summary["sharpe"],
            "max_drawdown": summary["max_drawdown"],
            "trade_times_per_year": round(len(trades) / years, 1),
            "alpha": summary["alpha"],
            "total_returns": summary["total_returns"],
        })

    return pd.DataFrame(results)


if __name__ == '__main__':
    with concurrent.futures.ProcessPoolExecutor(max_workers=multiprocessing.cpu_count()) as executor:
        for task in tasks:
            executor.submit(run_bt, task)
    get_analysis_result().sort_values(by='sharpe', ascending=False).to_excel(
        './backtest/bt_t28/param_optimize_result/bt_t28_wo_bond_param_optimize_result.xlsx', index=0)
