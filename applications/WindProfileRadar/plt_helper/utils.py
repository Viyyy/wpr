import matplotlib.pyplot as plt
import matplotlib
from matplotlib import ticker
from matplotlib.patches import Rectangle
import seaborn as sns
import pandas as pd
import numpy as np

from utils.common import get_time_str, TimeStr
from .configs import HeatMapConfig,TargetPollutants
from ..data_helper.models import HeatMapData
from ..data_helper.schemas import WPR_DataType
from ..data_helper.schemas import WindFieldDataType
from ..data_helper.utils import minus2rep

matplotlib.use('Agg')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']
# 统一修改字体
plt.rcParams['font.family'] = ['STSong']

def draw_wind_field_heat_map(savepath,data_type:WindFieldDataType,data:HeatMapData, config:HeatMapConfig=HeatMapConfig(), use_en:bool=True):
    ''' 绘制风场数据热力图
    
    参数：
    - savepath: 图片保存路径
    - data_type: 风场数据类型
    - data: 热力图数据
    - config: 绘图配置
    
    返回：
    - savepath: 图片保存路径
    '''
    fig, ax = plt.subplots(1,1,figsize=config.figsize)   
        
    match data_type:
        case WindFieldDataType.HWS:
            wind_data = data.horizontal_wind
            scale_speed = config.arrowLegendWS
        case WindFieldDataType.VWS:
            wind_data = data.vertical_wind
            scale_speed = config.arrowLegendWS/20
            
    wind_data.OriginWS.columns = data.col_index
    # region 热力图绘制
    cbar_limit = data_type.value.cbar_limit # 颜色条范围
    tick_locator = ticker.MaxNLocator(nbins=config.colorbarNticker) if isinstance(cbar_limit, tuple) else None
    if cbar_limit is None: cbar_limit = (None, None)

    mask = wind_data.OriginWS <= 0 if data_type!=WindFieldDataType.VWS else None
    heatmap = sns.heatmap(
        wind_data.OriginWS, ax=ax, vmax=cbar_limit[1], vmin=cbar_limit[0],
        annot=False, cbar=False, xticklabels=True, yticklabels=True, 
        mask=mask, cmap=data_type.value.cmap
    )
    # endregion
    
    # region 画箭头
    quiver = ax.quiver(data.grid.x, data.grid.y, wind_data.U, wind_data.V, 
        width=config.arrowWidth, headwidth=config.arrowHeadWidth, pivot=config.arrowPivot, units=config.arrowUnits, scale_units=config.arrowScale_Units, scale=100)
    
    ax = plt.gca()
    rect = Rectangle(xy=(0,0), width=ax.dataLim.bounds[2], height=ax.dataLim.bounds[3],
        linewidth=2, edgecolor='black', facecolor='none')
    ax.add_patch(rect) # 加边框
    # endregion
    
    # region 添加热力图颜色条
    cbar = heatmap.figure.colorbar(heatmap.collections[0], fraction=config.cFraction, pad=config.cPad)
    cbar.ax.tick_params(labelsize=config.cbTickSize)
    cbar.outline.set_visible(False)
    cbar.ax.yaxis.set_tick_params(width=config.cbTickWid, length=config.cbTickLen, color='black')
    # endregion
    
    # region 其他设置
    # y轴标题字体大小
    heatmap.yaxis.label.set_size(config.picAxisLabelSize)
    # 热力图坐标轴刻度标签大小设置
    heatmap.set_xticklabels(heatmap.get_xticklabels(), fontsize=config.picTickSize)
    heatmap.set_yticklabels(heatmap.get_yticklabels(), fontsize=config.picTickSize)
    
    # 将横坐标刻度标签替换为时间
    ax.set_xticks(data.col_index)
    ax.set_xticklabels(wind_data.WS.columns.tolist(), rotation=config.rotXticks)
    # 设置坐标轴刻度数量
    ax.locator_params(axis='x', nbins=config.nXticks)
    ax.locator_params(axis='y', nbins=config.nYticks)
    # 设置纵坐标标题
    if use_en:
        heatmap.set_ylabel(WPR_DataType.HEIGHT.value.label)
    else:
        heatmap.set_ylabel(WPR_DataType.HEIGHT.value.name)
    # endregion
    
    #region 向图中添加文本
    # 时间范围文本
    ax.text(config.txtLocX, config.txtLocY,f"{get_time_str(data.start_time,config.time_str_type)} ~ {get_time_str(data.end_time,config.time_str_type)}",
        fontdict={"size": config.txtFontSize,"color": config.txtFontColor}, transform=heatmap.transAxes)
    # 颜色条标题文本
    ax.text(config.cbUnitLocX, config.cbUnitLocY, data_type.value.label if use_en else data_type.value.name,
        fontdict={"size": config.txtFontSize,"color": config.txtFontColor}, transform=ax.transAxes)
    # 风场类型文本
    ax.set_title( "WindField_H" if use_en else "水平风场",
        fontdict={"fontsize": config.picTitleSize, 'fontweight': 'heavy'},
        loc=config.picTitleLoc, pad=config.txtLocY-1)
    #endregion
    
    #region 风场图例
    uLegend, vLegend = config.uv_legend
    q = ax.quiver(50, 150, uLegend, vLegend,
        color=config.arrowLegendColor, width=config.arrowWidth, headwidth=config.arrowHeadWidth,
        pivot=config.arrowPivot, units=config.arrowUnits, scale_units=config.arrowScale_Units, scale=100)

    add_x1 = (data.grid.x.shape[1]*config.arrowLegendLoc_X-config.arrowLegendTxtLoc_X)/data.grid.x.shape[1]+data.add_x
    
    ax.quiverkey(q ,0.2+add_x1, 1.04, 10,' ', labelpos='E') # labelpos 图例标签的位置，可以是'N'（北）、'S'（南）、'E'（东）或'W'（西）。这里的'E'表示图例标签位于箭头的东侧。

    # Scale文本内容
    content = f"Scale: {str(scale_speed)} m/s" if use_en else f"风速：{str(config.arrowLegendWS)}米/秒"

    ax.text(add_x1, 0.95+config.arrowLegendLoc_Y-config.arrowLegendTxtLoc_Y,
        content, fontdict={"size": config.txtFontSize, "color": config.arrowLegendColor}, transform=heatmap.transAxes)
    # endregion
    
    if tick_locator:
        cbar.locator = tick_locator
        cbar.update_ticks()
        
    fig.tight_layout()
    fig.subplots_adjust(left=None, bottom=None, top=None, hspace=None)
    ax.set_position(config.position)
    fig.savefig(savepath,dpi=config.dpi)
    # 关闭 Figure 对象
    plt.close(fig)

    # 清除缓存
    fig.clf()
    return savepath #,[pos.x0, pos.y0, pos.width, pos.height]

def draw_pollutant_plot(savepath, sitename, site_data, left_max, right_max, SO2_max, config:HeatMapConfig=HeatMapConfig(), use_en:bool=True):
    ''' 绘制污染物浓度折线图
    
    '''
    fig, ax_AQ = plt.subplots(1,1,figsize=config.figsize,dpi=config.dpi)   
    fig.tight_layout()
    fig.subplots_adjust(left=None, bottom=None, top=None, hspace=None)
    
    ax2 = ax_AQ.twinx()
    ax3 = ax_AQ.twinx()
    ax3.spines['right'].set_position(('outward', 15))
    
    # 通过接口获取的空气质量数据是按时间倒序排列的，需重新排序
    site_data = site_data.sort_values(by=['timePoint'])
    # 获取时间列表
    lstTime_AQ = site_data['timePoint'].tolist()
    # 格式化时间列表
    xtickLabel = []
    for item in lstTime_AQ:
        datetime_ = pd.to_datetime(item)
        xtickLabel.append(get_time_str(datetime_, TimeStr.HM))
    x_plot = np.arange(0, len(xtickLabel))
    for item_pol in TargetPollutants:
        # 获取指定参数
        data_pol = site_data[item_pol.value.annotation.value.col_name].apply(lambda x:minus2rep(x, np.nan))

        match item_pol:
            case TargetPollutants.PM10 | TargetPollutants.O3:
                item_pol.value.plot(ax=ax_AQ, x = x_plot, y = data_pol, use_en=use_en)
            case TargetPollutants.PM25 | TargetPollutants.NO2:
                item_pol.value.plot(ax=ax2, x = x_plot, y = data_pol, use_en=use_en)
            case TargetPollutants.SO2:
                item_pol.value.plot(ax=ax3, x = x_plot, y = data_pol, use_en=use_en)

    ax_AQ.set_ylim(bottom=0,top= left_max+3)
    ax_AQ.tick_params(labelsize=config.picTickSize)
    ax_AQ.tick_params(axis='y', color=TargetPollutants.O3.value.color)
    for t in ax_AQ.get_yticklabels():
        t.set_color(TargetPollutants.O3.value.color)
    ax_AQ.set_ylabel(TargetPollutants.O3.value.annotation.value.unit if use_en else TargetPollutants.O3.value.annotation.value.unit_cn,
                    fontdict={'size': config.picAxisLabelSize, 'color': TargetPollutants.O3.value.color})
    """locator = ticker.MaxNLocator(nbins=2)
    ax_AQ.yaxis.set_major_locator(locator)"""

    ax2.set_ylim(bottom=0,top=right_max+10)
    ax2.tick_params(labelsize=config.picTickSize)
    ax2.tick_params(axis='y', color=TargetPollutants.PM25.value.color)
    for t in ax2.get_yticklabels():
        t.set_color(TargetPollutants.PM25.value.color)
    ax2.set_ylabel(None)

    ax3.set_ylim(bottom=0,top=SO2_max+3)
    ax3.tick_params(labelsize=config.picTickSize)
    ax3.tick_params(axis='y', color=TargetPollutants.SO2.value.color)
    for t in ax3.get_yticklabels():
        t.set_color(TargetPollutants.SO2.value.color)
    ax3.set_ylabel(TargetPollutants.SO2.value.annotation.value.unit if use_en else TargetPollutants.SO2.value.annotation.value.unit_cn,
                    fontdict={'size': config.picAxisLabelSize, 'color': TargetPollutants.SO2.value.color})

    # 设置横坐标刻度个数
    ax_AQ.locator_params(axis='x', nbins=len(xtickLabel))
    # 设置横坐标范围，确保折线的起始位置在y轴
    ax_AQ.set_xlim(0, len(xtickLabel)-1)
    # 将横坐标刻度标签替换为时间，并选装刻度标签
    ax_AQ.set_xticklabels(xtickLabel, rotation=config.rotXticks)
    # 设置折线图标题，即参数名称
    ax_AQ.set_title('污染物浓度' if not use_en else sitename,
        fontdict={"fontsize": config.picTitleSize, 'fontweight': 'heavy'}, loc=config.picTitleLoc, pad=config.txtLocY)
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
                    loc=(0.41, 0.98))
    # 去掉图例边框
    leg.get_frame().set_linewidth(0.0)
    leg.get_frame().set_facecolor('none')

    # 设置坐标轴刻度标签字体大小
    # plt.tick_params(labelsize=config.drawRadarAQ.picTickSize)

    # 重置折线图宽度，确保与上面热力图对齐
    # if position is not None and len(position)==4:
    ax_AQ.set_position(config.position)
    
    fig.savefig(savepath, dpi=300)
    # 关闭 Figure 对象
    plt.close(fig)

    # 清除缓存
    fig.clf()
    return savepath