from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from statistics import mean

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
                1. 首先检查持仓中有哪些不符合条件需要卖出的。
                2. 调仓操作：建立仓位操作表，如果持仓数量不满，则根据现有持仓标的金额平均值补充虚拟持仓标的
                    -target- -持仓金额- -持仓比例- -今日目标金额-
                    -标的1-   -金额-    -比例-
                    -标的2-   -金额-    -比例-
                    -虚拟标的- -金额-    -比例-
                3. 根据今日目标股票总金额，按比例分配至不同标的（今日目标金额）
                4. 对比标的持仓金额和今日目标金额，操作买卖（数量不足100不操作）

        Args:
            sorted_df (_type_): _description_
        """
        current_positions = self.__get_stock_positions()

        if not current_positions:  # 当前空仓，按规则买入
            logger.info(f'当前空仓，按规则买入...')
            empty_position_to_buy = sorted_df.loc[sorted_df['up'] > (
                self.trend_indicator_filter+self.trend_indicator_buffer)]
            if empty_position_to_buy.empty:
                logger.info(f'没有符合要求的标的，静待明天...')
                return
            # # 此处需要测试：如果符合trend_indicator的标的数量小于目标持仓数量，要不要买？？
            # if len(empty_position_to_buy) < self.holding_num:
            #     logger.info(
            #         f'符合要求的标的数量：{len(empty_position_to_buy)}小于目标持仓量：{self.holding_num}，不操作，静待明天...')
            #     return
            # ######
            empty_position_to_buy = empty_position_to_buy.iloc[:self.holding_num, ]
            for target in empty_position_to_buy['target']:
                order_target_value(
                    target, self.today_total_portfolio_amount/self.holding_num)

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

            current_positions = self.__get_stock_positions()  # 卖出后重新获取仓位
            position_change_df = pd.DataFrame(
                columns=['order_book_id', 'holding_amount', 'holding_portion', 'today_target_amount'])
            for position in current_positions:  # 将当前持仓填入
                line_item_dict = {
                    'order_book_id': position.order_book_id,
                    'holding_amount': position.market_value,
                    'holding_portion': 0.0,
                    'today_target_amount': 0.0
                }
                position_change_df = pd.concat(
                    [position_change_df, pd.DataFrame(line_item_dict, index=[0])])
            if len(position_change_df) < self.holding_num:  # 持仓数量不足，加入虚拟持仓位（为方便计算比例）
                if position_change_df.empty:
                    holding_amount = 1
                else:
                    holding_amount = mean(
                        [holding['holding_amount'] for _, holding in position_change_df.iterrows()])
                for i in range(self.holding_num-len(position_change_df)):
                    line_item_dict = {
                        'order_book_id': f'V{i}',
                        'holding_amount': holding_amount,
                        'holding_portion': 0.0,
                        'today_target_amount': 0.0
                    }
                    position_change_df = pd.concat(
                        [position_change_df, pd.DataFrame(line_item_dict, index=[0])])

            # 计算当前持仓比例
            position_change_df['holding_portion'] = position_change_df['holding_amount'] / \
                position_change_df['holding_amount'].sum()
            # 填入今天应有仓位
            position_change_df['today_target_amount'] = self.today_total_portfolio_amount * \
                position_change_df['holding_portion']

            # 调整现有真实仓位
            for index, holding_position in position_change_df.iterrows():
                if holding_position['order_book_id'].startswith('V'):  # 忽略虚拟仓位
                    continue
                share_amount = abs(holding_position['today_target_amount']-holding_position['holding_amount']
                                   )/self.bar_dict[holding_position['order_book_id']].last
                if share_amount > 100:  # 交易量在100以上才操作，减少操作次数
                    order_target_value(
                        holding_position['order_book_id'], holding_position['today_target_amount'])

            current_positions = self.__get_stock_positions()
            if len(current_positions) < self.holding_num:  # 处理完真实仓位后，如果仍然不满
                today_to_buy = sorted_df.loc[sorted_df['up'] > (
                    self.trend_indicator_filter+self.trend_indicator_buffer)]
                # if len(today_to_buy) < self.holding_num:  # 符合要求数量小于持仓数量，说明形式不好，不操作
                #     logger.info(
                #         f'符合要求的标的数量：{len(today_to_buy)}小于目标持仓量：{self.holding_num}，不操作，静待明天...')
                #     return
                today_to_buy_list = list(
                    today_to_buy.iloc[:self.holding_num, ]['target'])
                today_holding_list = [
                    x.order_book_id for x in current_positions]
                today_to_buy_list = list(
                    set(today_to_buy_list).difference(set(today_holding_list)))
                if (len(today_to_buy_list)+len(today_holding_list)) > self.holding_num:  # 处理购买后超过持仓上限的情形
                    today_to_buy_list = list(
                        today_to_buy.iloc[:(self.holding_num-len(today_holding_list)), ]['target'])
                v_position_df = position_change_df[position_change_df['order_book_id'].str.startswith(
                    'V')].reset_index(drop=True)
                # if len(today_to_buy_list) != len(v_position_df):
                #     raise Exception('数量有误，程序错误！')
                for i in range(len(v_position_df)-len(today_to_buy_list)):
                    today_to_buy_list.append(pd.NaT)
                v_position_df['new_target'] = today_to_buy_list
                v_position_df.dropna(how='any', inplace=True)
                for index, row in v_position_df.iterrows():
                    share_amount = abs(
                        row['today_target_amount']-row['holding_amount'])/self.bar_dict[row['new_target']].last
                    if share_amount > 100:  # 交易量在100以上才操作，减少操作次数
                        order_target_value(
                            row['new_target'], row['today_target_amount'])

    def __get_stock_positions(self) -> list:
        return [position for position in get_positions() if position.order_book_id in self.target_list]
