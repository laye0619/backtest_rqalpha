from datetime import timedelta
import pandas as pd
import numpy as np
import talib
import glob
import pymongo
import pytz
from backtest.utils import const


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
        pd.DataFrame: column=['close', 'std', 'sma_std', 'std_pct'], index='date'-######
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

def caculate_va_1000002_lxr(date:str, method: str = 'median', pct_period: str = 'y5'):
    """查询理性人‘沪深A股’指数的给定日期，给定方法的pe，pb值

    Args:
        date (str): 六位数字，例如20150104
        method (str, optional): _description_. Defaults to 'median'.
        pct_period (str, optional): _description_. Defaults to 'y5'.
    """
    lxr_record = db_get_dict_from_mongodb(
        mongo_db_name=const.MONGODB_DB_LXR,
        col_name=const.MONGODB_COL_LXR_INDEX,
        query_dict={
            'stockCode': '1000002',
            'date': date
        }
    )
    if len(lxr_record) != 1:
        raise ValueError(f'1000002: 数据库中不存在数据或存在多条记录，有错误！')

    pe_pct = lxr_record[0]['pe_ttm'][pct_period][method]['cvpos']
    pb_pct = lxr_record[0]['pb'][pct_period][method]['cvpos']
    return pe_pct, pb_pct
    


def caculate_va_lxr(target: str, date: str, method: str = 'median', pct_period: str = 'y5'):
    """通过mongodb查询lxr的指数估值分位数表

    Args:
        target (str): 六位代码，例如399001
        date (str): 六位数字，例如20150104
        method (str, optional): ['median', 'mcw', 'ewpvo', 'ew', 'avg']. Defaults to 'median'.
        pct_period (str, optional): ['y10', 'y5']. Defaults to 'y5'.
    """
    # 此处需要单独处理中证消费：lxr中只有上海中证消费000932，没有深圳中证消费399932。这两个是同一指数
    if target[:6] == '399932':
        target = '000932'
    elif target[:6] == '399913':
        target = '000913'
    elif target[:6] == '399905':
        target = '000905'
    lxr_record = db_get_dict_from_mongodb(
        mongo_db_name=const.MONGODB_DB_LXR,
        col_name=const.MONGODB_COL_LXR_INDEX,
        query_dict={
            'stockCode': target,
            'date': date
        }
    )
    if len(lxr_record) != 1:
        raise ValueError(f'{target}数据库中不存在数据或存在多条记录，有错误！')

    pe_pct = lxr_record[0]['pe_ttm'][pct_period][method]['cvpos']
    pb_pct = lxr_record[0]['pb'][pct_period][method]['cvpos']
    return pe_pct, pb_pct


def db_get_dict_from_mongodb(mongo_db_name: str, col_name: str,
                             query_dict: dict = {}, field_dict: dict = {}, inc_id: bool = False):
    '''

    :param mongo_db_name:
    :param col_name:
    :param query_dict:
    :param field_dict: {'column1':1, 'column2':1}
    :return:
    '''
    c = pymongo.MongoClient(
        host=const.MONGODB_LINK,
        tz_aware=True,
        tzinfo=pytz.timezone('Asia/Shanghai')
    )
    db = c[mongo_db_name]
    db_col = db[col_name]
    if not inc_id:
        field_dict['_id'] = 0
    result_dict_list = [x for x in db_col.find(query_dict, field_dict)]
    return result_dict_list

