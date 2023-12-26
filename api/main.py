import requests
import pandas as pd
from typing import List
from utils.config_manager import webConfig

def get_headers(params:dict={}):
    headers = {
        "Content-Type": "application/json;charset=utf-8",
        'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36 QIHU 360SE'
    }
    for k,v in params.items():
        headers[k] = v
    return headers
    
def get_WPR_data(stationCode,startTime,endTime)->dict:
    ''' 获取风廓线雷达原始数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    :return dict
    '''
    api = webConfig.api.get('WPR')
    params = {
        'StationCode': stationCode,
        'StartTime': startTime,
        'EndTime': endTime,
        api['token']['key']:api['token']['value']
    }
    
    url = api['url']
    response = requests.get(url, params=params, headers=get_headers())

    # 检查响应状态码
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print('请求失败:', response.status_code, response.text)

def get_AQ_data(stationCodes:str|List[str],startTime,endTime)->pd.DataFrame:
    ''' 获取空气质量数据
    :param stationCode: 站点编码
    :param startTime:起始时间
    :param endTime:结束时间
    :return pd.DataFrame
    '''
    api = webConfig.api.get('AQ')
    Headers = get_headers(api['token'])
    url = api['url']
    params = {
        'StartDateTime':startTime,
        'EndDateTime':endTime,
        "Codes": stationCodes,
        'IsSK': 'true',
        'DataType': 'station',
        'CalcRegionAqiType': '0'
    }
    response = requests.get(url, params=params, headers=Headers)

    # 检查响应状态码
    if response.status_code == 200:
        data = response.json()
        # 处理返回的数据
        df = pd.DataFrame(data)
        return df
    else:
        print('请求失败:', response.status_code, response.text)