"""基于动量的大小盘风格轮动策略
"""
from backtest.rotation_strategy.strategy.rs_momentum import RSMomentum
from rqalpha.apis import *

TARGET_LIST = {
    'style_28': {
        '000903.XSHG': '中证100',
        '399006.XSHE': '创业板指'
    }
}


def init(context):   
    # 因为后续要做参数优化，而rqalpha传入参数在init之前，如果此处设置参数将会以此处参数为准，config传入参数失败，故统一处理为：
    # 1.不变参数在此设定
    # 2.可变参数通过config.extra.context_vars来传入，下面RSMomentum对象从context中读取
    
    context.target_list = list(TARGET_LIST['style_28'].keys())
    context.holding_num = 1,

    context.rs_momentum = RSMomentum(
        target_list=context.target_list,
        holding_num=context.holding_num[0],
        momentum_period=context.momentum_period[0],
        trend_indicator_filter=context.trend_indicator_filter[0],
        trend_indicator_buffer=context.trend_indicator_buffer[0],
    )


def handle_bar(context, bar_dict):
    if pd.to_datetime(context.now.date()) not in context.check_date:
        return
    logger.info('Strategy executing...')
    context.rs_momentum.bar_dict = bar_dict
    context.rs_momentum.context = context
    context.rs_momentum.transction(context.rs_momentum.sort_target_list())
