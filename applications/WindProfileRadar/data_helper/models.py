import numpy as np
import pandas as pd
import copy

from .schemas import WindFieldDataType, WPR_DataType
from .utils import calcUV, get_height_list, \
    get_wind_field_data, remain_spe_row, get_col_index, get_grid_coord, get_add_x

class SiteData():
    pass

class WindFieldData():
    def __init__(self, OriginWS, WS, WD):
        self.OriginWS = OriginWS
        self.WS = WS
        self.WD = WD
        self.U, self.V = calcUV(self.WS, self.WD,to_nan=True)
        # self.data_type = data_type
        
    # def __repr__(self) -> str:
    #     return self.data_type.value.name data_type:WindFieldDataType
    
    @classmethod
    def create_from_wpr_data(cls, wpr_data, height_list, data_type:WindFieldDataType, drawSpeLayerArrow:bool=True):
        ''' 从wpr数据创建风场数据（旧）
        :param wpr_data:风廓线雷达数据
        :param height_list:高度列表
        :param data_type:风场数据类型
        :param drawSpeLayerArrow:是否只画指定高度的风场
        '''
        _origin_ws = get_wind_field_data(wpr_data, data_type, height_list)
        match data_type:
            case WindFieldDataType.HWS:
                _ws = copy.deepcopy(_origin_ws)
                _wd = get_wind_field_data(wpr_data, WPR_DataType.HWD, height_list)
                if drawSpeLayerArrow:
                    _ws = remain_spe_row(wpr_data, _ws)
                    _wd = remain_spe_row(wpr_data, _wd)
                    
            case WindFieldDataType.VWS:
                _ws = _origin_ws * 20 # 我也不知道这个20是什么
                if drawSpeLayerArrow:
                    _ws = remain_spe_row(wpr_data, _ws)
                _wd = _ws.applymap(lambda x: np.where(x != 0, 180, x))

        return cls(_origin_ws, _ws, _wd)
         
class HeapMapGrid():
    '''热力图网格'''
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    @classmethod
    def create_grid(cls,data: pd.DataFrame | np.ndarray, addition: float = 0.5):
        x, y = get_grid_coord(data, addition)
        return cls(x, y)
    
class HeatMapData():
    def __init__(self, station_code, start_time, end_time,
            horizontal_wind:WindFieldData, vertical_wind:WindFieldData, height_list, col_index):
        self.station_code = station_code
        self.start_time = pd.to_datetime(start_time)
        self.end_time = pd.to_datetime(end_time)
        self.horizontal_wind = horizontal_wind
        self.vertical_wind = vertical_wind
        self.grid = HeapMapGrid.create_grid(self.horizontal_wind.WS,addition=0.5)
        self.col_index = col_index
        self.height_list = height_list
     
    @property
    def add_x(self):
        '''Scalex轴方向上的偏移位置'''
        return get_add_x(h=(self.end_time-self.start_time).total_seconds()/3600,c=-0.2)    
    
    @classmethod
    def create_from_wpr_data(cls, station_code, start_time, end_time, wpr_data,drawSpeLayerArrow:bool):
        ''' 通过wpr_data创建（旧）'''
        height_list = get_height_list(wpr_data)
        col_index = get_col_index(wpr_data)
        horizontal_wind = WindFieldData.create_from_wpr_data(wpr_data, height_list, WindFieldDataType.HWS,drawSpeLayerArrow)
        vertical_wind = WindFieldData.create_from_wpr_data(wpr_data, height_list, WindFieldDataType.VWS, drawSpeLayerArrow)
        
        return cls(station_code, start_time, end_time, horizontal_wind, vertical_wind, height_list, col_index)