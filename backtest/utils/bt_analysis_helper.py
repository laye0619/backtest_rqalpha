from datetime import timedelta
import pandas as pd
import numpy as np
import talib
import glob


def get_analysis_result(start_date, end_date, pkl_save_path) -> pd.DataFrame:
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


def caculate_vo_ts(data: pd.DataFrame, std_period: int = 30, sma_period=20) -> pd.DataFrame:
    """计算标的波动率相关数据

    Args:
        df (pd.DataFrame):column=['close'], index='date'
        std_period (int, optional): _description_. Defaults to 30.
        sma_period (int, optional): _description_. Defaults to 20.

    Returns:
        pd.DataFrame: column=['close', 'std', 'sma_std', 'std_pct'], index='date'
    """

    # 计算小周期波动率（标准差）
    std_list = []
    for i in range(0, len(data)-std_period):
        std_df = data.iloc[i:i+std_period, ]
        std_df['Log returns'] = np.log(std_df['close']/std_df['close'].shift())
        std = std_df['Log returns'].std()
        data.loc[std_df.iloc[0].name, 'std'] = std
    data['sma_std'] = talib.SMA(data['std'].sort_index(ascending=True), 20)
    
    # 计算小周期分位数
    pct_list = []
    for i in range(0, len(data)-250*5):
        pct_df = data.iloc[i:i+252*5, ]
        pct_df['pct'] = pct_df['std'].rank(pct=True)
        data.loc[pct_df.iloc[0].name, 'std_pct'] = pct_df.iloc[0]['pct']
    return data
