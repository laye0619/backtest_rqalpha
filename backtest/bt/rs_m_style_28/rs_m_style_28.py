"""基于动量的大小盘风格轮动策略
"""
from backtest.strategy.rs_m import RotationStrategyMomentum
from rqalpha.apis import *

TARGET_LIST = {
    'style_28': {
        '000903.XSHG': '中证100',
        '399006.XSHE': '创业板指'
    }
}


def init(context):
    # 未知原因，log_level不能传入，此处手工设置
    logger.level_name = context.config.extra.log_level
    
    # 因为后续要做参数优化，而rqalpha传入参数在init之前，如果此处设置参数将会以此处参数为准，config传入参数失败，故统一处理为：
    # 1.不变参数在此设定
    # 2.可变参数通过config.extra.context_vars来传入，下面RSMomentum对象从context中读取
    
    context.target_list = list(TARGET_LIST['style_28'].keys())
    context.holding_num = 1,

    context.rs_m_style_28 = RotationStrategyMomentum(
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
    context.rs_m_style_28.today_total_portfolio_amount = context.stock_account.total_value
    context.rs_m_style_28.bar_dict = bar_dict
    context.rs_m_style_28.context = context
    context.rs_m_style_28.transction(context.rs_m_style_28.sort_target_list())
