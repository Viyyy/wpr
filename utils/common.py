import os
import zipfile
import time
import random
from datetime import date, datetime
from enum import Enum
from decimal import Decimal,ROUND_HALF_EVEN# 四舍五入六成双

class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__

def dict_to_object(dict_obj):
    if not isinstance(dict_obj, dict):
        return dict_obj
    inst = Dict()
    for k, v in dict_obj.items():
        inst[k] = dict_to_object(v)
    return inst
    
def zip_folder(folder_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, folder_path))
                
def get_random_str(random_str:str = "viyi0806ying"):
    '''获取随机字符串'''
    random_str = list(random_str)
    random.shuffle(random_str)
    random_str = list(f"{time.time_ns()}_{''.join(random_str)}")
    random.shuffle(random_str)
    return ''.join(random_str)

class TimeStr(Enum):
    Ymd = "%Y-%m-%d"
    Ymd_CN = "%Y年%m月%d日"
    md_ = "%m-%d"
    md_CN = "%m月%d日"
    YmdH00 = "%Y-%m-%d %H:00:00"
    YmdHMS = "%Y-%m-%d %H:%M:%S"
    YmdHMS_Na = "%Y%m%d%H%M%S"
    YmdHMS_CN = "%Y年%m月%d日 %H时%M分%S秒"
    HM = "%H:%M"
    
def get_time_str(time_:datetime|date, type_:TimeStr):
    return time_.strftime(type_.value)

def round_half_even(value:float, num:int=1)->float:
    """
    对给定的浮点数进行四舍五入操作，并遵循四舍五入六成双的规则。

    Args:
        value (float): 待四舍五入的浮点数。
        num: 保留的小数位数，默认值为1，即保留1位小数。

    Returns:
        float: 四舍五入后的结果。
    """
    return float(Decimal(value).quantize(Decimal(f'{10**(-num)}'), rounding=ROUND_HALF_EVEN))

from PIL import Image

def concatenate_images_vertically(image_paths, output_path):
    """将多张图片竖向拼接成一张图片

    参数：
    - image_paths:包含图片路径的列表
    - output_path:输出图片的路径

    返回：
    输出图片
    """
    # 打开所有图片
    images = [Image.open(path) for path in image_paths]

    # 获取每张图片的宽度和高度
    width, height = images[0].size

    # 创建新的图片，高度为所有图片高度之和，宽度为其中一张图片的宽度
    new_width = width
    new_height = height * len(images)
    new_image = Image.new("RGB", (new_width, new_height))

    # 将所有图片依次粘贴到新的图片上
    for i, image in enumerate(images):
        new_image.paste(image, (0, height * i))

    # 保存拼接后的图片
    new_image.save(output_path)
    return output_path