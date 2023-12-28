import pandas as pd
import numpy as np
import copy
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor

import api
from .utils import get_WPR_data,remove_over_height_data, get_wpr_data_by, WPR_Data_Time_Key, concat_series, remain_spe_row_base
from .models import HeatMapData, WindFieldData
from .schemas import WPR_DataType
from utils.common import get_time_str,TimeStr


def get_wind_field_datas(df:pd.DataFrame, item_time, height_list):
    df_time = df[df['timePoint']==item_time]
    hws_ = pd.Series(height_list).apply(lambda x:get_wpr_data_by(df_time, WPR_DataType.HWS, by_val=x, by=WPR_DataType.HEIGHT.value.col_name))
    hwd_ = pd.Series(height_list).apply(lambda x:get_wpr_data_by(df_time, WPR_DataType.HWD, by_val=x, by=WPR_DataType.HEIGHT.value.col_name))
    vws_ = pd.Series(height_list).apply(lambda x:get_wpr_data_by(df_time, WPR_DataType.VWS, by_val=x, by=WPR_DataType.HEIGHT.value.col_name))
    return hws_, hwd_, vws_
    
    
def get_WPR_data_all(station_code,start_time,end_time,drawSpeLayerArrow:bool=True)-> HeatMapData:
    ''' 获取风廓线雷达数据，并提取想要的数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    :
    :return dict, key:文件名，val:pd.DataFrame
    '''
    data = api.get_WPR_data(station_code,start_time,end_time)
    assert isinstance(data, dict)
    
    df = pd.DataFrame(data['data'])
    columns = WPR_DataType.get_require_cols()
    df = df[columns] # 只保留需要的数据
    lst_time = list(df.groupby('timePoint').groups.keys())
    
    # region 尝试直接保留高度列表里的数据
    _,df0 = remove_over_height_data(df, lst_time[0])
    height_list = df0[WPR_DataType.HEIGHT.value.col_name]
    height_list = height_list.sort_values(ascending=False) # 倒序
    
    HWS = []
    VWS = []
    HWD = []    
    
    # region 多线程读取数据
    with ProcessPoolExecutor() as pool:
        futures = []
        for item_time in lst_time:
            futures.append(pool.submit(get_wind_field_datas, df, item_time, height_list))
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
    # endregion
    HWS_ = HWS * 1
    HWD_ = HWD
    VWS_ = VWS * 20
    height_list=list(height_list.values)
    if drawSpeLayerArrow:
        HWS_ = remain_spe_row_base(copy.deepcopy(HWS),height_list)
        HWD_ = remain_spe_row_base(HWD,height_list)
        VWS_ = remain_spe_row_base(VWS_,height_list)
    VWD_ = VWS_.applymap(lambda x: np.where(x != 0, 180, x))
    
    horizontal_wind = WindFieldData(OriginWS=HWS, WS=HWS_, WD=HWD_) # 水平风场数据
    vertical_wind = WindFieldData(OriginWS=VWS, WS=VWS_, WD=VWD_) # 垂直风场数据

    result = HeatMapData(station_code=station_code,
        start_time=start_time, end_time=end_time,
        horizontal_wind=horizontal_wind, vertical_wind=vertical_wind,
        height_list=height_list, col_index=col_index
    )
        
    return result