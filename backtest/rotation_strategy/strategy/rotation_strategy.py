from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from rqalpha.apis import *


@dataclass
class RotationStrategy(ABC):
    """趋势轮动策略基类，可适应所有趋势轮动策略。分为两个主要步骤：
        1）交易时点时，根据趋势指标，结合趋势类指标缓冲区大小，
           将target_list进行排名，返回结果只符合标准的排名列表
           如果没有符合趋势指标结合缓冲区标准的，返回为空 - sort_target_list
        2）根据现有持仓信息，以及排名指标缓冲区大小，确定是否需要调仓，并相应调仓操作 - transction
    """
    target_list: list
    holding_num: int  # 同时持仓数量
    context: StrategyContext = field(
        default_factory=StrategyContext)  # 回测框架中的context对象
    bar_dict: dict = field(default_factory=dict)  # 交易时点的K线

    trend_indicator_filter: float = 0.0  # 趋势类指标过滤器
    trend_indicator_buffer: float = 0.0  # 趋势类指标缓冲区大小
    rank_indicator_buffer: int = 0  # 排名指标缓冲区大小 - 用于调仓策略

    @abstractmethod
    def sort_target_list(self) -> pd.DataFrame():
        pass

    def transction(self, sorted_df):
        current_positions = get_positions()
        if not current_positions:  # 当前空仓，按规则买入
            logger.info(f'当前空仓，按规则买入...')
            empty_position_to_buy = sorted_df.loc[sorted_df['up'] > (
                self.trend_indicator_filter+self.trend_indicator_buffer)]
            if empty_position_to_buy.empty:
                logger.info(f'没有符合要求的标的，静待明天...')
                return

            # 此处需要测试：如果符合trend_indicator的标的数量小于目标持仓数量，要不要买？？
            if len(empty_position_to_buy) < self.holding_num:
                logger.info(
                    f'符合要求的标的数量：{len(empty_position_to_buy)}小于目标持仓量：{self.holding_num}，不操作，静待明天...')
                return
            ######

            empty_position_to_buy = empty_position_to_buy.iloc[:self.holding_num, ]
            for target in empty_position_to_buy['target']:
                order_target_percent(target, 1/len(empty_position_to_buy))
        else:  # 当前有持仓，需要按逻辑调仓
            # 确定当前持仓列表是否需要卖出
            for position in current_positions:
                holding_series = sorted_df.loc[
                    sorted_df['target'] == position.order_book_id
                ]
                today_ranking = holding_series['ranking'].iloc[0]
                today_up = holding_series['up'].iloc[0]
                if (today_ranking > self.holding_num+self.rank_indicator_buffer) or (today_up < self.trend_indicator_filter-self.trend_indicator_buffer):
                    logger.info(
                        f'{position.order_book_id}不符合策略持仓条件，需要全部卖出...')
                    order_target_percent(position.order_book_id, 0)

            # 卖出操作后，重新获取持仓
            current_positions = get_positions()
            # 确定当前是否需要买入
            if len(current_positions) == self.holding_num:  # 持仓数量符合要求，不操作
                return
            today_to_buy = sorted_df.loc[sorted_df['up'] > (
                self.trend_indicator_filter+self.trend_indicator_buffer)]

            if today_to_buy.empty:
                logger.info(f'没有符合要求的标的，静待明天...')
                return

            # 此处需要测试：如果符合trend_indicator的标的数量小于目标持仓数量，要不要买？？
            if len(today_to_buy) < self.holding_num:
                logger.info(
                    f'符合要求的标的数量：{len(today_to_buy)}小于目标持仓量：{self.holding_num}，不操作，静待明天...')
                return
            ######

            today_to_buy = list(
                today_to_buy.iloc[:self.holding_num, ]['target'])
            today_holding_list = [x.order_book_id for x in current_positions]
            today_to_buy = list(
                set(today_to_buy).difference(set(today_holding_list)))
            for target in today_to_buy:
                logger.info(f'买入{target}...')
                order_target_value(
                    target, self.context.stock_account.cash/len(today_to_buy))
