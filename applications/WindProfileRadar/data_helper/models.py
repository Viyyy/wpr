import numpy as np
import pandas as pd
import copy

from .schemas import WindFieldDataType, WPR_DataType
from .utils import *

class SiteData():
    pass

class WindFieldData():
    def __init__(self, wpr_data, height_list, data_type:WindFieldDataType, drawSpeLayerArrow:bool=True):
        ''' 风场数据
        :param wpr_data:风廓线雷达数据
        :param height_list:高度列表
        :param data_type:风场数据类型
        :param drawSpeLayerArrow:是否只画指定高度的风场
        '''
        self._origin_ws = get_wind_field_data(wpr_data, data_type, height_list)
        match data_type:
            case WindFieldDataType.HWS:
                self._ws = copy.deepcopy(self._origin_ws)
                self._wd = get_wind_field_data(wpr_data, WPR_DataType.HWD, height_list)
                if drawSpeLayerArrow:
                    self._ws = remain_spe_row(wpr_data, self._ws)
                    self._wd = remain_spe_row(wpr_data, self._wd)
                    
            case WindFieldDataType.VWS:
                self._ws = self._origin_ws * 20 # 我也不知道这个20是什么
                if drawSpeLayerArrow:
                    self._ws = remain_spe_row(wpr_data, self._ws)
                self._wd = self._ws.applymap(lambda x: np.where(x != 0, 180, x))
            
        self._u, self._v = calcUV(self._ws, self._wd,to_nan=True)
        # self._ws.to_csv(f'{data_type.value.col_name}-ws.csv',encoding='utf-8',index=False)
        # self._wd.to_csv(f'{data_type.value.col_name}-wd.csv',encoding='utf-8',index=False)
        
    # region properties
    @property
    def OriginWS(self):
        '''原始风速数据'''
        return self._origin_ws
    
    @property
    def WS(self):
        '''风速数据'''
        return self._ws
    
    @property
    def WD(self):
        '''风向数据'''
        return self._wd
    
    @property
    def U(self):
        '''U风'''
        return self._u
    
    @property
    def V(self):
        '''V风'''
        return self._v
    # endregion
         
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
    def __init__(self, station_code, start_time, end_time, wpr_data,drawSpeLayerArrow:bool):
        self.station_code = station_code
        self.start_time = pd.to_datetime(start_time)
        self.end_time = pd.to_datetime(end_time)
        self.height_list = get_height_list(wpr_data)
        self.col_index = get_col_index(wpr_data)
        self.horizontal_wind = WindFieldData(wpr_data, self.height_list, WindFieldDataType.HWS,drawSpeLayerArrow)
        self.vertical_wind = WindFieldData(wpr_data, self.height_list, WindFieldDataType.VWS, drawSpeLayerArrow)
        self.grid = HeapMapGrid.create_grid(self.horizontal_wind.WS,addition=0.5)
        self.add_x = get_add_x(h=(self.end_time-self.start_time).total_seconds()/3600,c=-0.2) # Scalex轴方向上的偏移位置