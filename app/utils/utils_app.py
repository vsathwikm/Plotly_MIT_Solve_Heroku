
import dash_html_components as html
import pandas as pd
import yaml 
import xlrd
import os 
import base64
import io
import csv 

with open("config.yml") as config_file: 
     config = yaml.load(config_file, Loader=yaml.FullLoader)




# Method used to parse files that are uploaded through the upload button
def parse_contents(contents, filename, date):
    '''
    contents - contents of the file being uploaded
    filename - name of the file being uploaded
    date - time the file is uploaded

    This method will take in the excel file that is
    uploaded and will create csv files of each sheet
    in the directory 'uploaded_excel_to_csv' which is 
    in the root directory

    It also has to potential to print out sheets that
    are uploaded
    '''
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            return html.Div([
            'Please upload an excel sheets.'
        ])
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            
            decoded_data = io.BytesIO(decoded)
            solver_data = pd.read_excel(decoded_data, sheet_name="Solver Team Data")
            partner_data = pd.read_excel(decoded_data, sheet_name="Partner Data")
        
            solver_data.to_csv(config['solver_location'])
            partner_data.to_csv(config['partner_location'])


    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

        
    return None

