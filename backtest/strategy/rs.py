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

    trend_indicator_filter: float = 0.0  # 趋势类指标过滤器，例如动量，均线能量等
    trend_indicator_buffer: float = 0.0  # 趋势类指标缓冲区大小
    rank_indicator_buffer: int = 0  # 排名指标缓冲区大小 - 用于调仓策略

    today_total_portfolio_amount: float = 0.0  # 今日应有本策略仓位总额

    @abstractmethod
    def sort_target_list(self) -> pd.DataFrame():
        pass

    def transction(self, sorted_df):
        """处理逻辑：
            先处理空仓情况
            再处理有持仓情况：
                1. 计算当前持仓情况与今天应有仓位总额关系，计算当前需要调仓计划，存入‘调仓暂存表’
                2. 检查今日持仓标的，是否有不符合要求的标的，进行卖出操作，并删除‘调仓暂存表’中对应的标的
                3. 根据排名表，结合今日剩余持仓，确定今天需要买入的标的，结合‘调仓暂存表’，确定需要买入的金额，进行买入操作

        Args:
            sorted_df (_type_): _description_
        """
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
                order_target_value(
                    target, self.today_total_portfolio_amount/len(empty_position_to_buy))

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
            if len(current_positions) == self.holding_num:  # 持仓数量符合要求，只进行仓位增补，不进行换仓操作
                # 今日调仓金额，正数为需要买入的金额，负数为需要卖出的金额
                today_to_buy_amount = self.today_total_portfolio_amount - self.context.stock_account.market_value
                current_positions_df = pd.DataFrame(columns=['order_book_id', 'market_value'])
                for position in current_positions:
                    line_item_dict = {
                        'order_book_id': position.order_book_id,
                        'market_value': position.market_value
                    }
                    current_positions_df = pd.concat([current_positions_df, pd.DataFrame(line_item_dict, index=[0])])
                current_positions_df['portion'] = current_positions_df['market_value'] / current_positions_df['market_value'].sum()
                current_positions_df['today_to_buy_amount'] = today_to_buy_amount * current_positions_df['portion']
                for index, line_item in current_positions_df.iterrows():
                    order_value(
                        line_item['order_book_id'], 
                        line_item['today_to_buy_amount']
                        )
                return
            # 处理新买入
            today_to_buy = sorted_df.loc[sorted_df['up'] > (
                self.trend_indicator_filter+self.trend_indicator_buffer)]

            # 此处需要测试：如果符合trend_indicator的标的数量小于目标持仓数量，要不要买？？
            if len(today_to_buy) < self.holding_num:
                logger.info(
                    f'符合要求的标的数量：{len(today_to_buy)}小于目标持仓量：{self.holding_num}，不操作，静待明天...')
                return
            ######
            today_to_buy_list = list(
                today_to_buy.iloc[:self.holding_num, ]['target'])
            today_holding_list = [x.order_book_id for x in current_positions]
            today_to_buy_list = list(
                set(today_to_buy_list).difference(set(today_holding_list)))
            if (len(today_to_buy_list)+len(today_holding_list)) > self.holding_num:  # 处理购买后超过持仓上限的情形
                today_to_buy_list = list(
                    today_to_buy.iloc[:(self.holding_num-len(today_holding_list)), ]['target'])
            # 按照今天应有仓位总额，以及现有仓位总额，计算可用资金
            # TODO: 此处需要修改，不能用整体股票账户持仓金额变量，应该用当前target_list持仓金额
            total_available_amount = self.today_total_portfolio_amount - \
                self.context.stock_account.market_value
            for target in today_to_buy_list:
                logger.info(f'买入{target}...')
                order_target_value(
                    target, total_available_amount/len(today_to_buy_list))
