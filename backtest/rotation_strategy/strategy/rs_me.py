from dataclasses import dataclass

from backtest.rotation_strategy.strategy.rotation_strategy import \
    RotationStrategy
from rqalpha.apis import *


@dataclass
class RSMomentum(RotationStrategy):
    """_summary_
        继承自基类RotationStrategy，实现基于均线能量的轮动类策略，例如均线能量行业轮动等
    """
    m_period: int = 20  # 动量期间，默认为20

    def sort_target_list(self) -> pd.DataFrame():
        price_list_df = pd.DataFrame(columns=['target', 'up'])
        for target in self.target_list:
            price_df = pd.DataFrame(
                history_bars(target, bar_count=self.momentum_period+10, frequency='1d', fields=['datetime', 'close']))
            price_df.sort_values(by='datetime', ascending=True, inplace=True)
            up = (
                (price_df.iloc[-2].close -
                 price_df.iloc[-2 - self.momentum_period].close)
                / price_df.iloc[-2 - self.momentum_period].close
                * 100
            )
            price_list_df = pd.concat([price_list_df, pd.DataFrame(
                [[target, up]], columns=['target', 'up'])], ignore_index=True)
        price_list_df = price_list_df.sort_values(
            by='up', ascending=False).reset_index(drop=True)
        price_list_df['ranking'] = price_list_df['up'].rank(ascending=False)
        return price_list_df
