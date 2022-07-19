from dataclasses import dataclass

from backtest.strategy.bs import BalanceStrategy
from rqalpha.apis import *


@dataclass
class BalanceStrategyTest(BalanceStrategy):
    def calculate_position(self) -> dict:
        if not self._init_fired:  # 初始仓位计算
            self._init_fired = True
            return {'stock': 0.5, 'bond': 0.5}
        return {'stock': 0.5, 'bond': 0.5}
