import uvicorn
from fastapi import FastAPI
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