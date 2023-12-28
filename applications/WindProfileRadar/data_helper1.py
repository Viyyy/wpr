import pandas as pd
import numpy as np
import copy
from enum import Enum
from typing import Dict,List
from datetime import datetime
# custom
import api
from utils.common import TimeStr,get_time_str

MaxHeight = 3000 # 垂直高度上限

class WPR_Annotaion:
    ''' WPR数据注释
    :param name:中文名
    :param col_name:原始列名
    :param label:英文名
    '''
    def __init__(self,name,col_name, label):
        self.col_name = col_name
        self.label = label
        self.name = name
        
class WPR_DataType(Enum):
    '''风廓线雷达数据类型'''
    CODE = WPR_Annotaion('站点编号', 'stationCode', '')
    TIMEPOINT = WPR_Annotaion('时间', 'timePoint', '')
    HEIGHT = WPR_Annotaion('高度（米）', 'height', 'Height (m)')
    HWD = WPR_Annotaion('水平风向 (度)', 'hwd', 'HWD (°)')
    HWS = WPR_Annotaion('水平风速（米/秒）', 'hws', 'HWS (m/s)')
    VWS = WPR_Annotaion('垂直风速（米/秒）', 'vws', 'VWS (m/s)')
    H_CRED = WPR_Annotaion('水平方向可信度', 'hCred', 'HCred')
    V_CRED = WPR_Annotaion('垂直方向可信度', 'vCred', 'VCred')
    RWS = WPR_Annotaion('径向风速（米/秒）', 'rws', 'RWS (m/s)')
    TURB = WPR_Annotaion('湍流强度', 'turbIntensity', 'TurbIntensity')
    SN = WPR_Annotaion('信噪比', 'sn', 'S/N')
    TEMP = WPR_Annotaion('地面温度（摄氏度）', 'temp', 'Temp (℃)')
    RH = WPR_Annotaion('相对湿度 （%%）', 'rh', 'RH (%)')
    H_SHERA = WPR_Annotaion('风切边系数', 'hshear', 'Hshear')

    @staticmethod
    def cols_dict()->dict:
        '''  return dict
            :key 原始WPR数据中的列名
            :value 新的列名（中文）
        '''
        return {a.value.name: a.value.col_name for a in WPR_DataType}

    @staticmethod
    def name_label_dict()->dict:
        '''  return dict
            :key WPR数据中文名
            :value 英文名（带单位）
        '''
        return {a.value.name: a.value.label for a in WPR_DataType}

    @staticmethod
    def require_cols()->list:
        ''' :return list 需要的数据的列名的列表 '''
        # 返回WPR_DataType里所有Annotation的一个列表：[a.col_name for a in WPR_DataType]
        return [a.value.col_name for a in WPR_DataType]

    @staticmethod
    def name_list()->list:
        ''' :return 需要的数据的中文名的列表'''
        return [a.value.name for a in WPR_DataType]
    
WPR_Data_Time_Key = TimeStr.YmdHMS

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
    lst_time = list(df.groupby('timePoint').groups.keys())
    results = {}

    for item_time in lst_time:
        df_time = df[df['timePoint']==item_time]
        dfSpeTimeData = df_time[WPR_DataType.require_cols()]
        dfSpeTimeData.sort_values(by=[WPR_DataType.HEIGHT.value.col_name],inplace=True)
        dfSpeTimeData=dfSpeTimeData.reset_index(drop=True)
        # 找到第一个'高度（米）'大于MaxHeight的index
        dfMaxHeight = dfSpeTimeData[dfSpeTimeData[WPR_DataType.HEIGHT.value.col_name] > MaxHeight]
        # 如果有大于MaxHeight的index的，删掉indexMaxHeight后面的值
        if len(dfMaxHeight)>0:
            indexMaxHeight = dfMaxHeight.index[0]
            dfSpeTimeData = dfSpeTimeData.iloc[:indexMaxHeight+1]

        key = get_time_str(pd.to_datetime(item_time),WPR_Data_Time_Key)
        results[key] = copy.deepcopy(dfSpeTimeData)
        
    return results
    
def get_heap_map_y_ticks(wpr_data:Dict[str,pd.DataFrame],reverse:bool=True)->list:
    ''' 获取热力图数据的y轴刻度
    :param wpr_data:风廓线雷达数据
    :return list
    '''
    l = list(wpr_data.keys())[0]
    y_ticks = wpr_data[l][WPR_DataType.HEIGHT.value.col_name].values
    
    if reverse:
        y_ticks = y_ticks[::-1]
    return y_ticks
    
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

def get_heat_map_data(wpr_data:Dict[str,pd.DataFrame], wpr_data_type:WPR_DataType, y_ticks:list,index_col:TimeStr=TimeStr.HM)->pd.DataFrame:
    ''' 从风廓线雷达数据获取热力图数据
    :param wpr_data:风廓线雷达数据
    :param wpr_data_type:风廓线雷达数据类型
    :param index_col:索引值的格式
    :return pd.DataFrame
    '''
    result = {}
    for key,df in wpr_data.items():
        # 热力图数据
        data = pd.Series(y_ticks).apply(lambda x:get_wpr_data_by(df, wpr_data_type, by_val=x, by=WPR_DataType.HEIGHT.value.col_name)).values
        datetime_ = datetime.strptime(key, WPR_Data_Time_Key.value)
        result[get_time_str(datetime_, index_col)] = copy.deepcopy(data)
        
    result = pd.DataFrame(result, index=y_ticks)
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

def calUV(ws, wd, to_nan:bool=True):
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

class PollutantAnnotation():
    def __init__(self, col_name, unit, unit_cn, label_plt, name_plt, name):
        ''' 污染物注释
        :param col_name:原始数据里的列名
        :param unit:英文单位
        :param unit_cn:中文单位
        :param label_plt:在图里的英文名称
        :param name_plt:在图里的中文名称
        :param name:中文名称
        '''
        self.col_name = col_name
        self.unit = unit
        self.unit_cn = unit_cn
        self.label_plt = label_plt
        self.name_plt = name_plt
        self.name = name
   
UNIT_UG = 'μg/$\mathregular{m^3}$'
UNIT_UG_CN = '微克/立方米'
UNIT_MG = 'mg/$\mathregular{m^3}$'
UNIT_MG_CN = '毫克/立方米'
class Pollutants(Enum):
    PM25 = PollutantAnnotation(col_name='pM25',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='P$\mathregular{M_{2.5}}$',name_plt='P$\mathregular{M_{2.5}}$',name='细颗粒物')
    PM10 = PollutantAnnotation(col_name='pM10',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='P$\mathregular{M_{10}}$',name_plt='P$\mathregular{M_{10}}$',name='可吸入颗粒物')
    NO2 = PollutantAnnotation(col_name='nO2',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='N$\mathregular{O_{2}}$',name_plt='N$\mathregular{O_{2}}$',name='二氧化氮')
    O3 = PollutantAnnotation(col_name='o3',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='$\mathregular{O_3}$',name_plt='$\mathregular{O_3}$',name='臭氧')
    SO2 = PollutantAnnotation(col_name='sO2',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='S$\mathregular{O_{2}}$',name_plt='S$\mathregular{O_{2}}$',name='二氧化硫')
    CO = PollutantAnnotation(col_name='cO',unit=UNIT_MG,unit_cn=UNIT_MG_CN,label_plt='CO',name_plt='CO',name='一氧化碳')
    AIRPRESS = PollutantAnnotation(col_name='airPress',unit='hPa',unit_cn='百帕',label_plt='AirPress',name_plt='气压',name='气压')
    RH = PollutantAnnotation(col_name='humidity',unit='%',unit_cn='%',label_plt='RH',name_plt='RH',name='相对湿度')
    TEMP = PollutantAnnotation(col_name='temperature',unit='℃',unit_cn='摄氏度',label_plt='Temp',name_plt='温度',name='温度')
    WD = PollutantAnnotation(col_name='windDirect',unit='℃',unit_cn='',label_plt='WD',name_plt='风向',name='风向')
    WS = PollutantAnnotation(col_name='windSpeed',unit='m/s',unit_cn='米/秒',label_plt='WS',name_plt='风速',name='风速')
    
    
def get_pol_max_min(site_datas:List[pd.DataFrame]):
    concat_df = pd.concat(site_datas)
    concat_df.replace('—',np.NaN,inplace=True)
    pollutants = [Pollutants.NO2,Pollutants.O3,Pollutants.PM10,Pollutants.SO2]
    for p in pollutants:
        concat_df[p.value.col_name] = concat_df[p.value.col_name].astype('float32')
    
    left_max = max(np.nanmax(concat_df[Pollutants.O3.value.col_name]),np.nanmax(concat_df[Pollutants.PM10.value.col_name]))
    right_max = np.nanmax(concat_df[Pollutants.NO2.value.col_name])
    SO2_max = np.nanmax(concat_df[Pollutants.SO2.value.col_name])
    return left_max,right_max,SO2_max