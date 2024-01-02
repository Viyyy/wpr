import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor

import api
from .utils import remove_over_height_data, concat_series, remain_special_layers
from .models import HeatMapData, WindFieldData
from .schemas import WPR_DataType
from utils.common import get_time_str,TimeStr

def get_wpr_data_by_height_idx(wpr_data:pd.DataFrame,wpr_data_type:WPR_DataType,idx,nan=np.NAN):
    ''' 根据by_val查找wpr的数据
    :param wpr_data:风廓线雷达数据
    :param idx:索引值
    :param nan:没有找到时的替代值
    :return pd.DataFrame
    '''
    result = nan
    try:
        result = wpr_data.loc[idx][wpr_data_type.value.col_name]
    finally:
        return result

def get_wind_field_datas_by_height_idx(df:pd.DataFrame, item_time, height_list:pd.Series):
    df_time = df[df['timePoint']==item_time]
    hws_ = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.HWS, x))
    hwd_ = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.HWD, x))
    vws_ = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.VWS, x))
    return hws_, hwd_, vws_

def get_WPR_data_all(station_code,start_time,end_time,drawSpeLayerArrow:bool=True)-> HeatMapData:
    ''' 获取风廓线雷达数据，并提取想要的数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    
    :return HeatMapData
    '''
    data = api.get_WPR_data(station_code,start_time,end_time)
    assert isinstance(data, dict)
    
    df = pd.DataFrame(data['data'])
    columns = WPR_DataType.get_require_cols()
    df = df[columns] # 只保留需要的数据
    lst_time = list(df.groupby(WPR_DataType.TIMEPOINT.value.col_name).groups.keys())
    
    # region 保留高度列表里的数据
    _, df0 = remove_over_height_data(df, lst_time[0])
    height_list = df0[WPR_DataType.HEIGHT.value.col_name]
    height_list = height_list.sort_values(ascending=False) # 倒序
    
    HWS = []
    VWS = []
    HWD = []
    df.set_index(WPR_DataType.HEIGHT.value.col_name, inplace=True) # 设置高度为index，后面用高度索引查找数据
    # region 多进程读取数据
    with ProcessPoolExecutor() as pool:
        futures = []
        for item_time in lst_time:
            futures.append(pool.submit(get_wind_field_datas_by_height_idx, df, item_time, height_list))
        for f in futures:
            hws_, hwd_, vws_ = f.result()
            HWS.append(hws_)
            HWD.append(hwd_)
            VWS.append(vws_)
    # endregion

    time_cols = [get_time_str(pd.to_datetime(item_time),TimeStr.HM) for item_time in lst_time]
    col_index = np.arange(0, len(time_cols))
    HWS = concat_series(HWS, height_list, time_cols)
    VWS = concat_series(VWS, height_list, time_cols)
    HWD = concat_series(HWD, height_list, time_cols)
    
    HWS_ = HWS * 1
    HWD_ = HWD
    VWS_ = VWS * 20
    if drawSpeLayerArrow:
        HWS_ = remain_special_layers(HWS_)
        HWD_ = remain_special_layers(HWD)
        VWS_ = remain_special_layers(VWS_)
        
    VWD_ = VWS_.applymap(lambda x: np.where(x != 0, 180, x))
    # endregion

    horizontal_wind = WindFieldData(OriginWS=HWS, WS=HWS_, WD=HWD_) # 水平风场数据
    vertical_wind = WindFieldData(OriginWS=VWS, WS=VWS_, WD=VWD_) # 垂直风场数据

    result = HeatMapData(station_code=station_code,
        start_time=start_time, end_time=end_time,
        horizontal_wind=horizontal_wind, vertical_wind=vertical_wind,
        height_list=height_list, col_index=col_index
    )
        
    return result