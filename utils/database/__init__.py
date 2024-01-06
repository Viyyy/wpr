from sqlalchemy import create_engine,Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sys,os
from contextlib import ExitStack
from pathlib import Path
from sqlalchemy.engine import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.schema import MetaData
if sys.version_info < (3, 8):
    from importlib_metadata import entry_points, version
else:
    from importlib.metadata import entry_points, version
from ..config_manager import webConfig
from traceback import print_exc

if not os.path.exists('databases'):
    os.mkdir('databases')
    
class Config():
    def __init__(self, username, pwd, server, db, 
                 echo=webConfig.config['sqlalchemy']['echo'], pool_size=10, max_overflow = 20):
        self._username = username
        self._pwd = pwd
        self._server = server
        self._db = db
        
        self.echo = echo
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        
    @property
    def url(self):
        return f"mssql+pymssql://{self._username}:{self._pwd}@{self._server}/{self._db}"
        
def get_sqlite_engine(
    url:str,
    # encoding='utf-8',
    echo=True,
    connect_args={'check_same_thread': False}
):
    '''创建数据库引擎'''
    engine = create_engine(url=url, echo=echo, connect_args=connect_args)
    return engine

def get_engine_base(db_name:str, name:str='Base'):
    '''创建基本映射类'''
    Base = declarative_base(name=name)
    Base.__bind__key = db_name
    return Base

def get_all_orm(engine:Engine):
    '''
    获取所有orm类
    '''
    # 创建自动映射的基类
    Base = automap_base()

    # 使用 engine 进行元数据的自动反射
    Base.prepare(engine, reflect=True)
    
    return Base.classes

def get_local_session(engine:Engine):
    '''
    在SQLAlchemy中，CRUD都是通过会话(session)进行的，所以我们必须要先创建会话，每一个SessionLocal实例就是一个数据库session
    flush()是指发送数据库语句到数据库，但数据库不一定执行写入磁盘；commit()是指提交事务，将变更保存到数据库文件
    '''
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=True)
    return SessionLocal    
    
def generate_orm_from_config(config:Config, outfile:Path, tables=None,mode='w'):
    generate_orm(config.url, outfile, tables)
    
def generate_orm_from_engine(engine:Engine, outfile:Path, tables=None,mode='w'):
    generate_orm(url=None, outfile=outfile, tables=tables, mode=mode, engine=engine)

def generate_orm(url, outfile:Path, tables=None,mode='w', engine=None):
    '''
    生成sqlalchemy的orm类
    url:sqlalchemy数据库连接字符串
    outfile:输出文件
    tables:要输出的表，如果为空，则输出数据库里的所有表
    （这个其实是sqlacodegen=3.0.0b2里cli的main方法，只是封装成一个方法。）
    （安装sqlacodegen: !pip install sqlacodegen==3.0.0b2）
    '''
    options=[]
    schemas=None
    noviews=None
    generator="declarative"
    eps = entry_points()
    assert 'sqlacodegen.generators' in eps.keys(), '请先安装sqlacodegen：pip install sqlacodegen==3.0.0b2'
    generators = {ep.name: ep for ep in eps['sqlacodegen.generators']}
    # Use reflection to fill in the metadata
    if url is None and engine is not None:
        engine=engine
    elif isinstance(url,str):
        engine = create_engine(url,echo=True)
    metadata = MetaData()
    tables = tables.split(',') if tables else None
    schemas = schemas.split(',') if schemas else [None]
    for schema in schemas:
        metadata.reflect(engine, schema, not noviews, tables)

    # Instantiate the generator
    generator_class = generators[generator].load()
    generator = generator_class(metadata, engine,options)

    # Open the target file (if given)
    with ExitStack() as stack:
        if outfile:
            with open(outfile, mode, encoding='utf-8') as outfile:
                stack.enter_context(outfile)
                # Write the generated model code to the specified file or standard output
                outfile.write(generator.generate())
        else:
            sys.stdout.write(generator.generate())
