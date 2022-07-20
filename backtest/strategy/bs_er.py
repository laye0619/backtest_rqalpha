from dataclasses import dataclass, field

import pandas as pd
import tushare as ts
from backtest.strategy.bs import BalanceStrategy
from backtest.utils import bt_analysis_helper
from numpy import mean
from rqalpha.apis import *


@dataclass
class BalanceStrategyEquallyRisk(BalanceStrategy):
    va_pct_period: str = '5y'  # 估值分位数长度，默认5年
    # 估值方法，默认中位数 ['median', 'mcw', 'ewpvo', 'ew', 'avg']
    va_method: str = 'median'
    vo_period: int = 30  # 波动率（标准差）计算周期，默认是30天

    # 波动率计算表，在策略init中调用get_vo传入
    __vo_df_dict: dict = field(default_factory=dict)

    __yesterday_target_stock_position: float = 0.0  # t-1期目标股票仓位, calculate_position传入
    __yesterday_vo_std: float = 0.0  # t-1期波动率std值, calculate_position传入
    yesterday_total_value: float = 0.0  # t-1期总资产，handle_bar中最后传入

    def calculate_position(self) -> dict:
        """风险暴露平价方法初始仓位与日常仓位计算逻辑不一致
            初始仓位使用估值确定，即股票仓位为1-(pe+pb)/2
            日常仓位=总资产（t-1期）*目标股票仓位（t-1期）*波动率（t-1期）/（总资产（t期）*波动率（t期））
        Returns:
            dict: _description_
        """
        today_str = self.context.now.date().strftime('%Y%m%d')

        if not self._init_fired:  # 计算初始仓位
            # 计算今日股票仓位 - 估值
            pe_pct, pb_pct = bt_analysis_helper.caculate_va_1000002_lxr(
                date=today_str,
                pct_period=self.va_pct_period,
                method=self.va_method
            )
            today_stock_position = 1-(pe_pct+pb_pct)/2

            # # 计算今日股票仓位 - 波动率分位
            # pct_list = []
            # for target, vo_df in self.__vo_df_dict.items():
            #     pct = vo_df.loc[today_str, 'std_pct']
            #     pct_list.append(0.5 if pd.isna(pct) else pct)
            # bond_position = mean(pct_list)

            # today_stock_position = 1-bond_position

            # 计算今日波动率值
            vo_std_list = []
            for target, vo_df in self.__vo_df_dict.items():
                std = vo_df.loc[today_str, 'std']
                vo_std_list.append(std)
            today_vo_std = mean(vo_std_list)

            self._init_fired = True
        else:  # 计算日常仓位
            # 计算今日波动率值
            vo_std_list = []
            for target, vo_df in self.__vo_df_dict.items():
                std = vo_df.loc[today_str, 'std']
                vo_std_list.append(std)
            today_vo_std = mean(vo_std_list)

            # 计算今日股票仓位
            yesterday_risk_value = self.yesterday_total_value * \
                self.__yesterday_target_stock_position*self.__yesterday_vo_std
            today_total_value = self.context.stock_account.total_value
            today_stock_position = yesterday_risk_value / \
                (today_total_value*today_vo_std)

            today_stock_position *= self.stock_position_multiples

            # 处理股票仓位>1的情况
            today_stock_position = today_stock_position if today_stock_position <= 1 else 1

        self.__yesterday_vo_std = today_vo_std  # 记录波动率
        self.__yesterday_target_stock_position = today_stock_position  # 记录股票目标仓位
        return {'stock': today_stock_position, 'bond': (1-today_stock_position)}

    def get_vo(self):
        # 计算波动率表
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
