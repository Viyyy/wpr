import uvicorn
import time
import datetime
from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.testclient import TestClient
# custom
from utils.config_manager import webConfig
from utils.router_manager import Router,RouterManager
import warnings
warnings.filterwarnings("ignore")
app = FastAPI(
    **webConfig.app['config'],
)

# 挂载静态文件
app.mount(path='/static',app=StaticFiles(directory='./static'), name='static')

# 设置跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins = webConfig.cors['allow_origins'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

# 自定义计时中间件
@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    start_time = time.time()
  
    response = await call_next(request)

    end_time = time.time()

    # 将处理时间添加到响应头中
    response.headers["X-Response-Time"] = str(end_time - start_time)

    return response

# 自定义异常处理中间件
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )
    
#region 动态添加路由
routers = [
    Router('WindProfileRadar',tags='WindProfileRadar',prefix='WPR'),
]

ROUTER_MANAGER = RouterManager(routers)
ROUTER_MANAGER.add_routers_to(app)
#endregion

#region 定时任务
scheduler = AsyncIOScheduler() # 实例化调度器

client = TestClient(app)

@scheduler.scheduled_job('interval', minutes=60) # 每60分钟更新一次当天的数据
async def get_WPR_img_job():
    # 获取今天到前30天的日期列表
    today = datetime.date.today()
    # 调用接口
    client.get('/WPR/Img', params={'date': today.strftime('%Y-%m-%d')})

# 每天12点执行一次
@scheduler.scheduled_job('cron', hour=23, minute=26) # 每天执行一次, 缓存近30天的数据
async def get_WPR_img_today():
    # 获取今天到前30天的日期列表
    today = datetime.date.today()
    dates = [today - datetime.timedelta(days=i) for i in range(1,31)]
    for date in dates:
        # 调用接口
        client.get('/WPR/Img', params={'date': date.strftime('%Y-%m-%d')})

@app.on_event("startup")
async def start_scheduler():
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()
#endregion

if __name__=='__main__':
    uvicorn.run(
        app="main:app",
        use_colors=True,
        workers=1,
        **webConfig.server
    )