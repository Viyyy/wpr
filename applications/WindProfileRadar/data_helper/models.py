import numpy as np
import pandas as pd
import math

from utils.common import timestr2timedelta
from .utils import calcUV, get_grid_coord, get_add_x

class WindFieldData():
    ''' 风场数据
    
    属性：
    - OriginWS:原始风速数据
    - WS:处理后的风速数据
    - WD:处理后的风向数据
    - U:U风
    - V:V风
    '''
    def __init__(self, OriginWS, WS, WD):
        self.OriginWS = OriginWS
        self.WS = WS
        self.WD = WD
        self.U, self.V = calcUV(WS, WD,to_nan=True)
         
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
        self.grid = HeapMapGrid.create_grid(horizontal_wind.WS,addition=0.5)
        self.col_index = col_index
        self.height_list = height_list

    def get_last_time(self)->str:
        '''获取最后的风廓线雷达的时间'''
        hw_time = list(self.horizontal_wind.OriginWS.columns)

        time_delta = [timestr2timedelta(t, "%H:%M") for t in hw_time]
        max_time_delta = max(time_delta)
        last_time = hw_time[time_delta.index(max_time_delta)]
        return last_time
    
    def get_last_hour(self)->int:
        '''获取最后的风廓线雷达的小时-整点'''
        max_time_delta = timestr2timedelta(self.get_last_time(), "%H:%M")
        last_hour = math.floor(max_time_delta.total_seconds() / 3600)
        return last_hour
     
    @property
    def add_x(self):
        '''Scalex轴方向上的偏移位置'''
        return get_add_x(h=(self.end_time-self.start_time).total_seconds()/3600,c=-0.2)