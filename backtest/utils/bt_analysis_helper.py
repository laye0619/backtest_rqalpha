import pandas as pd
import glob

def get_analysis_result(start_date, end_date, pkl_save_path):
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