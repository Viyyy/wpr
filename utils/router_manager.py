import importlib
from typing import List,Tuple
from traceback import print_exc
from fastapi import FastAPI,APIRouter,Depends

class Router:
    ''' 用于动态引入Router
        :param name:路由名称
        :param tags:API标签，可以是字符串或字符串列表
        :param prefix:路由前缀，不传prefix时默认prefix=name
        :param base:路由所在的根目录，默认为applications, base为空或None时，router为与main同一级的Router；
        router在多级目录下时，则base应设置为每一级目录的名称的元组，如：router在app/tools/spl，base=("app","tools","spl")
        :param dependencies: 路由依赖包，详看fastapi里关于Depends的文档
    '''
    def __init__(self, name:str, tags:str|List[str],prefix:str|None=None, base:str|Tuple[str]='applications', dependencies:List[Depends]=None):

        self.name = name
        if prefix is None:
            prefix = name
        if not prefix.startswith('/'):
            prefix = "/" + prefix
        self.prefix = prefix
        if isinstance(tags, str):
            self.tags = [tags]
        else:
            self.tags = tags
        self.dependencies = dependencies
        if base=="" or base is None:
            app = importlib.import_module(f'{name}')
        elif isinstance(base, tuple):
            base = '.'.join([str(b) for b in base])
            app = importlib.import_module(f'{base}.{name}')
        elif isinstance(base, str):
            app = importlib.import_module(f'{base}.{name}')
        self.router = app.router
            
class RouterManager:
    def __init__(self, routers:List[dict|Router], base:str|Tuple[str]='applications'):
        self.routers = []
        for router in routers:
            if isinstance(router, Router):
                self.routers.append(router)
            elif isinstance(router, dict):
                try:
                    self.routers.append(Router(base=base, **router))
                except:
                    print_exc()
                    
    def add_routers_to(self, app:FastAPI|APIRouter):
        '''添加路由到FastAPI app OR APIRouter'''
        for r in self.routers:
            if r.dependencies is None:
                app.include_router(r.router, prefix=r.prefix, tags=r.tags)
            else:
                app.include_router(r.router, prefix=r.prefix, tags=r.tags, dependencies=r.dependencies)