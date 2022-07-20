from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from backtest.strategy.rs import RotationStrategy
from backtest.utils import const
from rqalpha.apis import *


@dataclass
class BalanceStrategy(ABC):
    """股债平衡类策略，两部分分别记做bond和stock
        transction中，根据计算来的bond应有仓位，比较当前bond仓位，确定是否触发调仓交易
            1. 触发调仓交易。如果需要卖出，则立即卖出；如果是买入，则先记账（待交易账簿），待股票类卖出完再买入（防止金额不够）
            2. 没有触发调仓交易，不操作
            3. 更新当天股票应有仓位金额，调用股票交易
            4. 交易当天待交易账簿

    Args:
        ABC (_type_): _description_
    """
    stock_strategy: RotationStrategy  # 股票仓位部分的交易策略
    position_diff_threshold: float = 0.1  # 今天目标仓位和实际仓位差值限，若大于此线则出发调仓
    stock_position_multiples: float = 1  # 股票仓位乘数
    
    context: StrategyContext = field(
        default_factory=StrategyContext)  # 回测框架中的context对象
    bar_dict: dict = field(default_factory=dict)  # 交易时点的K线
    _init_fired: bool = False  # 区分是否是初始仓位

    @abstractmethod
    def calculate_position(self) -> dict:
        if not self._init_fired:  # 初始仓位计算
            pass
            return {}
        pass
        return {}

    def transction(self, calculated_position_dict):
        # 检查是否需要有仓位变化需要调仓
        # 账户总金额（加现金）
        today_total_amount = self.context.stock_account.total_value
        bond_order_book_id = list(const.TARGET_LIST['bond'].keys())[0]
        bond_current_position = get_position(
            bond_order_book_id).market_value / today_total_amount
        bond_target_position = calculated_position_dict['bond']
        bond_position_diff = bond_target_position - bond_current_position
        today_to_buy_value_dict = {}  # 待交易账簿
        if abs(bond_position_diff) > self.position_diff_threshold:  # 仓位变化过限，触发调仓
            if bond_position_diff < 0:  # 需要卖出债券至当天目标仓位
                order_target_percent(bond_order_book_id, bond_target_position)
            else:  # 需要买入债券至当天目标仓位，为避免资金不够，先记账（待交易账簿），股票操作后，在买入
                today_to_buy_value_dict[bond_order_book_id] = today_total_amount * \
                    bond_position_diff
            # 更新当天股票应有仓位金额，调用股票交易
            # 如果触发了调仓，则根据目标仓位比例更新股票仓位，否则就维持原比例
            stock_target_amount = today_total_amount * calculated_position_dict['stock']
        else:
            stock_target_amount = today_total_amount * (1-bond_current_position)

        self.stock_strategy.today_total_portfolio_amount = stock_target_amount
        self.stock_strategy.bar_dict = self.bar_dict
        self.stock_strategy.context = self.context
        self.stock_strategy.transction(self.stock_strategy.sort_target_list())

        # 交易当天待交易账簿
        for order_book_id, value in today_to_buy_value_dict.items():
            if self.context.stock_account.cash < value:
                if abs(self.context.stock_account.cash/value-1) > 0.20:
                    raise Exception()
                logger.info(
                    f'No enough cash for buying RMB {value}, buy {self.context.stock_account.cash} instead')
                value = self.context.stock_account.cash
            order_value(order_book_id, value)
