import pandas as pd
from typing import Dict
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Border, Side

def save_dataframes2xlsx(savepath:str, dataframes:Dict[str, pd.DataFrame]):
    assert savepath.endswith('.xlsx')
    #region 保存 Excel 文件
    xlsx_writer = pd.ExcelWriter(savepath, engine='openpyxl')
    for sheet_name, df in dataframes.items():
        df.to_excel(excel_writer=xlsx_writer,index=False,sheet_name=sheet_name)
        
    # 获取 ExcelWriter 对象的 workbook
    workbook = xlsx_writer.book

    # 遍历每个 sheet
    for sheet_name in xlsx_writer.sheets:
        sheet = workbook[sheet_name]
        
        # 遍历每列，设置列宽为自适应并将内容居中
        for column_cells in sheet.columns:
            max_length = 0
            column = column_cells[0].column_letter
            for cell in column_cells:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 5) * 1.5
            sheet.column_dimensions[column].width = adjusted_width
            
            for cell in column_cells:
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = Border(left=Side(border_style='thin'),
                                    right=Side(border_style='thin'),
                                    top=Side(border_style='thin'),
                                    bottom=Side(border_style='thin'))
    xlsx_writer.close()
    #endregion
    