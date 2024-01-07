from fastapi import APIRouter,Query
from typing import List
import datetime
import os
import gc
import pandas as pd
from starlette.responses import FileResponse
from starlette.background import BackgroundTask
from concurrent.futures import ThreadPoolExecutor
# custom
from .data_helper import get_heapmap, get_heatmap_from_wd,get_heat_map_from_wdc
from .plt_helper import Plotter
import api
from utils.common import TimeStr, get_time_str, get_random_str, concatenate_images_vertically

router = APIRouter()

SAVEDIR = 'static/wpr'
if not os.path.exists(SAVEDIR):os.makedirs(SAVEDIR)

from apscheduler.schedulers.background import BackgroundScheduler

def job(wpr_code='H0001'):
    date = datetime.date.today()
    date_str = get_time_str(date, TimeStr.Ymd)
    start_time_str = f'{date_str} 0:0:0'
    end_time_str = get_time_str(datetime.datetime.now()+datetime.timedelta(hours=1), TimeStr.YmdH00)
    print(f"[{start_time_str}--{end_time_str}] 定时任务启动")
    heatmap_data = get_heat_map_from_wdc(station_code=wpr_code, start_time=start_time_str, end_time=end_time_str, drawSpeLayerArrow=True)
    if not (heatmap_data is None):
        print(f"[{start_time_str}--{end_time_str}] 定时任务完成")

scheduler = BackgroundScheduler()
scheduler.add_job(job, "cron", hour=6) # 定时启动
# scheduler.add_job(job, "interval", minutes=1) # 间隔一段时间启动
scheduler.start()

@router.get('/Img')
def get_WPR_img(
    date:datetime.date|None|str=Query(default=None,description='日期'),
    wpr_code:str=Query('H0001',description='风廓线雷达站点编号'), 
    sitenames:List[str]= Query(['ShiLing','SuGang'], description='与编号对应的国控点名称'), 
    station_codes:List[str]=Query(["440600455",'440600405'], description='国控点编号')
):
    ''' 从数据库中获取数据，并绘制风廓线雷达图 '''
    # region 获取数据与处理数据
    if date is None:
        date = datetime.date.today()
    date_str = date if isinstance(date, str) else get_time_str(date, TimeStr.Ymd)
    savepath = f'{SAVEDIR}/{wpr_code}_{date_str}_{get_random_str()}.png'
    start_time_str = f'{date_str} 0:0:0'
    end_time_str = f'{date_str} 23:0:0'
    end_time = pd.to_datetime(end_time_str)
    if end_time > (now:=datetime.datetime.now()):
        end_time_str = get_time_str(now+datetime.timedelta(hours=1), TimeStr.YmdH00)

    site_datas = []
    with ThreadPoolExecutor() as pool:
        futures = []
        for code in station_codes:
            futures.append(pool.submit(api.get_AQ_data,code,start_time_str, end_time_str))
        for f in futures:
            site_datas.append(f.result())

    heatmap_data = get_heat_map_from_wdc(station_code=wpr_code, start_time=start_time_str, end_time=end_time_str, drawSpeLayerArrow=True)
    # endregion
    
    # region 绘制图片
    plotter = Plotter()
    results = plotter.draw(heatmap_data=heatmap_data,site_datas=site_datas,sitenames=sitenames,use_en=True)
    # endregion

    # 将这些图片合并为一张图后返回
    concatenate_images_vertically(results, savepath)
    return FileResponse(
        savepath,
        filename=f'{wpr_code}_{date_str}.png',
        # background=BackgroundTask(lambda:(os.remove(savepath)))
        background=BackgroundTask(lambda:([os.remove(r) for r in results],gc.collect()))
    )
    
@router.get('/Img1',deprecated=True)
def get_WPR_img(
    date:datetime.date|None|str=Query(default=None,description='日期'),
    wpr_code:str=Query('H0001',description='风廓线雷达站点编号'), 
    sitenames:List[str]= Query(['ShiLing','SuGang'], description='与编号对应的国控点名称'), 
    station_codes:List[str]=Query(["440600455",'440600405'], description='国控点编号')
):
    ''' 获取风廓线雷达图_旧 '''
    # region 获取数据与处理数据
    if date is None:
        date = datetime.date.today()
    date_str = date if isinstance(date, str) else get_time_str(date, TimeStr.Ymd)
    savepath = f'{SAVEDIR}/{wpr_code}_{date_str}_{get_random_str()}.png'
    start_time_str = f'{date_str} 0:0:0'
    end_time_str = f'{date_str} 23:0:0'
    end_time = pd.to_datetime(end_time_str)
    if end_time > (now:=datetime.datetime.now()):
        end_time_str = get_time_str(now+datetime.timedelta(hours=1), TimeStr.YmdH00)

    site_datas = []
    with ThreadPoolExecutor() as pool:
        futures = []
        for code in station_codes:
            futures.append(pool.submit(api.get_AQ_data,code,start_time_str, end_time_str))
        for f in futures:
            site_datas.append(f.result())

    heatmap_data = get_heapmap(station_code=wpr_code, start_time=start_time_str, end_time=end_time_str)
    # endregion
    
    # region 绘制图片
    plotter = Plotter()
    results = plotter.draw(heatmap_data=heatmap_data,site_datas=site_datas,sitenames=sitenames,use_en=True)
    # endregion

    # 将这些图片合并为一张图后返回
    concatenate_images_vertically(results, savepath)
    return FileResponse(
        savepath,
        filename=f'{wpr_code}_{date_str}.png',
        # background=BackgroundTask(lambda:(os.remove(savepath)))
        background=BackgroundTask(lambda:([os.remove(r) for r in results],gc.collect()))
    )