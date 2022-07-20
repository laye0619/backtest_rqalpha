from backtest.strategy.bs_vaq import BalanceStrategyVaQ
from backtest.strategy.rs_smae import RotationStrategySmaEnergy
from rqalpha.apis import *
from backtest.utils import const



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
    
    context.bs_vaq_rs_smae_ind = BalanceStrategyVaQ(
        stock_strategy=context.rs_smae_ind,
        position_diff_threshold=context.position_diff_threshold,
        pct_period=context.pct_period,
        va_method=context.va_method,
        stock_position_multiples=context.stock_position_multiples
    )


def handle_bar(context, bar_dict):
    if pd.to_datetime(context.now.date()) not in context.check_date:
        return
    logger.info('Strategy executing...')
    context.bs_vaq_rs_smae_ind.bar_dict = bar_dict
    context.bs_vaq_rs_smae_ind.context = context
    context.bs_vaq_rs_smae_ind.transction(
        context.bs_vaq_rs_smae_ind.calculate_position())
