import pandas as pd
import numpy as np
import seaborn as sns
from typing import List
import matplotlib.pyplot as plt
from matplotlib import ticker
from matplotlib.patches import Rectangle
from enum import Enum
from pydantic import BaseModel, Field
# 让中文的地方显示出来
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# 统一修改字体
plt.rcParams['font.family'] = ['STSong']
# custom
from utils.common import TimeStr, get_time_str
from .data_helper import WPR_DataType,Pollutants,get_heap_map_y_ticks,get_heat_map_data,remain_spe_row,calUV,get_pol_max_min
PLOT_TYPES = [WPR_DataType.HWS,WPR_DataType.VWS]

class PolluntantPlot():
    ''' 污染物折线图
    :param annotation:污染物注释
    :param marker:标签样式
    :param color:颜色
    :param linestyle:线条样式
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

def get_add_x(h,c=0,min=-0.4):
    ''' 计算scale距离
    :param h:小时数
    :param c:截距
    :param min:极小值
    '''
    total_h=23
    a = (-min+c)/(total_h**2)
    b = (min-c)*2/total_h
    add_x = a * h**2 + b * h + c
    return add_x

def minus2rep(val ,rep=""):
    ''' 替换负数值为rep
    :param val:检查值
    :param rep:替换值
    '''
    result = rep
    try:
        val = float(val)
        if val>=0:
            result = val
    finally:
        return result

class HeatMapConfig(BaseModel):
    figsize: tuple = Field(default=(6,2), description='图片大小')
    dpi: int = Field(default=300, description='图片分辨率')
    drawSpeLayerArrow: bool = Field(default=True, description='是否只画指定高度的风场')
    hw_limit: tuple = Field(default=None, description='水平风场颜色条范围')
    vw_limit: tuple = Field(default=None, description='垂直风场颜色条范围')
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
    

def drawWind(savepath,
data_type:WPR_DataType,
x,y,u,v,y_ticks,dfWS_H,colIndex,data:pd.DataFrame,time_label:str,arrowLocX:float,
cHeadMap="jet",hw_limit:tuple|None=(0,10),arrowWidth=0.004, arrowHeadWidth=4, arrowPivot='mid', arrowUnits='inches', arrowScale_Units='inches', 
cFraction=0.05, cPad=0.01, cbTickSize=6, cbTickWid=0.2, cbTickLen=1,colorbarNticker=10,
picAxisLabelSize=6, picTickSize=6, rotXticks=-30, nXticks=24, nYticks=10, 
use_en:bool=True, txtLocX=0.72, txtLocY=1.02, txtFontSize=6, txtFontColor="k", 
cbUnitLocX=1, cbUnitLocY=-0.15, picTitleSize=6, picTitleLoc='left', 
arrowLegendWS=10, arrowLegendWD=270, arrowLegendLoc_X=0.78, arrowLegendLoc_Y=0.1, arrowLegendColor='red', arrowLegendTxtLoc_X=16, arrowLegendTxtLoc_Y=0.035,
figsize=FIGSIZE,dpi=DPI):
    ''' 绘制风场数据
    :param arrowLocX:箭头图例的位置
    :param data:风场数据
    :param time_label:时间标记
    :param cHeadMap:热力图颜色序列
    :param hw_limit:水平风场颜色条范围
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
    fig,ax = plt.subplots(1,1,figsize=figsize,dpi=dpi)
    fig.tight_layout()
    fig.subplots_adjust(left=None, bottom=None, top=None, hspace=None)
    # region 绘制水平风场
    # data = get_heat_map_data(wpr_data, wpr_data_type=PLOT_TYPES[0],y_ticks=y_ticks)
    # colIndex = np.arange(0, len(wpr_data.keys()))
    # data.columns = colIndex
    # 0值白化
    if PLOT_TYPES[0]!=WPR_DataType.VWS:
        mask = data <= 0
    # 画热力图
    tick_locator_H = ticker.MaxNLocator(nbins=colorbarNticker) if isinstance(hw_limit,tuple) else None
    if hw_limit is None:
        hw_limit = (None, None)
    figHeatmap_H = sns.heatmap(
        data, ax=ax, vmax=hw_limit[1], vmin=hw_limit[0], annot=False, cbar=False, xticklabels=True,
        yticklabels=True, mask=mask, cmap=cHeadMap)

    # # 画箭头
    q_H = ax.quiver(x, y, u, v, width=arrowWidth, headwidth=arrowHeadWidth,
        pivot=arrowPivot, units=arrowUnits, scale_units=arrowScale_Units, scale=100)
    # 加边框
    ax = plt.gca()
    rect = Rectangle((0, 0), ax.dataLim.bounds[2], ax.dataLim.bounds[3], linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(rect)
    # 添加热力图颜色条
    cbar_H = figHeatmap_H.figure.colorbar(figHeatmap_H.collections[0], fraction=cFraction, pad=cPad)
    cbar_H.ax.tick_params(labelsize=cbTickSize)
    cbar_H.outline.set_visible(False)
    cbar_H.ax.yaxis.set_tick_params(width=cbTickWid, length=cbTickLen, color='black')
    # y轴标题字体大小
    figHeatmap_H.yaxis.label.set_size(picAxisLabelSize)
    # 热力图坐标轴刻度标签大小设置
    figHeatmap_H.set_xticklabels(figHeatmap_H.get_xticklabels(), fontsize=picTickSize)
    figHeatmap_H.set_yticklabels(figHeatmap_H.get_yticklabels(), fontsize=picTickSize)
    
    # 将横坐标刻度标签替换为时间
    ax.set_xticks(colIndex)
    ax.set_xticklabels(dfWS_H.columns.tolist(), rotation=rotXticks)
    # 设置坐标轴刻度数量
    ax.locator_params(axis='x', nbins=nXticks)
    ax.locator_params(axis='y', nbins=nYticks)

    # 设置纵坐标标题
    if use_en:
        figHeatmap_H.set_ylabel(WPR_DataType.HEIGHT.value.label)
    else:
        figHeatmap_H.set_ylabel(WPR_DataType.HEIGHT.value.name)
        
    #region 向图中添加文本
    # 时间范围文本
    ax.text(txtLocX, txtLocY, time_label,
        fontdict={"size": txtFontSize,"color": txtFontColor}, transform=figHeatmap_H.transAxes)
    # 颜色条标题文本
    ax.text(cbUnitLocX, cbUnitLocY, PLOT_TYPES[0].value.label if use_en else PLOT_TYPES[0].value.name,
        fontdict={"size": txtFontSize,"color": txtFontColor}, transform=ax.transAxes)
    # 风场类型文本
    ax.set_title( "WindField_H" if use_en else "水平风场",
        fontdict={"fontsize": picTitleSize, 'fontweight': 'heavy'},
        loc=picTitleLoc, pad=txtLocY-1)
    #endregion
    
    #region 风场图例,TODO：图例位置不够自动化
    uLegend, vLegend = calUV(arrowLegendWS, arrowLegendWD, to_nan=False)
    # xLegend, yLegend = np.meshgrid(x.shape[1] * arrowLegendLoc_X, y.shape[0] * arrowLegendLoc_Y)
    q = ax.quiver(50, 150, uLegend, vLegend,
        color=arrowLegendColor, width=arrowWidth, headwidth=arrowHeadWidth,
        pivot=arrowPivot, units=arrowUnits, scale_units=arrowScale_Units, scale=100)

    # hour_delta = (end_time-start_time).total_seconds()/3600
    # add_x = get_add_x(h=hour_delta,c=-0.2)
    # arrowLocX = (x.shape[1]*arrowLegendLoc_X-arrowLegendTxtLoc_X)/x.shape[1]+add_x
    ax.quiverkey(q ,0.2+arrowLocX, 1.04,10,' ', labelpos='E') # labelpos 图例标签的位置，可以是'N'（北）、'S'（南）、'E'（东）或'W'（西）。这里的'E'表示图例标签位于箭头的东侧。

    txtTemp = f"Scale: {str(arrowLegendWS)} m/s" if use_en else f"风速：{str(arrowLegendWS)}米/秒"
    
    ax.text(arrowLocX, 0.95+arrowLegendLoc_Y-arrowLegendTxtLoc_Y,
        txtTemp, fontdict={"size": txtFontSize, "color": arrowLegendColor}, transform=figHeatmap_H.transAxes)
    fig.savefig(savepath,dpi=dpi)
    # endregion
    # endregion

def drawHeatMapMultiVar(
    savepath:str,
    wpr_data, sitenames:List[str],site_datas:List[pd.DataFrame], start_time, end_time, time_str_type:TimeStr=TimeStr.YmdHMS_Na,
    drawSpeLayerArrow:bool=True,hw_limit:tuple|None=(0,10),vw_limit:tuple|None=(-1,1),
    cHeadMap="jet", arrowWidth=0.004, arrowHeadWidth=4, arrowPivot='mid', arrowUnits='inches', arrowScale_Units='inches',
    cFraction=0.05, cPad=0.01, cbTickSize=6, cbTickWid=0.2, cbTickLen=1,colorbarNticker=10, 
    picAxisLabelSize=6, picTickSize=6, rotXticks=-30, nXticks=24, nYticks=10, 
    use_en:bool=True, txtLocX=0.72, txtLocY=1.02, txtFontSize=6, txtFontColor="k", 
    cbUnitLocX=1, cbUnitLocY=-0.15, picTitleSize=6, picTitleLoc='left', 
    arrowLegendWS=10, arrowLegendWD=270, arrowLegendLoc_X=0.78, arrowLegendLoc_Y=0.1, arrowLegendColor='red', arrowLegendTxtLoc_X=16, arrowLegendTxtLoc_Y=0.035,
):
    """ 绘制水平风场、垂直风场和空气质量变化的组合图
    :param savepath:图片保存路径
    :param wpr_data:风廓线雷达数据
    :param sitenames:空气监测站点的名称
    :param site_datas:空气监测站点数据
    :param start_time:起始时间
    :param end_time:结束时间
    :param time_str_type:标题上的时间格式
    :param drawSpeLayerArrow:是否只画指定高度的风场
    :param hw_limit:水平风场颜色条范围
    :param vw_limit:垂直风场颜色条范围
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
    """
    fig_num = 2 + len(site_datas)
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)
    # 背景颜色数据
    y_ticks = get_heap_map_y_ticks(wpr_data)

    # region 风场数据
    dfWS_H = get_heat_map_data(wpr_data,WPR_DataType.HWS,y_ticks)
    dfWD_H = get_heat_map_data(wpr_data,WPR_DataType.HWD,y_ticks)
    dfWS_V = get_heat_map_data(wpr_data,WPR_DataType.VWS,y_ticks) * 20
    if drawSpeLayerArrow:
        dfWD_H = remain_spe_row(wpr_data, dfWD_H)
        dfWS_H = remain_spe_row(wpr_data, dfWS_H)
        dfWS_V = remain_spe_row(wpr_data, dfWS_V)
    dfWD_V = dfWS_V.applymap(lambda x: np.where(x != 0, 180, x))
    u_H, v_H = calUV(dfWS_H, dfWD_H, to_nan=True)
    u_V, v_V = calUV(dfWS_V, dfWD_V, to_nan=True)
    # endregion
    
    # 坐标网格化
    x, y = np.meshgrid((np.arange(0, dfWS_H.shape[1]))+[0.5], (np.arange(0, dfWS_H.shape[0]))+[0.5])

    # 创建画板
    plt.figure(figsize=(6,fig_num*2), dpi=300)
    plt.tight_layout()
    plt.subplots_adjust(left=None, bottom=None, top=None, hspace=0.5) #组合图中子图的垂直间距=0.5

    # region 绘制水平风场
    ax_H = plt.subplot(fig_num, 1, 1)
    CurrentDrawVari = get_heat_map_data(wpr_data, wpr_data_type=PLOT_TYPES[0],y_ticks=y_ticks)
    colIndex = np.arange(0, len(wpr_data.keys()))
    CurrentDrawVari.columns = colIndex
    # 0值白化
    if PLOT_TYPES[0]!=WPR_DataType.VWS:
        mask = CurrentDrawVari <= 0
    # 画热力图
    tick_locator_H = ticker.MaxNLocator(nbins=colorbarNticker) if isinstance(hw_limit,tuple) else None
    if hw_limit is None:
        hw_limit = (None, None)
    figHeatmap_H = sns.heatmap(
        CurrentDrawVari, ax=ax_H, vmax=hw_limit[1], vmin=hw_limit[0], annot=False, cbar=False, xticklabels=True,
        yticklabels=True, mask=mask, cmap=cHeadMap)

    # # 画箭头
    q_H = ax_H.quiver(x, y, u_H, v_H, width=arrowWidth, headwidth=arrowHeadWidth,
        pivot=arrowPivot, units=arrowUnits, scale_units=arrowScale_Units, scale=100)
    # 加边框
    ax_H = plt.gca()
    rect = Rectangle((0, 0), ax_H.dataLim.bounds[2], ax_H.dataLim.bounds[3], linewidth=2, edgecolor='black', facecolor='none')
    ax_H.add_patch(rect)
    # 添加热力图颜色条
    cbar_H = figHeatmap_H.figure.colorbar(figHeatmap_H.collections[0], fraction=cFraction, pad=cPad)
    cbar_H.ax.tick_params(labelsize=cbTickSize)
    cbar_H.outline.set_visible(False)
    cbar_H.ax.yaxis.set_tick_params(width=cbTickWid, length=cbTickLen, color='black')
    # y轴标题字体大小
    figHeatmap_H.yaxis.label.set_size(picAxisLabelSize)
    # 热力图坐标轴刻度标签大小设置
    figHeatmap_H.set_xticklabels(figHeatmap_H.get_xticklabels(), fontsize=picTickSize)
    figHeatmap_H.set_yticklabels(figHeatmap_H.get_yticklabels(), fontsize=picTickSize)
    
    # 将横坐标刻度标签替换为时间
    ax_H.set_xticks(colIndex)
    ax_H.set_xticklabels(dfWS_H.columns.tolist(), rotation=rotXticks)
    # 设置坐标轴刻度数量
    ax_H.locator_params(axis='x', nbins=nXticks)
    ax_H.locator_params(axis='y', nbins=nYticks)

    # 设置纵坐标标题
    if use_en:
        figHeatmap_H.set_ylabel(WPR_DataType.HEIGHT.value.label)
    else:
        figHeatmap_H.set_ylabel(WPR_DataType.HEIGHT.value.name)
        
    #region 向图中添加文本
    # 时间范围文本
    ax_H.text(txtLocX, txtLocY,f"{get_time_str(start_time,time_str_type)} ~ {get_time_str(end_time,time_str_type)}",
        fontdict={"size": txtFontSize,"color": txtFontColor}, transform=figHeatmap_H.transAxes)
    # 颜色条标题文本
    ax_H.text(cbUnitLocX, cbUnitLocY, PLOT_TYPES[0].value.label if use_en else PLOT_TYPES[0].value.name,
        fontdict={"size": txtFontSize,"color": txtFontColor}, transform=ax_H.transAxes)
    # 风场类型文本
    ax_H.set_title( "WindField_H" if use_en else "水平风场",
        fontdict={"fontsize": picTitleSize, 'fontweight': 'heavy'},
        loc=picTitleLoc, pad=txtLocY-1)
    #endregion
    
    #region 风场图例,TODO：图例位置不够自动化
    uLegend, vLegend = calUV(arrowLegendWS, arrowLegendWD, to_nan=False)
    # xLegend, yLegend = np.meshgrid(x.shape[1] * arrowLegendLoc_X, y.shape[0] * arrowLegendLoc_Y)
    q = ax_H.quiver(50, 150, uLegend, vLegend,
        color=arrowLegendColor, width=arrowWidth, headwidth=arrowHeadWidth,
        pivot=arrowPivot, units=arrowUnits, scale_units=arrowScale_Units, scale=100)

    hour_delta = (end_time-start_time).total_seconds()/3600
    add_x = get_add_x(h=hour_delta,c=-0.2)
    add_x1 = (x.shape[1]*arrowLegendLoc_X-arrowLegendTxtLoc_X)/x.shape[1]+add_x
    ax_H.quiverkey(q ,0.2+add_x1, 1.04,10,' ', labelpos='E') # labelpos 图例标签的位置，可以是'N'（北）、'S'（南）、'E'（东）或'W'（西）。这里的'E'表示图例标签位于箭头的东侧。

    txtTemp = f"Scale: {str(arrowLegendWS)} m/s" if use_en else f"风速：{str(arrowLegendWS)}米/秒"
    
    ax_H.text(add_x1, 0.95+arrowLegendLoc_Y-arrowLegendTxtLoc_Y,
        txtTemp, fontdict={"size": txtFontSize, "color": arrowLegendColor}, transform=figHeatmap_H.transAxes)
    # endregion
    # endregion

    # region 垂直风场
    ax_V = plt.subplot(fig_num, 1, 2)
    # 0值白化
    CurrentDrawVari = get_heat_map_data(wpr_data, wpr_data_type=PLOT_TYPES[1],y_ticks=y_ticks)
    CurrentDrawVari.columns = colIndex
    CurrentDrawVari.columns = colIndex
    if PLOT_TYPES[1] != WPR_DataType.VWS:
        mask=CurrentDrawVari<=0
        
    tick_locator_V = ticker.MaxNLocator(nbins=colorbarNticker) if isinstance(vw_limit,tuple) else None
    if vw_limit is None:
        vw_limit = (None, None)
    figHeatmap_V = sns.heatmap(CurrentDrawVari, ax=ax_V, vmax=vw_limit[1], vmin=vw_limit[0], annot=False,
        cbar=False, xticklabels=True, yticklabels=True, mask=mask, cmap='seismic')
    # 画箭头
    q_V = ax_V.quiver(x, y, u_V, v_V, width=arrowWidth, headwidth=arrowHeadWidth, pivot=arrowPivot,
        units=arrowUnits, scale_units=arrowScale_Units, scale=100)
    # 加边框
    ax_V = plt.gca()
    rect = Rectangle((0, 0), ax_V.dataLim.bounds[2], ax_V.dataLim.bounds[3],
                     linewidth=2, edgecolor='black', facecolor='none')
    ax_V.add_patch(rect)

    cbar_V = figHeatmap_V.figure.colorbar(figHeatmap_V.collections[0], fraction=cFraction, pad=cPad)
    cbar_V.ax.tick_params(labelsize=cbTickSize)
    cbar_V.outline.set_visible(False)
    cbar_V.ax.yaxis.set_tick_params(width=cbTickWid, length=cbTickLen, color='black')
    figHeatmap_V.yaxis.label.set_size(picAxisLabelSize)
    figHeatmap_V.set_xticklabels(figHeatmap_V.get_xticklabels(), fontsize=picTickSize)
    figHeatmap_V.set_yticklabels(figHeatmap_V.get_yticklabels(), fontsize=picTickSize)
    ax_V.set_xticks(colIndex)
    ax_V.set_xticklabels(dfWS_V.columns.tolist(), rotation=rotXticks)
    ax_V.locator_params(axis='x', nbins=nXticks)
    ax_V.locator_params(axis='y', nbins=nYticks)
    figHeatmap_V.set_ylabel(WPR_DataType.HEIGHT.value.label if use_en else WPR_DataType.HEIGHT.value.name)
    ax_V.text(cbUnitLocX, cbUnitLocY,PLOT_TYPES[1].value.label if use_en else PLOT_TYPES[1].value.name,
              fontdict={"size": txtFontSize, "color": txtFontColor}, transform=ax_V.transAxes)
    ax_V.set_title("WindField_V" if use_en else "垂直风场",
        fontdict={"fontsize": picTitleSize, 'fontweight': 'heavy'}, loc=picTitleLoc, pad=txtLocY-1)

    q = ax_V.quiver(50, 150, uLegend, vLegend,
        color=arrowLegendColor, width=arrowWidth, headwidth=arrowHeadWidth,
        pivot=arrowPivot, units=arrowUnits, scale_units=arrowScale_Units, scale=100)

    ax_V.quiverkey(q,0.2+add_x1, 1.04,10,' ', labelpos='E')

    txtTemp = f"Scale: {str(arrowLegendWS/20)} m/s" if use_en else f"风速：{str(arrowLegendWS/20)}米/秒"

    ax_V.text(add_x1, 0.95+arrowLegendLoc_Y-arrowLegendTxtLoc_Y,
        txtTemp, fontdict={"size": txtFontSize, "color": arrowLegendColor}, transform=figHeatmap_V.transAxes)
    # endregion
    
    if tick_locator_H:
        cbar_H.locator = tick_locator_H
        cbar_H.update_ticks()
    if tick_locator_V:
        cbar_V.locator = tick_locator_V
        cbar_V.update_ticks()

    # region 污染物浓度变化
    left_max,right_max,SO2_max = get_pol_max_min(site_datas)
    for idx, site_data in enumerate(site_datas):
        ax_AQ = plt.subplot(fig_num, 1, idx+3)
        ax2 = ax_AQ.twinx()
        ax3 = ax_AQ.twinx()
        ax3.spines['right'].set_position(('outward', 15))
        
        data_AQ = site_data
        # 通过接口获取的空气质量数据是按时间倒序排列的，需重新排序
        data_AQ = data_AQ.sort_values(by=['timePoint'])
        # 获取时间列表
        lstTime_AQ = data_AQ['timePoint'].tolist()
        # 格式化时间列表
        xtickLabel = []
        for item in lstTime_AQ:
            datetime_ = pd.to_datetime(item)
            xtickLabel.append(get_time_str(datetime_, TimeStr.HM))
        x_plot = np.arange(0, len(xtickLabel))
        for item_pol in TargetPollutants:
            # 获取指定参数
            data_pol = data_AQ[item_pol.value.annotation.value.col_name].apply(lambda x:minus2rep(x, np.nan))

            match item_pol:
                case TargetPollutants.PM10 | TargetPollutants.O3:
                    item_pol.value.plot(ax=ax_AQ, x = x_plot, y = data_pol, use_en=use_en)
                case TargetPollutants.PM25 | TargetPollutants.NO2:
                    item_pol.value.plot(ax=ax2, x = x_plot, y = data_pol, use_en=use_en)
                case TargetPollutants.SO2:
                    item_pol.value.plot(ax=ax3, x = x_plot, y = data_pol, use_en=use_en)

        ax_AQ.set_ylim(bottom=0,top= left_max+3)
        ax_AQ.tick_params(labelsize=picTickSize)
        ax_AQ.tick_params(axis='y', color=TargetPollutants.O3.value.color)
        for t in ax_AQ.get_yticklabels():
            t.set_color(TargetPollutants.O3.value.color)
        ax_AQ.set_ylabel(TargetPollutants.O3.value.annotation.value.unit if use_en else TargetPollutants.O3.value.annotation.value.unit_cn,
                        fontdict={'size': picAxisLabelSize, 'color': TargetPollutants.O3.value.color})
        """locator = ticker.MaxNLocator(nbins=2)
        ax_AQ.yaxis.set_major_locator(locator)"""

        ax2.set_ylim(bottom=0,top=right_max+10)
        ax2.tick_params(labelsize=picTickSize)
        ax2.tick_params(axis='y', color=TargetPollutants.PM25.value.color)
        for t in ax2.get_yticklabels():
            t.set_color(TargetPollutants.PM25.value.color)
        ax2.set_ylabel(None)

        ax3.set_ylim(bottom=0,top=SO2_max+3)
        ax3.tick_params(labelsize=picTickSize)
        ax3.tick_params(axis='y', color=TargetPollutants.SO2.value.color)
        for t in ax3.get_yticklabels():
            t.set_color(TargetPollutants.SO2.value.color)
        ax3.set_ylabel(TargetPollutants.SO2.value.annotation.value.unit if use_en else TargetPollutants.SO2.value.annotation.value.unit_cn,
                        fontdict={'size': picAxisLabelSize, 'color': TargetPollutants.SO2.value.color})

        # 设置横坐标刻度个数
        ax_AQ.locator_params(axis='x', nbins=len(xtickLabel))
        # 设置横坐标范围，确保折线的起始位置在y轴
        ax_AQ.set_xlim(0, len(xtickLabel)-1)
        # 将横坐标刻度标签替换为时间，并选装刻度标签
        ax_AQ.set_xticklabels(xtickLabel, rotation=rotXticks)
        # 设置折线图标题，即参数名称
        ax_AQ.set_title('污染物浓度' if not use_en else sitenames[idx],
            fontdict={"fontsize": picTitleSize, 'fontweight': 'heavy'}, loc=picTitleLoc, pad=txtLocY)
        # 添加图例
        linesMajor, labelsMajor = ax_AQ.get_legend_handles_labels()
        linesMinor, labelsMinor = ax2.get_legend_handles_labels()
        linesMinor3, labelsMinor3 = ax3.get_legend_handles_labels()
        lines = linesMajor+linesMinor+linesMinor3
        labels = labelsMajor+labelsMinor+labelsMinor3
        leg = ax_AQ.legend(lines,
                        labels,
                        prop={'weight': 'normal', 'size': 6},
                        ncol=5,
                        loc=(0.41, 0.98))  # loc='lower left'  "upper left"
        # 去掉图例边框
        leg.get_frame().set_linewidth(0.0)
        leg.get_frame().set_facecolor('none')

        # 设置坐标轴刻度标签字体大小
        # plt.tick_params(labelsize=config.drawRadarAQ.picTickSize)

        # 重置折线图宽度，确保与上面热力图对齐
        pos = figHeatmap_V.get_position(original=True)
        pos1 = ax_AQ.get_position(original=True)
        ax_AQ.set_position([pos1.x0, pos1.y0, pos.width, pos1.height])
    # endregion

    # plt.show()
    plt.savefig(savepath, bbox_inches='tight')
    return savepath
