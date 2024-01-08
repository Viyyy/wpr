
from utils.common import get_time_str,TimeStr
import datetime
from applications.WindProfileRadar.data_helper import get_heat_map_from_wdc
from apscheduler.schedulers.background import BackgroundScheduler,BlockingScheduler
from pytz import utc
from multiprocessing import Lock

def job(wpr_code='H0001'):
    date = datetime.date.today()
    date_str = get_time_str(date, TimeStr.Ymd)
    start_time_str = f'{date_str} 0:0:0'
    end_time_str = get_time_str(datetime.datetime.now()+datetime.timedelta(hours=1), TimeStr.YmdH00)
    print(f"{get_time_str(datetime.datetime.now(),TimeStr.YmdHMS)} 定时任务启动")
    heatmap_data = get_heat_map_from_wdc(station_code=wpr_code, start_time=start_time_str, end_time=end_time_str, drawSpeLayerArrow=True)
    if not (heatmap_data is None):
        print(f"{get_time_str(datetime.datetime.now(),TimeStr.YmdHMS)} 定时任务完成")

def job_test():
    with Lock() as lock:
        # print('job_test输出：',get_time_str(datetime.datetime.now(),TimeStr.YmdHMS))
        print('job_test输出：',datetime.datetime.now())
    
job_defaults = {
    'coalesce': True,
    'misfire_grace_time': None
}

def scheduler_updata_wdc(interval_minutes=60):
    scheduler = BackgroundScheduler(timezone=utc)
    # scheduler.add_job(job, "cron", hour=9, minute=00) # 定时启动
    scheduler.add_job(job, "interval", minutes=interval_minutes)
    scheduler.start()