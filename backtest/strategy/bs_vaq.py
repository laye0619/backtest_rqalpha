from dataclasses import dataclass, field
from statistics import mean

import pandas as pd
from backtest.strategy.bs import BalanceStrategy
from backtest.utils import bt_analysis_helper
from rqalpha.apis import *


@dataclass
class BalanceStrategyVaQ(BalanceStrategy):
    pct_period: str = '5y'  # 估值分位数长度，默认5年
    va_method: str = 'median'  # 估值方法，默认中位数

    def calculate_position(self) -> dict:
        """估值分位数方法初始仓位和日常仓位计算逻辑一致
        Returns:
            dict: _description_
        """
        today_str = self.context.now.date().strftime('%Y%m%d')
        pe_pct_list = []
        pb_pct_list = []
        for target in self.stock_strategy.target_list:
            pe_pct, pb_pct = bt_analysis_helper.caculate_va_lxr(
                target=target[:6],
                date=today_str,
                pct_period=self.pct_period,
                method=self.va_method
            )
            pe_pct_list.append(0.5 if pd.isna(pe_pct) else pe_pct)
            pb_pct_list.append(0.5 if pd.isna(pb_pct) else pb_pct)
        bond_position = (mean(pe_pct_list)+mean(pb_pct_list))/2
        return {'stock': (1-bond_position), 'bond': bond_position}
