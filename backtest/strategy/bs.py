from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class BalanceStrategy(ABC):
    """XX平衡类策略，例如股债平衡类策略，两部分分别记做balance_1和balance_2

    Args:
        ABC (_type_): _description_
    """
    
    @abstractmethod
    def first_day():
        pass
    
    def each_day():
        pass