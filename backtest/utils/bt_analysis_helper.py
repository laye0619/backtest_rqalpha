import pandas as pd
import glob

def get_analysis_result(start_date, end_date, pkl_save_path)->pd.DataFrame:
    """分析给定的pkl文件夹下所有的pkl文件，并生成df

    Args:
        start_date (_type_): 为了计算年交易次数，需要给出起始日期
        end_date (_type_): 为了计算年交易次数，需要给出结束日期
        pkl_save_path (_type_): 给定pkl文件存储位置

    Returns:
        pd.DataFrame: _description_
    """
    years = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days / 365
    results = []

    for name in glob.glob(f'{pkl_save_path}/*.pkl'):
        result_dict = pd.read_pickle(name)
        summary = result_dict["summary"]
        trades = result_dict['trades']
        results.append({
            "name": name,
            "annualized_returns": summary["annualized_returns"],
            "sharpe": summary["sharpe"],
            "max_drawdown": summary["max_drawdown"],
            "income_drawdown_ratio": summary["annualized_returns"]/summary["max_drawdown"],
            "trade_times_per_year": round(len(trades) / years, 1),
            "alpha": summary["alpha"],
            "total_returns": summary["total_returns"],
        })
    return pd.DataFrame(results)