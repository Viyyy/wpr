from enum import Enum

class WPR_Annotaion:
    ''' WPR数据注释
    :param name:中文名
    :param col_name:原始列名
    :param label:英文名
    '''
    def __init__(self,name,col_name, label, kwargs:dict=None):
        self.col_name = col_name
        self.label = label
        self.name = name
        if isinstance(kwargs, dict):
            for k,v in kwargs.items():
                setattr(self, k, v)
     
class WindFieldDataType(Enum):
    HWS = WPR_Annotaion('水平风速（米/秒）', 'hws', 'HWS (m/s)',{'cbar_limit':(0,10),'cmap':'jet'})
    VWS = WPR_Annotaion('垂直风速（米/秒）', 'vws', 'VWS (m/s)',{'cbar_limit':(-1,1),'cmap':'seismic'})
    
class WPR_DataType(Enum):
    '''风廓线雷达数据类型'''
    # CODE = WPR_Annotaion('站点编号', 'stationCode', '')
    TIMEPOINT = WPR_Annotaion('时间', 'timePoint', '')
    HEIGHT = WPR_Annotaion('高度（米）', 'height', 'Height (m)')
    HWS = WPR_Annotaion('水平风速（米/秒）', 'hws', 'HWS (m/s)')
    HWD = WPR_Annotaion('水平风向 (度)', 'hwd', 'HWD (°)')
    VWS = WPR_Annotaion('垂直风速（米/秒）', 'vws', 'VWS (m/s)')
    # H_CRED = WPR_Annotaion('水平方向可信度', 'hCred', 'HCred')
    # V_CRED = WPR_Annotaion('垂直方向可信度', 'vCred', 'VCred')
    # RWS = WPR_Annotaion('径向风速（米/秒）', 'rws', 'RWS (m/s)')
    # TURB = WPR_Annotaion('湍流强度', 'turbIntensity', 'TurbIntensity')
    # SN = WPR_Annotaion('信噪比', 'sn', 'S/N')
    # TEMP = WPR_Annotaion('地面温度（摄氏度）', 'temp', 'Temp (℃)')
    # RH = WPR_Annotaion('相对湿度 （%%）', 'rh', 'RH (%)')
    # H_SHERA = WPR_Annotaion('风切边系数', 'hshear', 'Hshear')
    
    @staticmethod
    def get_cols_dict()->dict:
        '''  return dict
            :key 原始WPR数据中的列名
            :value 新的列名（中文）
        '''
        return {a.value.name: a.value.col_name for a in WPR_DataType}

    @staticmethod
    def get_name_label_dict()->dict:
        '''  return dict
            :key WPR数据中文名
            :value 英文名（带单位）
        '''
        return {a.value.name: a.value.label for a in WPR_DataType}

    @staticmethod
    def get_require_cols()->list:
        ''' :return list 需要的数据的列名的列表 '''
        # 返回WPR_DataType里所有Annotation的一个列表：[a.col_name for a in WPR_DataType]
        return [a.value.col_name for a in WPR_DataType]

    @staticmethod
    def get_name_list()->list:
        ''' :return 需要的数据的中文名的列表'''
        return [a.value.name for a in WPR_DataType]
    
class PollutantAnnotation():
    def __init__(self, col_name, unit, unit_cn, label_plt, name_plt, name):
        ''' 污染物注释
        :param col_name:原始数据里的列名
        :param unit:英文单位
        :param unit_cn:中文单位
        :param label_plt:在图里的英文名称
        :param name_plt:在图里的中文名称
        :param name:中文名称
        '''
        self.col_name = col_name
        self.unit = unit
        self.unit_cn = unit_cn
        self.label_plt = label_plt
        self.name_plt = name_plt
        self.name = name
   
UNIT_UG = 'μg/$\mathregular{m^3}$'
UNIT_UG_CN = '微克/立方米'
UNIT_MG = 'mg/$\mathregular{m^3}$'
UNIT_MG_CN = '毫克/立方米'

class Pollutants(Enum):
    PM25 = PollutantAnnotation(col_name='pM25',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='P$\mathregular{M_{2.5}}$',name_plt='P$\mathregular{M_{2.5}}$',name='细颗粒物')
    PM10 = PollutantAnnotation(col_name='pM10',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='P$\mathregular{M_{10}}$',name_plt='P$\mathregular{M_{10}}$',name='可吸入颗粒物')
    NO2 = PollutantAnnotation(col_name='nO2',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='N$\mathregular{O_{2}}$',name_plt='N$\mathregular{O_{2}}$',name='二氧化氮')
    O3 = PollutantAnnotation(col_name='o3',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='$\mathregular{O_3}$',name_plt='$\mathregular{O_3}$',name='臭氧')
    SO2 = PollutantAnnotation(col_name='sO2',unit=UNIT_UG,unit_cn=UNIT_UG_CN,label_plt='S$\mathregular{O_{2}}$',name_plt='S$\mathregular{O_{2}}$',name='二氧化硫')
    CO = PollutantAnnotation(col_name='cO',unit=UNIT_MG,unit_cn=UNIT_MG_CN,label_plt='CO',name_plt='CO',name='一氧化碳')
    AIRPRESS = PollutantAnnotation(col_name='airPress',unit='hPa',unit_cn='百帕',label_plt='AirPress',name_plt='气压',name='气压')
    RH = PollutantAnnotation(col_name='humidity',unit='%',unit_cn='%',label_plt='RH',name_plt='RH',name='相对湿度')
    TEMP = PollutantAnnotation(col_name='temperature',unit='℃',unit_cn='摄氏度',label_plt='Temp',name_plt='温度',name='温度')
    WD = PollutantAnnotation(col_name='windDirect',unit='℃',unit_cn='',label_plt='WD',name_plt='风向',name='风向')
    WS = PollutantAnnotation(col_name='windSpeed',unit='m/s',unit_cn='米/秒',label_plt='WS',name_plt='风速',name='风速')