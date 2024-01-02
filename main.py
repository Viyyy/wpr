import uvicorn
import time
from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
# custom
from utils.config_manager import webConfig
from utils.router_manager import Router,RouterManager
import warnings
warnings.filterwarnings("ignore")
app = FastAPI(
    **webConfig.app['config'],
)

@app.get("/index",tags=['index'], deprecated=True)
def index():
    '''弃用的方法'''
    return webConfig.app['config']['title']


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

#region 动态添加路由
routers = [
    Router('WindProfileRadar',tags='WindProfileRadar',prefix='WPR'),
]

ROUTER_MANAGER = RouterManager(routers)
ROUTER_MANAGER.add_routers_to(app)
#endregion

if __name__=='__main__':
    uvicorn.run(
        app="main:app",
        use_colors=True,
        workers=1,
        **webConfig.server
    )