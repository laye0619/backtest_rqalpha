import os
import json
from dataclasses import dataclass, field
from statistics import mean

import pandas as pd
import tushare as ts
from backtest.strategy.bs import BalanceStrategy
from backtest.utils import bt_analysis_helper
from rqalpha.apis import *


@dataclass
class BalanceStrategyVoQ(BalanceStrategy):
    # bt_analysis_helper.caculate_vo计算出来的波动率信息表
    __vo_df_dict: dict = field(default_factory=dict)
    vo_period: int = 30  # 波动率（标准差）计算周期，默认是30天

    def calculate_position(self) -> dict:
        """波动率分位数方法初始仓位和日常仓位计算逻辑一致

        Returns:
            dict: _description_
        """
        today_str = self.context.now.date().strftime('%Y%m%d')
        pct_list = []
        for target, vo_df in self.__vo_df_dict.items():
            pct = vo_df.loc[today_str, 'std_pct']
            pct_list.append(0.5 if pd.isna(pct) else pct)
        bond_position = mean(pct_list)
        stock_position = 1-bond_position

        stock_position *= self.stock_position_multiples
        # 处理股票仓位>1的情况
        stock_position = stock_position if stock_position <= 1 else 1

        return {'stock': stock_position, 'bond': (1-stock_position)}

    def get_vo(self):
        ts.set_token(
            '602e5ad960d66ab8b1f3c13b4fd746f5323ff808b0820768b02c6da3')
        pro = ts.pro_api()
        vo_table_dict = {}
        for target in self.stock_strategy.target_list:
            target_ts = target[:6] + \
                '.SH' if target.endswith('XSHG') else target[:6]+'.SZ'
            df = pro.index_daily(ts_code=target_ts)
            df = df[['trade_date', 'close']]
            df = df.set_index('trade_date')
            vo_table_dict[target] = bt_analysis_helper.caculate_vo_ts(
                df, std_period=self.vo_period)
        self.__vo_df_dict = vo_table_dict
