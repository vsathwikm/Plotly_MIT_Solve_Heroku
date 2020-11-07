
# for file reading
import base64
import datetime
import io

# for creating the new total_score.xlsx
from create_total_score import create_total_score_excel

# for auth
import dash_auth
from flask import Flask 

# for downloading excel file
from flask import send_file
import zipfile

# for turning excel into csv
import csv
import xlrd
import sys



# for app
import os
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import dash
import plotly.graph_objects as go
from dash.dependencies import Output, Input
# writing to excel files
import openpyxl





def ExceltoCSV(excel_file, csv_file_base_path, csv_folder = "../uploaded_excel_to_csv/"):
    '''
    inputs:
    Excel file, str - name of the original file
    csv_file_base_path, str - folder location where each file will be stored
    excel_folder, str - a folder with this name will be created in csv_base_file_path with sheet names
                        with excel file. If excel file has sheets then each sheet will be stored as
                        a seperte csv file

    '''    
    if not os.path.isdir(csv_file_base_path+csv_folder): 
        os.mkdir(csv_file_base_path+csv_folder)
    full_path = csv_file_base_path+csv_folder
    workbook = xlrd.open_workbook(excel_file)

    for sheet_name in workbook.sheet_names():
        print('processing - ' + sheet_name)
        worksheet = workbook.sheet_by_name(sheet_name)
        csv_file_full_path = full_path + sheet_name.lower().replace(" - ", "_").replace(" ","_") + '.csv'
        csvfile = open(csv_file_full_path, 'w',encoding='utf-8')
        writetocsv = csv.writer(csvfile, quoting = csv.QUOTE_ALL, )
        for rownum in range(worksheet.nrows):
            writetocsv.writerow(
    #                 list(x.encode('utf-8') if type(x) == type(u'') else x for x in worksheet.row_values(rownum)
                    worksheet.row_values(rownum)
                )
            
        csvfile.close()
     #( "{} has been saved at {}".format(sheet_name, csv_file_full_path))

if __name__ == "__main__":
    filename = "../mock_input_data.xlsx" 

    ExceltoCSV(excel_file=filename , csv_file_base_path ="" )
    solver_needs_df = pd.read_csv('outputs/solver_team_data.csv')
    solvers = solver_needs_df['Org'].values.tolist()