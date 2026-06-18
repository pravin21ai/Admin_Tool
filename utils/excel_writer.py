import xlsxwriter
from io import BytesIO

def create_error_report(df, filename="error_report.xlsx"):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Errors")

    # Formats
    header_format = workbook.add_format({
        'bold': True, 'bg_color': '#D3D3D3', 'border': 1
    })
    error_format = workbook.add_format({
        'bg_color': '#FFC7CE', 'font_color': '#9C0006'
    })

    # Write headers
    columns = list(df.columns)
    for col_num, col_name in enumerate(columns):
        worksheet.write(0, col_num, col_name, header_format)

    # Write rows
    for row_num, row_data in enumerate(df.values):
        for col_num, cell_data in enumerate(row_data):
            # Highlight the row in red
            worksheet.write(row_num + 1, col_num, str(cell_data), error_format)

    workbook.close()
    return output.getvalue()

def create_credentials_report(df):
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Credentials")

    header_format = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    broker_format = workbook.add_format({'bg_color': '#B4C6E7'}) # Blue
    group_format = workbook.add_format({'bg_color': '#C6E0B4'}) # Green
    trader_format = workbook.add_format({'bg_color': '#FFFFFF'}) # White

    columns = list(df.columns)
    for col_num, col_name in enumerate(columns):
        worksheet.write(0, col_num, col_name, header_format)

    for row_num, row_data in enumerate(df.values):
        role = str(row_data[1]).lower() # Assuming role is in column 1
        fmt = trader_format
        if role == 'broker':
            fmt = broker_format
        elif role == 'group':
            fmt = group_format

        for col_num, cell_data in enumerate(row_data):
            worksheet.write(row_num + 1, col_num, str(cell_data), fmt)

    workbook.close()
    return output.getvalue()
