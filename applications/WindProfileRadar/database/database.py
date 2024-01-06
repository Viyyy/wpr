from utils.database import get_sqlite_engine,get_local_session,get_engine_base
from utils.config_manager import webConfig

DB_NAME = 'wpr'
URL = webConfig.sqlite_db[DB_NAME]['url']
engine = get_sqlite_engine(URL, echo=webConfig.config['sqlalchemy']['echo'])

Base = get_engine_base(db_name=DB_NAME, name=f'{DB_NAME}Base')

SessionLocal = get_local_session(engine=engine)