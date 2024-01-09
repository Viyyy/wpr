import pandas as pd
import numpy as np
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime
from fastapi import HTTPException

import api
from .utils import remove_over_height_data, concat_series, remain_special_layers, get_targeted_height_list
from .models import HeatMapData, WindFieldData
from .schemas import WPR_DataType
from utils.common import get_time_str,TimeStr
from ..database.crud import *
from ..database.database import SessionLocal

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

def get_heapmap(station_code,start_time,end_time,drawSpeLayerArrow:bool=True)-> HeatMapData:
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
        targeted_height_list = get_targeted_height_list(list(height_list))
        HWS_ = remain_special_layers(HWS_,targeted_height_list)
        HWD_ = remain_special_layers(HWD,targeted_height_list)
        VWS_ = remain_special_layers(VWS_,targeted_height_list)
        
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

def get_heatmap_from_wd(station_code, start_time, end_time,drawSpeLayerArrow:bool=True)-> HeatMapData:
    ''' 从数据库中获取风廓线雷达数据，并提取想要的数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    :param drawSpeLayerArrow:是否保留特定高度
    
    :return HeatMapData
    '''
    # 数据日期
    date_ = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').date()
    
    # region 查询WPR数据
    wpr_data = api.get_WPR_data(station_code,start_time,end_time)
    assert isinstance(wpr_data, dict)
    df = pd.DataFrame(wpr_data['data'])
    columns = WPR_DataType.get_require_cols()
    df = df[columns] # 只保留需要的数据
    lst_time = list(sorted(df.groupby(WPR_DataType.TIMEPOINT.value.col_name).groups.keys()))
    # endregion

    # region 查询高度数据
    with SessionLocal() as db:
        h_data = query_height_data(db, station_code=station_code, date_=date_)
    # 没有时新增
    if h_data is None:
        # 查询高度
        _, df0 = remove_over_height_data(df, lst_time[0])
        height_list = df0[WPR_DataType.HEIGHT.value.col_name]
        height_list = height_list.sort_values(ascending=False).tolist() # 倒序
        # 创建高度数据实例
        h_data = Hdata()
        h_data.date = date_
        h_data.station_code = station_code
        h_data.height_list = height_list
        h_data.targeted_height_list = get_targeted_height_list(height_list)
        h_data.targeted_height_index = [height_list.index(h) for h in h_data.targeted_height_list]
        
        with SessionLocal() as db:
            h_data = add_height_data(db, h_data=h_data)
    assert isinstance(h_data, Hdata)
    height_list = pd.Series(h_data.height_list)
    height_num = len(height_list)
    df.set_index(WPR_DataType.HEIGHT.value.col_name, inplace=True) # 设置高度为index，后面用高度索引查找数据
    # endregion 
    
    # region 查询风场数据
    with SessionLocal() as db:
        w_data_h = query_wind_datas(db, hid=h_data.id, is_horizon=True)
    # endregion
    
    # region 检查是否有新的数据
    time_point_ls = set([get_time_str(wd.time_point, TimeStr.YmdHMS) for wd in w_data_h])
    
    for t in lst_time:
        if t in time_point_ls:
            continue
        # region 新增风场数据
        df_time = df[df[WPR_DataType.TIMEPOINT.value.col_name]==t]
        t = pd.to_datetime(t).to_pydatetime()
        hws_origin = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.HWS, x)) # 原始水平风速
        hwd = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.HWD, x)) # 水平风场
        hws = hws_origin.tolist() # 水平风速

        vws_origin = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.VWS, x)) # 原始垂直风速
        vws = vws_origin * 20 # 垂直风速
        
        if drawSpeLayerArrow: # 保留特定高度
            hwd_remained = [None] * height_num # 保留后的水平风场
            hws_remained = [None] * height_num # 保留后的水平风速
            vws_remained = [None] * height_num # 保留后的垂直风速
            for idx in h_data.targeted_height_index:
                hwd_remained[idx] = hwd[idx]
                hws_remained[idx] = hws[idx]
                vws_remained[idx] = vws[idx]
            hwd = hwd_remained
            hws = hws_remained
            vws = vws_remained
        else:
            hwd = hwd.tolist()
            vws = vws.tolist()
        vwd = pd.Series(vws).apply(lambda x: np.where(x != 0, 180, x)).tolist()
        
        with SessionLocal() as db: # 新增水平风场数据
            hw_data = Wdata()
            hw_data.hid = h_data.id
            hw_data.time_point = t
            hw_data.is_horizon = True
            hw_data.is_remained = drawSpeLayerArrow
            hw_data.origin_ws = hws_origin.tolist()
            hw_data.ws = hws
            hw_data.wd = hwd
            add_wind_data(db, hw_data)
        
        with SessionLocal() as db: # 新增垂直风场数据
            vw_data = Wdata()
            vw_data.hid = h_data.id
            vw_data.time_point = t
            vw_data.is_horizon = False
            vw_data.is_remained = drawSpeLayerArrow
            vw_data.origin_ws = vws_origin.tolist()
            vw_data.ws = vws
            vw_data.wd = vwd
            add_wind_data(db, vw_data) 
        # endregion      
    # endregion
    
    # 重新查询数据
    with SessionLocal() as db:
        w_data_h = query_wind_datas(db, hid=h_data.id, is_horizon=True, is_remained=drawSpeLayerArrow)
        w_data_v = query_wind_datas(db, hid=h_data.id, is_horizon=False, is_remained=drawSpeLayerArrow)
        
    assert len(w_data_h) == len(w_data_v)
    time_cols = set([get_time_str(wd.time_point, TimeStr.HM) for wd in w_data_h])
    col_index = np.arange(0, len(time_cols))
    
    HWS = []
    HWS_ = []
    HWD_ = []
    for data in w_data_h:
        HWS.append(pd.Series(data.origin_ws))
        HWS_.append(pd.Series(data.ws))
        HWD_.append(pd.Series(data.wd))
        
    VWS = []
    VWS_ = []
    VWD_ = []
    for data in w_data_v:
        VWS.append(pd.Series(data.origin_ws))
        VWS_.append(pd.Series(data.ws))
        VWD_.append(pd.Series(data.wd))
        
    HWS = concat_series(HWS, height_list, time_cols)
    HWS_ = concat_series(HWS_, height_list, time_cols)
    HWD_ = concat_series(HWD_, height_list, time_cols)
    VWS = concat_series(VWS, height_list, time_cols)
    VWS_ = concat_series(VWS_, height_list, time_cols)
    VWD_ = concat_series(VWD_, height_list, time_cols)
    horizontal_wind = WindFieldData(OriginWS=HWS, WS=HWS_, WD=HWD_) # 水平风场数据
    vertical_wind = WindFieldData(OriginWS=VWS, WS=VWS_, WD=VWD_) # 垂直风场数据

    result = HeatMapData(station_code=station_code,
        start_time=start_time, end_time=end_time,
        horizontal_wind=horizontal_wind, vertical_wind=vertical_wind,
        height_list=height_list, col_index=col_index
    )

    return result
        
def get_heat_map_from_wdc(station_code, start_time, end_time,drawSpeLayerArrow:bool=True)-> HeatMapData:
    ''' 从数据库中获取风廓线雷达数据，并提取想要的数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    :param drawSpeLayerArrow:是否保留特定高度
    
    :return HeatMapData
    '''
    # 数据日期
    date_ = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S').date()
    with SessionLocal() as db:
        h_data = query_height_data(db, station_code=station_code, date_=date_)
    if isinstance(h_data, Hdata):
        if h_data.finish_cached == True:# 已经缓存完成的直接查询热力图结果
            with SessionLocal() as db:
                # 查询风场数据
                wind_data_combined = query_wind_data_combined(db, hid=h_data.id, is_remained=drawSpeLayerArrow)
            horizontal_wind, vertical_wind = get_hv_wind(wind_data_combined)
            
            col_index = np.arange(0, len(wind_data_combined.time_cols))
            result = HeatMapData(station_code=station_code,
                start_time=start_time, end_time=end_time,
                horizontal_wind=horizontal_wind, vertical_wind=vertical_wind,
                height_list=pd.Series(h_data.height_list), col_index=col_index
            )
            return result
        
    # region 查询WPR数据
    wpr_data = api.get_WPR_data(station_code,start_time,end_time)
    assert isinstance(wpr_data, dict)
    df = pd.DataFrame(wpr_data['data'])
    if len(df) == 0:
        raise HTTPException(status_code=400, detail=f'【{start_time}--{end_time}】WPR data is Empty')
    columns = WPR_DataType.get_require_cols()
    df = df[columns] # 只保留需要的数据
    lst_time = list(sorted(df.groupby(WPR_DataType.TIMEPOINT.value.col_name).groups.keys()))
    # endregion

    # region 高度数据没有时新增
    if h_data is None:
        # 查询高度
        _, df0 = remove_over_height_data(df, lst_time[0])
        height_list = df0[WPR_DataType.HEIGHT.value.col_name]
        height_list = height_list.sort_values(ascending=False).tolist() # 倒序
        # 创建高度数据实例
        h_data = Hdata()
        h_data.date = date_
        h_data.station_code = station_code
        h_data.height_list = height_list
        h_data.targeted_height_list = get_targeted_height_list(height_list)
        h_data.targeted_height_index = [height_list.index(h) for h in h_data.targeted_height_list]
        
        with SessionLocal() as db:
            h_data = add_height_data(db, h_data=h_data)
    assert isinstance(h_data, Hdata)
    
    height_list = pd.Series(h_data.height_list)
    height_num = len(height_list)
    df.set_index(WPR_DataType.HEIGHT.value.col_name, inplace=True) # 设置高度为index，后面用高度索引查找数据
    # endregion 
    
    # 查询风场数据
    with SessionLocal() as db:
        wind_data_combined = query_wind_data_combined(db, hid=h_data.id, is_remained=drawSpeLayerArrow)
    
    if wind_data_combined is None:
        # 创建一个新的数据
        wind_data_combined = WDataCombined()
        wind_data_combined.hid = h_data.id
        wind_data_combined.is_remained = drawSpeLayerArrow
        
        wind_data_combined.time_cols = []
        wind_data_combined.OriginHWS = {WPR_DataType.HEIGHT.value.col_name:h_data.height_list}
        wind_data_combined.HWS = {WPR_DataType.HEIGHT.value.col_name:h_data.height_list}
        wind_data_combined.HWD = {WPR_DataType.HEIGHT.value.col_name:h_data.height_list}
        
        wind_data_combined.OriginVWS = {WPR_DataType.HEIGHT.value.col_name:h_data.height_list}
        wind_data_combined.VWS = {WPR_DataType.HEIGHT.value.col_name:h_data.height_list}
        wind_data_combined.VWD = {WPR_DataType.HEIGHT.value.col_name:h_data.height_list}
        
    for t in lst_time:
        time_col = get_time_str(pd.to_datetime(t).to_pydatetime(), TimeStr.HM)
        if time_col in wind_data_combined.time_cols:
            continue
        wind_data_combined.time_cols.append(time_col)
        df_time = df[df[WPR_DataType.TIMEPOINT.value.col_name]==t]
        hws_origin = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.HWS, x)) # 原始水平风速
        hwd = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.HWD, x)) # 水平风场
        hws = hws_origin * 1 # 水平风速

        vws_origin = height_list.apply(lambda x:get_wpr_data_by_height_idx(df_time, WPR_DataType.VWS, x)) # 原始垂直风速
        vws = vws_origin * 20 # 垂直风速
        
        if drawSpeLayerArrow: # 保留特定高度
            hwd_remained = [None] * height_num # 保留后的水平风场
            hws_remained = [None] * height_num # 保留后的水平风速
            vws_remained = [None] * height_num # 保留后的垂直风速
            for idx in h_data.targeted_height_index:
                hwd_remained[idx] = hwd[idx]
                hws_remained[idx] = hws[idx]
                vws_remained[idx] = vws[idx]
            hwd = hwd_remained
            hws = hws_remained
            vws = vws_remained
        else:
            hwd = hwd.tolist()
            hws = hwd.tolist()
            vws = vws.tolist()
        vwd = pd.Series(vws).apply(lambda x: np.where(x != 0, 180, x)).tolist()
        
        wind_data_combined.OriginHWS[time_col] = hws_origin.tolist()
        wind_data_combined.HWS[time_col] = hws
        wind_data_combined.HWD[time_col] = hwd
        
        wind_data_combined.OriginVWS[time_col] = vws_origin.tolist()
        wind_data_combined.VWS[time_col] = vws
        wind_data_combined.VWD[time_col] = vwd
        
    # 更新数据库
    with SessionLocal() as db:
        wind_data_combined = update_wind_data_combined(db, wind_data_combined)
        horizontal_wind, vertical_wind = get_hv_wind(wind_data_combined)
    if pd.to_datetime(end_time).hour==23:
        with SessionLocal() as db:
            h_data.finish_cached = True
            update_height_data(db, h_data)
            

    col_index = np.arange(0, len(wind_data_combined.time_cols))
    result = HeatMapData(station_code=station_code,
        start_time=start_time, end_time=end_time,
        horizontal_wind=horizontal_wind, vertical_wind=vertical_wind,
        height_list=height_list, col_index=col_index
    )

    return result
        
def get_hv_wind(wind_data_combined:WDataCombined):
    OriginHWS = pd.DataFrame(wind_data_combined.OriginHWS).set_index(WPR_DataType.HEIGHT.value.col_name)
    HWS = pd.DataFrame(wind_data_combined.HWS).set_index(WPR_DataType.HEIGHT.value.col_name)
    HWD = pd.DataFrame(wind_data_combined.HWD).set_index(WPR_DataType.HEIGHT.value.col_name)
    
    OriginVWS = pd.DataFrame(wind_data_combined.OriginVWS).set_index(WPR_DataType.HEIGHT.value.col_name)
    VWS = pd.DataFrame(wind_data_combined.VWS).set_index(WPR_DataType.HEIGHT.value.col_name)
    VWD = pd.DataFrame(wind_data_combined.VWD).set_index(WPR_DataType.HEIGHT.value.col_name)

    horizontal_wind = WindFieldData(OriginWS=OriginHWS, WS=HWS, WD=HWD) # 水平风场数据
    vertical_wind = WindFieldData(OriginWS=OriginVWS, WS=VWS, WD=VWD) # 垂直风场数据

    return horizontal_wind, vertical_wind


    

