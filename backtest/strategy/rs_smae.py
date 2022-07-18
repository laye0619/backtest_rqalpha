from dataclasses import dataclass
from statistics import mean

from backtest.strategy.rs import RotationStrategy
from rqalpha.apis import *
import talib


@dataclass
class RotationStrategySmaEnergy(RotationStrategy):
    """_summary_
        继承自基类RotationStrategy，实现基于均线能量的轮动类策略，例如均线能量行业轮动等
    """
    sma_period: int = 20  # 均线期间，默认为20

    def sort_target_list(self) -> pd.DataFrame():
        price_list_df = pd.DataFrame(columns=['target', 'up', 'diff_avg'])
        sma_buffer = 35
        for target in self.target_list:
            price_df = pd.DataFrame(
                history_bars(target, bar_count=self.sma_period+sma_buffer, frequency='1d', fields=['datetime', 'close']))
            price_df.sort_values(by='datetime', ascending=True, inplace=True)
            price_df['sma'] = talib.SMA(price_df['close'], self.sma_period)
            up = 0
            diff_avg = 0
            diff_list = []  # 增加涨幅，以区分能量相同的不同标的
            for i in range(1, sma_buffer):
                today_sma = price_df['sma'].iloc[(i+1)*-1]
                yesterday_sma = price_df['sma'].iloc[(i+2)*-1]
                if today_sma >= yesterday_sma:
                    up += 1
                    diff_list.append((today_sma-yesterday_sma)/yesterday_sma)
                else:
                    diff_avg = mean(diff_list) if diff_list else 0
                    break

            price_list_df = pd.concat([price_list_df, pd.DataFrame(
                [[target, up, diff_avg]], columns=['target', 'up', 'diff_avg'])], ignore_index=True)
        price_list_df['up'] = price_list_df['up'] + \
            price_list_df['diff_avg']
        price_list_df['ranking'] = price_list_df['up'].rank(
            ascending=False, method='min')
        return price_list_df
