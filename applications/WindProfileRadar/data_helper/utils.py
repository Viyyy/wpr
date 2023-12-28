import numpy as np
import pandas as pd
from typing import Dict,List
import copy
import datetime

import api
from .schemas import WPR_DataType,WindFieldDataType,Pollutants
from ..data_helper.models import HeatMapData
from utils.common import get_time_str, TimeStr

MaxHeight =  3000

def get_height_list(wpr_data:Dict[str,pd.DataFrame],reverse:bool=True)->list:
    ''' 获取高度列表
    :param wpr_data:风廓线雷达数据
    :return list
    '''
    l = list(wpr_data.keys())[0]
    y_ticks = wpr_data[l][WPR_DataType.HEIGHT.value.col_name].values
    
    if reverse:
        y_ticks = y_ticks[::-1]
    return y_ticks

WPR_Data_Time_Key = TimeStr.YmdHMS

def remove_over_height_data(df:pd.DataFrame, item_time):
    dfSpeTimeData = df[df['timePoint']==item_time]
    dfSpeTimeData.sort_values(by=[WPR_DataType.HEIGHT.value.col_name],inplace=True)
    dfSpeTimeData=dfSpeTimeData.reset_index(drop=True)
    # 找到第一个'高度（米）'大于MaxHeight的index
    dfMaxHeight = dfSpeTimeData[dfSpeTimeData[WPR_DataType.HEIGHT.value.col_name] > MaxHeight]
    # 如果有大于MaxHeight的index的，删掉indexMaxHeight后面的值
    if len(dfMaxHeight)>0:
        indexMaxHeight = dfMaxHeight.index[0]
        dfSpeTimeData = dfSpeTimeData.iloc[:indexMaxHeight+1]

    key = get_time_str(pd.to_datetime(item_time),WPR_Data_Time_Key)
    return key, dfSpeTimeData
    
def get_WPR_data(stationCode,startTime,endTime)-> dict:
    ''' 获取风廓线雷达数据，并提取想要的数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    :return dict, key:文件名，val:pd.DataFrame
    '''
    data = api.get_WPR_data(stationCode,startTime,endTime)
    assert isinstance(data, dict)
    
    df = pd.DataFrame(data['data'])
    columns = WPR_DataType.get_require_cols()
    df = df[columns] # 只保留需要的数据
    lst_time = list(df.groupby('timePoint').groups.keys())

    # endregion
    results = {}
    
    for item_time in lst_time:
        k,v = remove_over_height_data(df, item_time)
        results[k] = v
        
    return results

def get_WPR_data_all(stationCode,startTime,endTime)-> HeatMapData:
    ''' 获取风廓线雷达数据，并提取想要的数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    :return dict, key:文件名，val:pd.DataFrame
    '''
    data = api.get_WPR_data(stationCode,startTime,endTime)
    assert isinstance(data, dict)
    
    df = pd.DataFrame(data['data'])
    columns = WPR_DataType.get_require_cols()
    df = df[columns] # 只保留需要的数据
    lst_time = list(df.groupby('timePoint').groups.keys())
    
    # region 尝试直接保留高度列表里的数据
    time_key,df0 = remove_over_height_data(df, lst_time[0])
    results[time_key] = df0
    height_list = df0[WPR_DataType.HEIGHT.value.col_name]
    height_list = height_list.sort_values(ascending=False) # 倒序
    for i in range(1, len(lst_time)+1):
        item_time = lst_time[i]
        df_time = df[df['timePoint']==item_time]
        key = get_time_str(pd.to_datetime(item_time),WPR_Data_Time_Key)
        time_list = pd.Series([key]*len(height_list))
        hws_data = pd.Series(height_list).apply(lambda x:get_wpr_data_by(df_time, WPR_DataType.HWS, by_val=x, by=WPR_DataType.HEIGHT.value.col_name))
        hwd_data = pd.Series(height_list).apply(lambda x:get_wpr_data_by(df_time, WPR_DataType.HWD, by_val=x, by=WPR_DataType.HEIGHT.value.col_name))
        vws_data = pd.Series(height_list).apply(lambda x:get_wpr_data_by(df_time, WPR_DataType.VWS, by_val=x, by=WPR_DataType.HEIGHT.value.col_name))
        df1 = pd.concat([time_list, height_list, hws_data, hwd_data, vws_data], axis=1, keys=columns)
        
    
    # 剩下的其他时间只保留高度列表里的数据
    
    # endregion
    results = {}
    
    for item_time in lst_time:
        k,v = remove_over_height_data(df, item_time)
        results[k] = v
        
    return results
  

def get_col_index(wpr_data):
    col_index = np.arange(0, len(wpr_data.keys()))
    return col_index

def get_wpr_data_by(wpr_data:pd.DataFrame,wpr_data_type:WPR_DataType,by_val,by:str,nan=np.NAN):
    ''' 根据by_val查找wpr的数据
    :param wpr_data:风廓线雷达数据
    :param by_val:查找值
    :param by:索引值
    :param nan:没有找到时的替代值
    :return pd.DataFrame
    '''
    result = nan
    try:
        df1 = wpr_data[wpr_data[by]==by_val]
        if len(df1)>0:
            result = df1.iloc[0][wpr_data_type.value.col_name]
    finally:
        return result


def get_wind_field_data(wpr_data, data_type:WPR_DataType|WindFieldDataType, height_list,index_col:TimeStr=TimeStr.HM)->pd.DataFrame:
    ''' 获取风场数据
    :param wpr_data:风廓线雷达数据
    :param wpr_data_type:风廓线雷达数据类型
    :param index_col:索引值的格式
    :return pd.DataFrame
    '''
    result = {}
    for key,df in wpr_data.items():
        # 热力图数据
        data = pd.Series(height_list).apply(lambda x:get_wpr_data_by(df, data_type, by_val=x, by=WPR_DataType.HEIGHT.value.col_name)).values
        datetime_ = datetime.datetime.strptime(key, WPR_Data_Time_Key.value)
        result[get_time_str(datetime_, index_col)] = copy.deepcopy(data)
        
    result = pd.DataFrame(result, index=height_list)
    return result

def get_add_x(h,c=0,min=-0.4):
    ''' 计算scale距离
    :param h:小时数
    :param c:截距
    :param min:极小值
    '''
    total_h=23
    a = (-min+c)/(total_h**2)
    b = (min-c)*2/total_h
    add_x = a * h**2 + b * h + c
    return add_x

def minus2rep(val ,rep=""):
    ''' 替换负数值为rep
    :param val:检查值
    :param rep:替换值
    '''
    result = rep
    try:
        val = float(val)
        if val>=0:
            result = val
    finally:
        return result
    
def remain_spe_row(wpr_data:Dict[str,pd.DataFrame],w_data:pd.DataFrame, upperLayer:int|float=MaxHeight, downLayer:int|float=0, nLayer:int=10):
    ''' 指定高度的风场
    :param wpr_data:风廓线雷达数据
    :param w_data:风场数据
    :param upperLayer:顶层高度
    :param downLayer:顶层高度
    :param nLayer:风场箭头的层数
    '''
    assert downLayer>=0 and upperLayer>downLayer and nLayer>0
    # w_data = pd.DataFrame(w_data)
    lstTime = list(wpr_data.keys())
    len_wpr_data = len(lstTime)
    # 获取全部高度
    yTicksAll = list(wpr_data[lstTime[0]][WPR_DataType.HEIGHT.value.col_name])

    # 确定要保留的各层高度
    yTicks = list(np.arange(downLayer,upperLayer,(upperLayer-downLayer)/nLayer))
    yTicks.append(upperLayer)
    # 找出各层高度的行索引
    heightIndex = []
    for item in yTicks:
        if item in yTicksAll:
            heightIndex.append(yTicksAll.index(item))
        else:
            try:
                yTickTemp = min(i for i in yTicksAll if i > item)
            except Exception as e:
                a = 1
            if yTicksAll.index(yTickTemp)not in heightIndex:
                heightIndex.append(yTicksAll.index(yTickTemp))
            else:
                continue

    for rowIndex in range(0, len(yTicksAll)):
        if rowIndex not in heightIndex:
            w_data.iloc[rowIndex] = [None]*len_wpr_data
    return w_data

def get_mask(ws_data):
    '''0值白化
    参数：
    - ws_data:风速数据
    '''
    mask = ws_data <= 0
    return mask

def calcUV(ws, wd, to_nan:bool=True):
    """ 以正北或正南方向为起点，逆时针旋转，将风向风速转换为U、V风量
    :param ws:风速
    :param wd:风向
    :param to_nan: 0值是否改为nan, 风速为0时不绘制风场箭头
    :return Tuple(np.ndarray) U、V风
    """
    U = -np.multiply(ws, np.sin(np.deg2rad(wd)))
    V = -np.multiply(ws, np.cos(np.deg2rad(wd)))
    if to_nan: #风速为0时不绘制风场箭头
        U[U == 0] = np.nan
        V[V == 0] = np.nan
    return U, V

def get_grid_coord(data: pd.DataFrame | np.ndarray, addition: float = 0.5):
    """ 坐标网格化

    参数:
    - data: pd.DataFrame | np.ndarray，输入的数据，可以是DataFrame或者NumPy数组。
    - addition: float，添加到坐标数组的额外值。

    返回值:
    - x: np.ndarray，x轴的网格坐标数组。
    - y: np.ndarray，y轴的网格坐标数组。
    """
    x, y = np.meshgrid((np.arange(0, data.shape[1])) + [addition], (np.arange(0, data.shape[0])) + [addition])
    return x, y

def get_pollutant_max(site_datas:List[pd.DataFrame]):
    '''
    获取污染物浓度变化图坐标的最大值
    '''
    concat_df = pd.concat(site_datas)
    concat_df.replace('—',np.NaN,inplace=True)
    pollutants = [Pollutants.NO2,Pollutants.O3,Pollutants.PM10,Pollutants.SO2]
    for p in pollutants:
        concat_df[p.value.col_name] = concat_df[p.value.col_name].astype('float32')
    
    left_max = max(np.nanmax(concat_df[Pollutants.O3.value.col_name]),np.nanmax(concat_df[Pollutants.PM10.value.col_name]))
    right_max = np.nanmax(concat_df[Pollutants.NO2.value.col_name])
    SO2_max = np.nanmax(concat_df[Pollutants.SO2.value.col_name])
    return left_max,right_max,SO2_max