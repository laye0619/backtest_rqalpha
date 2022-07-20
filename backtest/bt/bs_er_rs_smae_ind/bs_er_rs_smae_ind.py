from backtest.strategy.bs_er import BalanceStrategyEquallyRisk
from backtest.strategy.rs_smae import RotationStrategySmaEnergy
from rqalpha.apis import *
from backtest.utils import const


def init(context):
    # 未知原因，log_level不能传入，此处手工设置
    logger.level_name = context.config.extra.log_level
    
    # for 参数优化程序，未知原因，参数放入了tuple
    if context.config.mod.sys_analyser.output_file:
        if not isinstance(context.config.mod.sys_analyser.output_file, str):
            context.config.mod.sys_analyser.output_file = context.config.mod.sys_analyser.output_file[0]

    # 因为后续要做参数优化，而rqalpha传入参数在init之前，如果此处设置参数将会以此处参数为准，config传入参数失败，故统一处理为：
    # 1.不变参数在此设定
    # 2.可变参数通过config.extra.context_vars来传入，下面RSMomentum对象从context中读取

    context.target_list = list(const.TARGET_LIST['ind_rotation'].keys())

    context.rs_smae_ind = RotationStrategySmaEnergy(
        target_list=context.target_list,
        holding_num=context.holding_num,
        sma_period=context.sma_period[0],
        trend_indicator_filter=context.trend_indicator_filter[0],
        trend_indicator_buffer=context.trend_indicator_buffer[0],
        rank_indicator_buffer=context.rank_indicator_buffer
    )

    context.bs_er_rs_smae_ind = BalanceStrategyEquallyRisk(
        stock_strategy=context.rs_smae_ind,
        position_diff_threshold=context.position_diff_threshold,
        va_pct_period=context.va_pct_period,
        va_method=context.va_method,
        vo_period=context.vo_period,
        stock_position_multiples=context.stock_position_multiples
    )
    context.bs_er_rs_smae_ind.get_vo()  # 初始化时生成波动率表


def handle_bar(context, bar_dict):
    if pd.to_datetime(context.now.date()) not in context.check_date:
        return
    logger.info('Strategy executing...')
    context.bs_er_rs_smae_ind.bar_dict = bar_dict
    context.bs_er_rs_smae_ind.context = context
    context.bs_er_rs_smae_ind.transction(
        context.bs_er_rs_smae_ind.calculate_position())

    # 交易完成后，传入账户总金额
    context.bs_er_rs_smae_ind.yesterday_total_value = context.stock_account.total_value
