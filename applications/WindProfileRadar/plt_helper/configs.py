from typing import List
from pydantic import BaseModel, Field
from enum import Enum

from utils.common import TimeStr
from ..data_helper.utils import calcUV
from ..data_helper.schemas import Pollutants

class HeatMapConfig(BaseModel):
    ''' HeatMap配置
    - time_str_type:标题上的时间格式
    - position:图片的位置，[x0,y0,width,height]
    - drawSpeLayerArrow:是否只画指定高度的风场
    - cHeadMap:热力图颜色序列
    - arrowWidth:折线图中风场箭头的箭杆宽度
    - arrowHeadWidth:折线图中箭头相对于箭杆宽度的倍数
    - arrowPivot:折线图中风场箭头的枢轴，即箭头的旋转中心，可选'tail'、'mid'、'middle'、'tip'
    - arrowUnits:折线图中风场箭头尺寸（除长度外）以此单位的倍数计算，即选定单位后，箭头尺寸即是此单位的倍数，可选'width'、'height'、'dots'、'inches'、'x'、'y'、'xy'
    - arrowScale_Units:折线图中风场箭头长度单位，可选'width'、'height'、'dots'、'inches'、'x'、'y'、'xy'
    - cFraction:通过设置该变量调整colorbar的大小
    - cPad:colorbar与主图的距离
    - cbTickSize:colorbar数据字体大小
    - cbTickWid:colorbar刻度线的宽度
    - cbTickLen:colorbar刻度线的长度
    - colorbarNticker:colorbar刻度个数
    - picAxisLabelSize:坐标轴标题字体大小
    - picTickSize:坐标轴字体大小
    - rotXticks:横坐标旋转角度
    - nXticks:横坐标刻度的个数
    - nYticks:纵坐标刻度的个数
    - use_en:图标文本是否使用英文，否则用中文
    - txtLocX:标签x轴方向位置
    - txtFontSize:标签字体大小
    - txtFontColor:标签字体颜色
    - cbUnitLocX:colorbar单位标签x轴方向位置
    - cbUnitLocY:colorbar单位标签y轴方向位置
    - picTitleSize:图片标题大小
    - picTitleLoc:图片标题位置：left、center、right
    - arrowLegendWS:热力图中风场图例的风速
    - arrowLegendWD:热力图中风场图例的风向
    - arrowLegendLoc_X:热力图中风场图例x轴方向位置，值越大距离y轴越远
    - arrowLegendLoc_Y:热力图中风场图例y轴方向位置，值越小距离y轴越远
    - arrowLegendColor:风场图例颜色
    - arrowLegendTxtLoc_X:风场图例箭头到x的距离
    - arrowLegendTxtLoc_Y:风场图例箭头到y的距离
    '''
    time_str_type: TimeStr = Field(default=TimeStr.YmdHMS_Na, description='标题上的时间格式')
    position:List[float] = Field(default=[0.09,0.15,0.81,0.73], description='图片的位置，[x0,y0,width,height]')
    figsize: tuple = Field(default=(6,2), description='图片大小')
    dpi: int = Field(default=300, description='图片分辨率')
    drawSpeLayerArrow: bool = Field(default=True, description='是否只画指定高度的风场')
    cHeadMap: str = Field(default='jet', description='热力图颜色序列')
    arrowWidth: float = Field(default=0.004, description='折线图中风场箭头的箭杆宽度')
    arrowHeadWidth: int = Field(default=4, description='折线图中箭头相对于箭杆宽度的倍数')
    arrowPivot: str = Field(default='mid', description='折线图中风场箭头的枢轴')
    arrowUnits: str = Field(default='inches', description='折线图中风场箭头尺寸（除长度外）的单位')
    arrowScale_Units: str = Field(default='inches', description='折线图中风场箭头长度的单位')
    cFraction: float = Field(default=0.05, description='通过设置该变量调整colorbar的大小')
    cPad: float = Field(default=0.01, description='colorbar与主图的距离')
    cbTickSize: int = Field(default=6, description='colorbar数据字体大小')
    cbTickWid: float = Field(default=0.2, description='colorbar刻度线的宽度')
    cbTickLen: int = Field(default=1, description='colorbar刻度线的长度')
    colorbarNticker: int = Field(default=10, description='colorbar刻度个数')
    picAxisLabelSize: int = Field(default=6, description='坐标轴标题字体大小')
    picTickSize: int = Field(default=6, description='坐标轴字体大小')
    rotXticks: int = Field(default=-30, description='横坐标旋转角度')
    nXticks: int = Field(default=24, description='横坐标刻度的个数')
    nYticks: int = Field(default=10, description='纵坐标刻度的个数')
    use_en: bool = Field(default=True, description='图标文本是否使用英文')
    txtLocX: float = Field(default=0.72, description='标签x轴方向位置')
    txtLocY: float = Field(default=1.02, description='标签y轴方向位置')
    txtFontSize: int = Field(default=6, description='标签字体大小')
    txtFontColor: str = Field(default='k', description='标签字体颜色')
    cbUnitLocX: float = Field(default=1, description='colorbar单位标签x轴方向位置')
    cbUnitLocY: float = Field(default=-0.1, description='colorbar单位标签y轴方向位置')
    picTitleSize: int = Field(default=6, description='图片标题大小')
    picTitleLoc: str = Field(default='left', description='图片标题位置')
    arrowLegendWS: int = Field(default=10, description='热力图中风场图例的风速')
    arrowLegendWD: int = Field(default=270, description='热力图中风场图例的风向')
    arrowLegendLoc_X: float = Field(default=0.78, description='热力图中风场图例x轴方向位置')
    arrowLegendLoc_Y: float = Field(default=0.1, description='热力图中风场图例y轴方向位置')
    arrowLegendColor: str = Field(default='red', description='风场图例颜色')
    arrowLegendTxtLoc_X: int = Field(default=16, description='风场图例箭头到x的距离')
    arrowLegendTxtLoc_Y: float = Field(default=0.035, description='风场图例箭头到y的距离')
    
    @property
    def uv_legend(self):
        uLegend, vLegend = calcUV(self.arrowLegendWS, self.arrowLegendWD, to_nan=False)
        return uLegend,vLegend
       
class PolluntantPlot():
    ''' 污染物折线图
    - annotation:污染物注释
    - marker:标签样式
    - color:颜色
    - linestyle:线条样式
    '''
    def __init__(self, annotation:Pollutants,marker,color,linestyle='--'):
        self.annotation = annotation
        self.marker = marker
        self.color = color
        self.linestyle = linestyle
        
    def plot(self, ax, x, y, use_en:bool=True,marker_size=2, line_width=0.5):
        line = ax.plot(x, y, marker=self.marker, markersize=marker_size,
            ls=self.linestyle, linewidth=line_width, color=self.color,
            label=self.annotation.value.label_plt if use_en else self.annotation.value.name_plt)
        return line
    
class TargetPollutants(Enum):
    O3 = PolluntantPlot(annotation=Pollutants.O3, marker='s', color='red')
    PM10 = PolluntantPlot(annotation=Pollutants.PM10, marker='d', color='red')
    NO2 = PolluntantPlot(annotation=Pollutants.NO2, marker='o', color='blue',linestyle='-')
    PM25 = PolluntantPlot(annotation=Pollutants.PM25, marker='H', color='blue')
    SO2 = PolluntantPlot(annotation=Pollutants.SO2, marker='s', color='green')