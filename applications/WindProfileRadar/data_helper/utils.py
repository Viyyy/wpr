import numpy as np
import math
import pandas as pd
from typing import Dict,List
from .schemas import WPR_DataType,Pollutants
from utils.common import get_time_str

MaxHeight =  3000 # 顶层高度
MinHeight = 0 # 底层高度
Layers = 10 # 风场箭头的层数
H = (MaxHeight-MinHeight)/Layers # 单层高度
Height_List = np.arange(MinHeight, MaxHeight+H, H) # 确定要保留的各层高度

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

def remove_over_height_data(df:pd.DataFrame, item_time):
    ''' 移除超出最大高度的数据
    TODO 优化算法
    '''
    dfSpeTimeData = df[df['timePoint']==item_time]
    dfSpeTimeData.sort_values(by=[WPR_DataType.HEIGHT.value.col_name],inplace=True)
    dfSpeTimeData=dfSpeTimeData.reset_index(drop=True)
    # 找到第一个'高度（米）'大于MaxHeight的index
    dfMaxHeight = dfSpeTimeData[dfSpeTimeData[WPR_DataType.HEIGHT.value.col_name] > MaxHeight]
    # 如果有大于MaxHeight的index的，删掉indexMaxHeight后面的值
    if len(dfMaxHeight)>0:
        indexMaxHeight = dfMaxHeight.index[0]
        dfSpeTimeData = dfSpeTimeData.iloc[:indexMaxHeight+1]

    key = get_time_str(pd.to_datetime(item_time),WPR_DataType.TIMEPOINT.value.key)
    return key, dfSpeTimeData

def concat_series(series_list:List[pd.Series], index_values, keys)->pd.DataFrame:
    ''' 合并Series
    
    参数：
    - series_list:序列列表
    - index_values:索引值
    - index_name:索引名称
    - keys:列名
    
    返回：
    - 合并后的DataFrame
    '''
    df:pd.DataFrame = pd.concat(series_list, axis=1, ignore_index=True)
    df.insert(0, WPR_DataType.HEIGHT.value.col_name, index_values)
    df.set_index(WPR_DataType.HEIGHT.value.col_name, inplace=True)
    df.columns = keys
    return df

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
   
def get_targeted_height_list(height_list):
    targeted_height_list = []
    for item in Height_List:
        if item in height_list:
            targeted_height_list.append(item)
        else:
            targeted_height_list.append(min(i for i in height_list if i > item))
    targeted_height_list = list(set(targeted_height_list))
    return targeted_height_list
    
def remain_special_layers(w_data:pd.DataFrame,targeted_height_list=None):
    ''' 指定高度的风场
    :param w_data:风场数据，index为height
    '''
    # 找出各层高度
    if targeted_height_list is None:
        height_list = w_data.index.values
        targeted_height_list = get_targeted_height_list(height_list)

    for idx, _ in w_data.iterrows():
        if idx not in targeted_height_list:
            w_data.loc[idx] = None
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
    pollutants = [Pollutants.NO2,Pollutants.O3,Pollutants.PM10,Pollutants.SO2,Pollutants.PM25]
    concat_df = concat_df[[p.value.col_name for p in pollutants]]
    concat_df = concat_df.astype('float32')
    
    left_max = math.ceil(concat_df[[Pollutants.PM10.value.col_name,Pollutants.O3.value.col_name]].max().max())
    right_max = math.ceil(concat_df[[Pollutants.NO2.value.col_name,Pollutants.PM25.value.col_name]].max().max())
    SO2_max = np.nanmax(concat_df[Pollutants.SO2.value.col_name])
    
    return left_max,right_max,SO2_max