"""基于动量的大小盘风格轮动策略
"""
from backtest.strategy.rs_smae import RotationStrategySmaEnergy
from backtest.utils import const
from rqalpha.apis import *

def init(context):
    # 未知原因，log_level不能传入，此处手工设置
    logger.level_name = context.config.extra.log_level
    
    # 因为后续要做参数优化，而rqalpha传入参数在init之前，如果此处设置参数将会以此处参数为准，config传入参数失败，故统一处理为：
    # 1.不变参数在此设定
    # 2.可变参数通过config.extra.context_vars来传入，下面RSMomentum对象从context中读取
    
    context.target_list = list(const.TARGET_LIST['ind_rotation'].keys())

    context.rs_smae_ind = RotationStrategySmaEnergy(
        target_list=context.target_list,
        holding_num=context.holding_num[0],
        sma_period=context.sma_period[0],
        trend_indicator_filter=context.trend_indicator_filter[0],
        trend_indicator_buffer=context.trend_indicator_buffer[0],
        rank_indicator_buffer=context.rank_indicator_buffer[0]
    )


def handle_bar(context, bar_dict):
    if pd.to_datetime(context.now.date()) not in context.check_date:
        return
    logger.info('Strategy executing...')
    context.rs_smae_ind.today_total_portfolio_amount = context.stock_account.total_value
    context.rs_smae_ind.bar_dict = bar_dict
    context.rs_smae_ind.context = context
    context.rs_smae_ind.transction(context.rs_smae_ind.sort_target_list())
