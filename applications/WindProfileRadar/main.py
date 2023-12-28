from fastapi import APIRouter,Query
from typing import List
import datetime
import os
import pandas as pd
from starlette.responses import FileResponse
from starlette.background import BackgroundTask
# custom
from .data_helper import get_WPR_data,HeatMapData
from .plt_helper import Plotter
import api
from utils.common import TimeStr, get_time_str, get_random_str, concatenate_images_vertically

router = APIRouter()

SAVEDIR = 'static/tmp'

from time import time
@router.get('/Img')
def get_WPR_img(
    date:datetime.date|None|str=Query(default=None,description='日期'),
    wpr_code:str=Query('H0001',description='风廓线雷达站点编号'), 
    sitenames:List[str]= Query(['ShiLing','SuGang'], description='与编号对应的国控点名称'), 
    station_codes:List[str]=Query(["440600455",'440600405'], description='国控点编号')
):
    ''' 获取风廓线雷达图 '''
    # region 获取数据
    durations = []
    st = time()
    if date is None:
        date = datetime.date.today()
    date_str = date if isinstance(date, str) else get_time_str(date, TimeStr.Ymd)
    savepath = f'{SAVEDIR}/{wpr_code}_{date_str}_{get_random_str()}.png'
    start_time_str = f'{date_str} 0:0:0'
    end_time_str = f'{date_str} 23:0:0'
    end_time = pd.to_datetime(end_time_str)
    if end_time > (now:=datetime.datetime.now()):
        end_time_str = get_time_str(now+datetime.timedelta(hours=1), TimeStr.YmdH00)
    wpr_data = get_WPR_data(wpr_code, start_time_str, end_time_str)
    site_datas = [api.get_AQ_data(code,start_time_str, end_time_str) for code in station_codes]
    et = time()
    durations.append(et-st)
    # endregion

    # region 处理数据
    st = time()
    heatmap_data = HeatMapData(
        station_code=wpr_code, start_time=start_time_str, end_time=end_time_str, 
        wpr_data=wpr_data, drawSpeLayerArrow=True
    )
    et = time()
    durations.append(et-st)
    # endregion
    
    # region 绘制图片
    st = time()
    plotter = Plotter()
    results = plotter.draw(heatmap_data=heatmap_data,site_datas=site_datas,sitenames=sitenames,use_en=True)
    et = time()
    durations.append(et-st)
    # endregion

    # 将这些图片合并为一张图后返回
    st = time()
    concatenate_images_vertically(results, savepath)
    et = time()
    durations.append(et-st)
    print(durations)
    print('总耗时：', sum(durations))
    return FileResponse(
        savepath,
        filename=f'{wpr_code}_{date_str}.png',
        # background=BackgroundTask(lambda:(os.remove(savepath)))
    )