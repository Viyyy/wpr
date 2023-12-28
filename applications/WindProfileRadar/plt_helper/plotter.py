from concurrent.futures import ThreadPoolExecutor
from typing import List
from matplotlib import pyplot as plt

from ..data_helper.utils import get_pollutant_max
from ..data_helper.models import HeatMapData
from ..data_helper.schemas import WindFieldDataType
from .configs import HeatMapConfig
from .utils import draw_wind_field_heat_map, draw_pollutant_plot
from utils.common import get_time_str, TimeStr

BaseDir = 'static/wpr'
class Plotter():
    def __init__(self, config:HeatMapConfig=HeatMapConfig()):
        self.config = config

    def draw(self, heatmap_data:HeatMapData, site_datas, sitenames, use_en:bool=True, base_dir=BaseDir)->List[str]:
        ''' 绘制风廓线雷达图
        
        参数：
        - heatmap_data: 热力图数据
        - site_datas: 站点污染物浓度数据
        - sitenames:站点名称
        - use_en:是否使用英文
        - base_dir:图片保存根目录
        
        返回：
        - 图片保存路径列表
        '''
        results = []
        # region init
        time_str = f"{get_time_str(heatmap_data.start_time,TimeStr.YmdHMS_Na)}--{get_time_str(heatmap_data.end_time,TimeStr.YmdHMS_Na)}"
        left_max, right_max, SO2_max = get_pollutant_max(site_datas)
        # endregion

        for _, dt in WindFieldDataType.__members__.items():
            savepath = f'{base_dir}/{heatmap_data.station_code}-{time_str}--{dt.value.col_name}.png'
            # TODO 用了seaborn的热力图，无法用多线程绘图
            results.append(draw_wind_field_heat_map( # target 
                savepath,dt, heatmap_data, self.config, use_en # args
            ))
        
        with ThreadPoolExecutor() as pool:
            futures = []
            for idx, site_data in enumerate(site_datas):
                savepath = f'{base_dir}/{heatmap_data.station_code}-{time_str}--{sitenames[idx]}.png'
                futures.append(pool.submit(
                    draw_pollutant_plot, # target
                    savepath, sitenames[idx], site_data, left_max, right_max, SO2_max, self.config, use_en # args
                ))
            
            for future in futures:
                results.append(future.result())
                            
        return results

        
        
    