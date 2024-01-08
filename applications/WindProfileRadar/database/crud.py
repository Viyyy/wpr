from sqlalchemy.orm import Session
from traceback import print_exc
from typing import List
from datetime import date
from .models import THeightData as Hdata
from .models import TWindData as Wdata
from .models import TWindDataCombined as WDataCombined
from .database import Base, engine
from utils.common import js2str

Base.metadata.create_all(bind=engine)
        
def add_height_data(db:Session, h_data:Hdata):
    try:
        find_ = db.query(Hdata).filter(Hdata.station_code==h_data.station_code, Hdata.date==h_data.date).first()
        if not find_:
            db.add(h_data)
            db.commit()
            db.refresh(h_data)
            return h_data
        else:
            return find_
    except Exception as e:
        print_exc()

def query_height_data(db:Session, station_code:str, date_:date):
    try:
        find_ = db.query(Hdata).filter(Hdata.station_code==station_code, Hdata.date==date_).first()
        if find_:
            return find_
    except Exception as e:
        print_exc()
        
def update_height_data(db:Session, h_data:Hdata):
    try:
        find_ = db.query(Hdata).filter(Hdata.date==h_data.date, Hdata.height_list==h_data.height_list).first()
        # 更新h_data
        if find_:
            find_.finish_cached = h_data.finish_cached
            db.commit()
            return find_
    except Exception as e:
        print_exc()


def add_wind_data(db:Session, w_data:Wdata):
    try:
        find_ = db.query(Wdata).filter(Wdata.hid==w_data.hid, Wdata.time_point==w_data.time_point,Wdata.is_horizon==w_data.is_horizon,Wdata.is_remained==w_data.is_remained).first()
        if not find_:
            db.add(w_data)
            db.commit()
            db.refresh(w_data)
            return w_data
    except Exception as e:
        print_exc()

def query_wind_datas(db:Session, hid:int, is_horizon:bool, is_remained:bool=True):
    try:
        result = db.query(Wdata).filter(Wdata.hid==hid, Wdata.is_horizon==is_horizon, Wdata.is_remained==is_remained)
        rows =  result.all()
        return rows
    except:
        print_exc()
        
def add_wind_data_combined(db:Session, w_data_combined:WDataCombined):
    try:
        find_ = db.query(WDataCombined).filter(WDataCombined.hid==w_data_combined.hid, WDataCombined.is_remained==w_data_combined.is_remained).first()
        if not find_:
            db.add(w_data_combined)
            db.commit()
            db.refresh(w_data_combined)
            return w_data_combined
        else:
            return find_
    except Exception as e:
        print_exc()
        
def query_wind_data_combined(db:Session, hid:int, is_remained:bool=True):
    try:
        result = db.query(WDataCombined).filter(WDataCombined.hid==hid, WDataCombined.is_remained==is_remained).first()
        return result
    except:
        print_exc()
        
def update_wind_data_combined(db:Session, w_data_combined:WDataCombined):
    try:
        find_ = db.query(WDataCombined).filter(WDataCombined.hid==w_data_combined.hid, WDataCombined.is_remained==w_data_combined.is_remained).first()
        # 更新w_data_combined
        if find_:
            find_.time_cols = w_data_combined.time_cols
            
            find_.OriginHWS = w_data_combined.OriginHWS
            find_.HWS = w_data_combined.HWS
            find_.HWD = w_data_combined.HWD
            
            find_.OriginVWS = w_data_combined.OriginVWS
            find_.VWS = w_data_combined.VWS
            find_.VWD = w_data_combined.VWD
            db.commit()
            return find_
        else:
            return add_wind_data_combined(db, w_data_combined)
    except Exception as e:
        print_exc()

        