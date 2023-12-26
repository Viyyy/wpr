from typing import List
from pydantic import BaseModel, Field

class HeatMapConfig(BaseModel):
    ''' HeatMap配置
    :param drawSpeLayerArrow:是否只画指定高度的风场
    :param cbar_limit:风场颜色条范围
    :param cHeadMap:热力图颜色序列
    :param arrowWidth:折线图中风场箭头的箭杆宽度
    :param arrowHeadWidth:折线图中箭头相对于箭杆宽度的倍数
    :param arrowPivot:折线图中风场箭头的枢轴，即箭头的旋转中心，可选'tail'、'mid'、'middle'、'tip'
    :param arrowUnits:折线图中风场箭头尺寸（除长度外）以此单位的倍数计算，即选定单位后，箭头尺寸即是此单位的倍数，可选'width'、'height'、'dots'、'inches'、'x'、'y'、'xy'
    :param arrowScale_Units:折线图中风场箭头长度单位，可选'width'、'height'、'dots'、'inches'、'x'、'y'、'xy'
    :param cFraction:通过设置该变量调整colorbar的大小
    :param cPad:colorbar与主图的距离
    :param cbTickSize:colorbar数据字体大小
    :param cbTickWid:colorbar刻度线的宽度
    :param cbTickLen:colorbar刻度线的长度
    :param colorbarNticker:colorbar刻度个数
    :param picAxisLabelSize:坐标轴标题字体大小
    :param picTickSize:坐标轴字体大小
    :param rotXticks:横坐标旋转角度
    :param nXticks:横坐标刻度的个数
    :param nYticks:纵坐标刻度的个数
    :param use_en:图标文本是否使用英文，否则用中文
    :param txtLocX:标签x轴方向位置
    :param txtFontSize:标签字体大小
    :param txtFontColor:标签字体颜色
    :param cbUnitLocX:colorbar单位标签x轴方向位置
    :param cbUnitLocY:colorbar单位标签y轴方向位置
    :param picTitleSize:图片标题大小
    :param picTitleLoc:图片标题位置：left、center、right
    :param arrowLegendWS:热力图中风场图例的风速
    :param arrowLegendWD:热力图中风场图例的风向
    :param arrowLegendLoc_X:热力图中风场图例x轴方向位置，值越大距离y轴越远
    :param arrowLegendLoc_Y:热力图中风场图例y轴方向位置，值越小距离y轴越远
    :param arrowLegendColor:风场图例颜色
    :param arrowLegendTxtLoc_X:风场图例箭头到x的距离
    :param arrowLegendTxtLoc_Y:风场图例箭头到y的距离
    '''
    figsize: tuple = Field(default=(6,2), description='图片大小')
    dpi: int = Field(default=300, description='图片分辨率')
    drawSpeLayerArrow: bool = Field(default=True, description='是否只画指定高度的风场')
    cbar_limit: tuple = Field(default=(0,10), description='风场颜色条范围')
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
    cbUnitLocY: float = Field(default=-0.15, description='colorbar单位标签y轴方向位置')
    picTitleSize: int = Field(default=6, description='图片标题大小')
    picTitleLoc: str = Field(default='left', description='图片标题位置')
    arrowLegendWS: int = Field(default=10, description='热力图中风场图例的风速')
    arrowLegendWD: int = Field(default=270, description='热力图中风场图例的风向')
    arrowLegendLoc_X: float = Field(default=0.78, description='热力图中风场图例x轴方向位置')
    arrowLegendLoc_Y: float = Field(default=0.1, description='热力图中风场图例y轴方向位置')
    arrowLegendColor: str = Field(default='red', description='风场图例颜色')
    arrowLegendTxtLoc_X: int = Field(default=16, description='风场图例箭头到x的距离')
    arrowLegendTxtLoc_Y: float = Field(default=0.035, description='风场图例箭头到y的距离')
    