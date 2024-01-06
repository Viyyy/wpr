from sqlalchemy import Column, String, Integer, Date, JSON, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from .database import Base
    
class THeightData(Base):
    __tablename__ = 'height_data'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    station_code = Column(String(20), nullable=False, comment='站点编码')
    date = Column(Date, nullable=False, comment='数据日期')
    height_list = Column(JSON, nullable=False, comment='高度列表')
    targeted_height_list = Column(JSON, nullable=False, comment='目标高度列表')
    targeted_height_index = Column(JSON, nullable=False, comment='目标高度列表索引值')
    
    finish_cached = Column(Boolean, default=False, nullable=False, comment='是否缓存完毕')
    
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(),comment='更新时间')
    soft_deleted = Column(Boolean, default=False, nullable=False, comment='软删除')
    
class TWindData(Base):
    __tablename__ = 'wind_data'
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hid = Column(Integer, ForeignKey('height_data.id'), nullable=False) # 关联THeightData的Id，外键
    height_data = relationship('THeightData', backref='wind_data')
    
    time_point = Column(DateTime, nullable=False, comment='数据时间')
    is_horizon = Column(Boolean, nullable=False, comment='是否为水平风场，否时则为垂直风场')
    
    origin_ws = Column(JSON, nullable=False, comment='原始风速数据列表')
    ws = Column(JSON, nullable=False, comment='风速数据列表')
    wd = Column(JSON, nullable=False, comment='风向数据列表')
    is_remained = Column(Boolean, default=True, comment='是否保留特定高度的风场数据')
    
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    soft_deleted = Column(Boolean, default=False, nullable=False, comment='软删除')
    
class TWindDataCombined(Base):
    __tablename__ = 'wind_data_combined'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    hid = Column(Integer, ForeignKey('height_data.id'), nullable=False,unique=True) # 关联THeightData的Id，外键
    height_data = relationship('THeightData', backref='wind_data_combined')
    is_remained = Column(Boolean, default=True, comment='是否保留特定高度的风场数据')
    
    time_cols = Column(JSON, default=[], nullable=False, comment='时间数据列表')
    
    OriginHWS = Column(JSON, default={}, nullable=False, comment='原始水平风速数据列表')
    HWS = Column(JSON, default={}, nullable=False, comment='水平风速数据列表')
    HWD = Column(JSON, default={}, nullable=False, comment='水平风向数据列表')
    
    OriginVWS = Column(JSON, default={}, nullable=False, comment='原始垂直风速数据列表')
    VWS = Column(JSON, default={}, nullable=False, comment='垂直风速数据列表')
    VWD = Column(JSON, default={}, nullable=False, comment='垂直风向数据列表')
    
    create_time = Column(DateTime, server_default=func.now(), comment='创建时间')
    soft_deleted = Column(Boolean, default=False, nullable=False, comment='软删除')