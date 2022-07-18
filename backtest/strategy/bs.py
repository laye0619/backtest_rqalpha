from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from backtest.utils import const

from rqalpha.apis import *


@dataclass
class BalanceStrategy(ABC):
    """股债平衡类策略，两部分分别记做balance_1和balance_2

    Args:
        ABC (_type_): _description_
    """

    @abstractmethod
    def calculate_init_position() -> dict:
        pass

    @abstractmethod
    def calculate_daily_position() -> dict:
        pass

    @abstractmethod
    def transction(self, calculated_position_dict):
        balance_2_target = const.TARGET_LIST['bond']
        balance_2_position = get_position(balance_2_target)
        pass
