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
import dash_table_experiments as dte
from flask import send_file
import zipfile

# for turning excel into csv
import csv
import xlrd
import sys

# for writing to confirmed matches excel sheet
from xlwt import Workbook
from xlutils.copy import copy # not sure if needed

# for app
import os
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import dash

# writing to excel files
import openpyxl


# for adding basic Auth 
VALID_USERNAME_PASSWORD_PAIRS = {
    'mit': 'solve2020'
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

# the Flask app
app = Flask(__name__) 
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server 
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# Determines how many matches have been created so writing to the excel
# file with new matches is a smooth process
df = pd.read_excel('mit_solve_confirmed_matches.xlsx') 
mentors_list = df['MENTOR'].tolist()
# GLOBAL VARIABLE USED TO COUNT NUMBER OF MATCHES
COUNT_OF_MATCHES = len(mentors_list)

# Getter for COUNT_OF_MATCHES
def get_count_of_matches():
    global COUNT_OF_MATCHES
    return COUNT_OF_MATCHES

# Increments COUNT_OF_MATCHES
def increment_count_of_matches():
    global COUNT_OF_MATCHES
    COUNT_OF_MATCHES += 1

# Initially the excel sheet 'total_score.xlsx' is used for the dashboard
# until new data is uploaded to the dashboard. The 'total_score.xlsx' sheet
# is hard coded and stored in the root directory
hardcoded_file_total_score = pd.ExcelFile('total_score.xlsx')
df_total_score = hardcoded_file_total_score.parse('Sheet1')

# list of solvers from hard coded 'total_score.xlsx'
Solvers = list(df_total_score.columns[1:])
# List of mentors from hard coded 'total_score.xlsx'
Mentors = list(df_total_score["Org_y"])

# Creates the initial horizonatl bar graph that is displayed on the dashboard
total_fig = px.bar(df_total_score.sort_values(Solvers[0], ascending=False)[:5], x=Solvers[0], 
y="Org_y", labels = {'Org_y':'MENTOR',Solvers[0]:'Total Score'})
total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
# Format the bar graph
total_fig.update_layout(
    autosize=True,
    # width=700,
    height=500,
    margin=dict(
        l=50,
        r=50,
        b=100,
        t=100,
        pad=4
    )
)

# Getting initial, hardcoded Solver Table from dropdown bar
solver_needs_df = pd.read_csv("unused_files/excel_to_csv/solver_team_data.csv")
selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns')
selected_solver_row_info_list = list(solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns'))

# Creates a dictionary of all the Solver info to put in the selected_solver_table
selected_solver_row_list = []
for col in selected_solver_row_info:
    ind_row_dict = {}
    ind_row_dict["label"] = col
    ind_row_dict["value"] = selected_solver_row_info[col]
    selected_solver_row_list.append(ind_row_dict)

# DO WE EVEN NEED THIS CODE
# Getting initial, hardcoded Mentor Table - will be blank initially
mentor_data_df = pd.read_csv("unused_files/excel_to_csv/partner_data.csv")
selected_mentor_row_info = mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns')
selected_mentor_row_info_list = list(mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns'))


# Creates a dictionary to put all Solvers as options of drop down menu
solver_list_dict = []
for solver in Solvers:
    ind_solver_dict = {}
    ind_solver_dict["label"]=solver
    ind_solver_dict["value"]=solver
    solver_list_dict.append(ind_solver_dict)

# Method that generates tables
# Used for the selected_solver_table and clicked_on_mentor_table
def generate_table(dataframe, max_rows=200):    
    """
    inputs:
    dataframe, padas df - dataframe to output to a table
    max_rows, int - max amount of rows to print. Set at 100 to 
    be high enough to deal with any dataframe used in this dashboard
    """
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
        
    ], 
)


# Allows the input excel fileS to be turned into csv files which will be used
# to calculate the information required for pairing in create_total_score.py
def ExceltoCSV(excel_file, csv_file_base_path, csv_folder = "uploaded_excel_to_csv/"):
    """
    inputs:
    Excel file, str - name of the original file
    csv_file_base_path, str - folder location where each file will be stored
    excel_folder, str - a folder with this name will be created in csv_base_file_path with sheet names
                        with excel file. If excel file has sheets then each sheet will be stored as
                        a seperte csv file

    """    
    if not os.path.isdir(csv_file_base_path+csv_folder): 
        os.mkdir(csv_file_base_path+csv_folder)
    full_path = csv_file_base_path+csv_folder
    workbook = xlrd.open_workbook(excel_file)

    for sheet_name in workbook.sheet_names():
     #   print('processing - ' + sheet_name)
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
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    ExceltoCSV(excel_file=filename , csv_file_base_path ="" )
    return None


# APP LAYOUT
app.layout = html.Div(children=[
    html.H1(
        children='MIT SOLVE',
        style={
            'textAlign': 'center'
            
        }
    ),

    # Upload files button
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload Excel Data File'),
        style={
            'height': '60px',
            'textAlign': 'center',
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),

    # Download all excel files button
    html.Div(children=[
        html.A(html.Button('Download All Excel Files'), href="/download_all/",
        ),
    ],
    style={
        'height': '60px',
        'textAlign': 'center',
    }),

    # Solver drop down menu 
    html.Label('Select a Solver'),
        dcc.Dropdown(
            id='Solver_dropdown',
            options= solver_list_dict,
            value = solver_list_dict[0]['value'], 
           ),

    # A few line breaks to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # Title for the horizontal bar graph
    html.H2(children='Total Outputs Graph', style={'textAlign': 'center'}),

    # Horizontal graph
    dcc.Graph( 
        id='output_bargraph',
        figure= total_fig
    ),

    # Generates the table for the selected solver
    # selected_solver_row_info is that data of the seleced solver
    # that will go into the table
    html.H4(children='Selected Solver Information',style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='selected_solver_table',
        columns=[{"name": i, "id": i} for i in selected_solver_row_info.columns],
        data=selected_solver_row_info.to_dict('records'),
        style_cell={
            'whiteSpace': 'normal',
            'height': 'auto',
            'textAlign': 'center',
            'font_family': 'helvetica',
            'font_size': '20px',
        },
        style_header={
        'backgroundColor': 'rgb(30, 30, 30)',
        'color': 'white',
        },
    ),

    # A few line breaks to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
   
    # Generate a checkbox that determines whether the current partner and solver 
    html.H3(children='Click Checkbox to Confirm Match between Selected Solver and Selected Mentor',
        style={'textAlign': 'center'}
    ),
    dcc.RadioItems(
        id='checkbox_confirm',
        options=[  
            {'label': 'Yes Match?', 'value': 'Confirm'},
            {'label': 'No Match?', 'value': 'Denied'}
        ],
        style={
            'textAlign': 'center',
        },
        value='Denied', # set intitial value to 'denied' which means no match
        inputStyle={"margin-right": "20px"},
        labelStyle={'display': 'inline-block'}
    ),  

    # A line break to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # Generates table for the mentor that is clicked on in the graph
    # selected_mentor_row_info is that data of the seleced mentor
    # that will go into the table - initially this table won't be populated
    html.H4(children='Clicked on Mentor Information',style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='clicked_on_mentor_table',
        columns=[{"name": i, "id": i} for i in selected_mentor_row_info.columns],
        data=selected_mentor_row_info.to_dict('records'),
        style_cell={
            'whiteSpace': 'normal',
            'height': 'auto',
            'textAlign': 'center',
            'font_family': 'helvetica',
            'font_size': '20px',
        },
        style_header={
        'backgroundColor': 'rgb(30, 30, 30)',
        'color': 'white',
        },
    ),
    html.H4(children='Green = 0-1 matches, Blue = 2-3 matches, Red = 4 or more matches',style={'textAlign': 'center'}),

    # A few line breaks to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # Used to print out the newly calculated total score dataframe from
    # the uploaded files. Should only be used for debugging and is not set 
    # to be functional right now
    html.Div(id='output-data-upload'),

    # Print the solver matches for the selected mentor below the mentor table
    html.Div(id='mentor-matches-list',
    children=[]),

    # Break line to space out the dashboard
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # hidden app layout which is target of callbacks that don't update anything but
    # plotly dash requires outputs for all callbacks
    html.Div(id='hidden-div', 
    ),

    # Comment box
    dcc.Textarea(
        id='textarea-for-comments',
        value='Text area for comments', # initial value
        style={'width': '50%', 'height': 200, 'Align-items': 'center'},
    ),
])


# This callback prints the current list of solver matches for the current selected mentor
# If there are no matches it default prints
@app.callback(
    dash.dependencies.Output('mentor-matches-list', 'children'),
    [dash.dependencies.Input('checkbox_confirm', 'value')],
    [dash.dependencies.State('output_bargraph', 'clickData'),
    dash.dependencies.State('Solver_dropdown', 'value')],
)
def list_matches_for_a_mentor(value, clickData, solver_name):
    df = pd.read_excel('mit_solve_confirmed_matches.xlsx')
    mentors_list = df['MENTOR'].tolist()
    solvers_list = df['SOLVER'].tolist()

    # If no mentor is selected
    if clickData == None:
        # defualt response
        return 'You need to select a mentor'

    matches_list = []

    # populate a list with all the solvers currently matched with the mentor
    for i in range(len(solvers_list)):
        if mentors_list[i] == str(clickData['points'][0]['label']):
            matches_list.append(solvers_list[i])

    # If match is just created add the selected solver (solver_name) to the list
    if value == 'Confirm':
        if solver_name not in matches_list:
            matches_list.append(solver_name)

    # If match is just deleted remove the selected solver (solver_name) from the list
    if value == 'Denied':
        if solver_name in matches_list:
            matches_list.remove(solver_name)

    if matches_list == []:
        return 'no current matches for this mentor'
    else:
        return "List of current matches for " + str(clickData['points'][0]['label']) + ": \n" + str(matches_list)


# This method allows for you to download all of the generated excel files as a zip file
# Files are challenge_match.xlsx, geo_match.xlsx, needs_match.xlsx, stage_match.xlsx,
# total_score_from_upload.xlsx and mit_solve_confirmed_matches.xlsx
@app.server.route('/download_all/')
def download_all():
    zipf = zipfile.ZipFile('app/MIT_Solve_Excel_Files.zip','w', zipfile.ZIP_DEFLATED)
    for root,dirs, files in os.walk('MIT_SOLVE_downloadable_excel_files/'):
        for file in files:
            zipf.write('MIT_SOLVE_downloadable_excel_files/'+file)
    zipf.write('mit_solve_confirmed_matches.xlsx')
    zipf.close()
    return send_file('MIT_Solve_Excel_Files.zip',
            mimetype = 'zip',
            attachment_filename= 'MIT_Solve_Excel_Files.zip',
            as_attachment = True)


# This method will update the table displaying more information
# on the mentor that is clicked on in the graph
@app.callback(
    [dash.dependencies.Output('clicked_on_mentor_table', 'data'),
    dash.dependencies.Output('clicked_on_mentor_table', 'style_cell')],
    [dash.dependencies.Input('output_bargraph', 'clickData'),
    dash.dependencies.Input('checkbox_confirm', 'value'),
    ])
def display_click_data(clickData, value):
    # Check to make sure a mentore is selected
    if clickData != None:
        mentor_name = clickData['points'][0]['label']
        mentor_data_df = pd.read_csv("uploaded_excel_to_csv/partner_data.csv")
        selected_mentor_row_info = mentor_data_df[mentor_data_df['Org']==mentor_name].dropna(axis='columns')
        generate_table(selected_mentor_row_info)
        df = pd.read_excel('mit_solve_confirmed_matches.xlsx') 
        mentors_list = df['MENTOR'].tolist()

        
        # This loop counts how many matches there are for the specific mentor
        mentor_matches_count = 0
        for i in range(len(mentors_list)):
            if mentors_list[i] == mentor_name:
                mentor_matches_count += 1

        # Pick color for color_code based on number of matches
        # STILL A LITTLE BUGGY, DOESN'T UPDATE LIVE
        if mentor_matches_count <= 1:
            color_code = 'green'
        elif mentor_matches_count == 2 or mentor_matches_count == 3:
            color_code = 'blue'
        else:
            color_code = 'red'

        new_style = {
            'whiteSpace': 'normal',
            'height': 'auto',
            'textAlign': 'center',
            'font_family': 'helvetica',
            'font_size': '20px',
            'color' : color_code
        }

        return [selected_mentor_row_info.to_dict('records'), new_style]
    return [None, {
        'whiteSpace': 'normal',
        'height': 'auto',
        'textAlign': 'center',
        'font_family': 'helvetica',
        'font_size': '20px',
        }]


# Callback that either checks off or leaves blank the checkbox when a new solver or
# partneris selected
@app.callback(
    dash.dependencies.Output('checkbox_confirm', 'value'),
    [dash.dependencies.Input('Solver_dropdown', 'value'),
    dash.dependencies.Input('output_bargraph', 'clickData')]
)
def check_or_uncheck_checkbox(solver_name, clickData):
    df = pd.read_excel('mit_solve_confirmed_matches.xlsx')
    mentors_list = df['MENTOR'].tolist()
    solvers_list = df['SOLVER'].tolist()

    # check to make sure there is a mentor selected
    if clickData == None:
            return 'You need to select a mentor'

    # iterate through list of solvers to find currently selected solver (solver_name)
    for i in range(len(solvers_list)):
        if solvers_list[i] == solver_name:
            # if the solver name is found check if its mentor is the currently selected mentor
            if mentors_list[i] == clickData['points'][0]['label']:
                # This is  a match 
                return 'Confirm'

    # If we get here this is not a match
    return 'Denied'


# Callback that adds and deletes matches to the 'mit_solve_confirmed_matches.xlsx'
@app.callback(
    dash.dependencies.Output('hidden-div', 'children'),
    [dash.dependencies.Input('checkbox_confirm', 'value')],
    [dash.dependencies.State('Solver_dropdown', 'value'),
    dash.dependencies.State('output_bargraph', 'clickData')]
    )
def add_confirmed_match(checkbox, solver_name, clickData):
    # Check if we are adding a match
    if checkbox == 'Confirm':
        if clickData == None:
            return 'You need to select a mentor'
        else:
            df = pd.read_excel('mit_solve_confirmed_matches.xlsx') 
            mentors_list = df['MENTOR'].tolist()
            solvers_list = df['SOLVER'].tolist()

            # checks if already a match
            for i in range(len(solvers_list)):
                if solvers_list[i] == solver_name:
                    if mentors_list[i] == clickData['points'][0]['label']:
                        # This is already a match 
                        return None

            file = 'mit_solve_confirmed_matches.xlsx'
            wb = openpyxl.load_workbook(filename=file)
            ws = wb.get_sheet_by_name('Sheet1')

            # count number of matches 
            # start the count at 1 to account for this match not being added to the sheet yet
            matches_count_for_mentor = 1
            for i in range(len(mentors_list)):
                if mentors_list[i] == clickData['points'][0]['label']:
                    matches_count_for_mentor += 1
                    
            # insert the mentor and solver names, as well as datetime and number of matches
            time_right_now = datetime.datetime.now()
            ws['A' + str(COUNT_OF_MATCHES + 2)] = str(clickData['points'][0]['label'])
            ws['B' + str(COUNT_OF_MATCHES + 2)] = str(solver_name)
            ws['C' + str(COUNT_OF_MATCHES + 2)] = str(time_right_now)
            ws['D' + str(COUNT_OF_MATCHES + 2)] = str(matches_count_for_mentor)
            # Save the workbook
            wb.save(file)
            #increment amount of total matches
            increment_count_of_matches()
            return ''

    # Check if we are removing a match
    if checkbox == 'Denied':
        if clickData == None:
            return 'No mentor selected'
        else:
            df = pd.read_excel('mit_solve_confirmed_matches.xlsx') 
            mentors_list = df['MENTOR'].tolist()
            solvers_list = df['SOLVER'].tolist()

            # checks if already a match
            for i in range(len(solvers_list)):
                if solvers_list[i] == solver_name:
                    if mentors_list[i] == clickData['points'][0]['label']:
                        # This match needs to be deleted

                        file = 'mit_solve_confirmed_matches.xlsx'
                        wb = openpyxl.load_workbook(filename=file)
                        # Select the right sheet
                        ws = wb.get_sheet_by_name('Sheet1')
                        # insert the mentor and solver name, datetime, and number of matches
                        ws['A' + str(i + 2)] = str('')
                        ws['B' + str(i + 2)] = str('')
                        ws['C' + str(i + 2)] = str('')
                        ws['D' + str(i + 2)] = str('')
                        # Save the workbook
                        wb.save(file)
                        # NEED TO DECREMENT NUMBER OF MATCHES HERE
                        # LOGIC MAY NEED WORK TOO, NOT SURE IF JUST DECREMENTING IS THE RIGHT MOVE


# This method updates the table displaying more information on a solver
# everytime a new solver is selected from the dropdown
@app.callback(
    dash.dependencies.Output('selected_solver_table', 'data'),
    [dash.dependencies.Input('Solver_dropdown', 'value')])
def update_solver_table(value):
    # Checks if new files have been uploaded yet instead of hard coded
    try:
        solver_needs_df = pd.read_csv("uploaded_excel_to_csv/solver_team_data.csv")
        selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==value].dropna(axis='columns')
        generate_table(selected_solver_row_info)  
        return selected_solver_row_info.to_dict('records')
    # Uses the hard coded Solver info if no files have been uploaded yet
    except:
        solver_needs_df = pd.read_csv("unused_files/excel_to_csv/solver_team_data.csv")
        selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==value].dropna(axis='columns')
        generate_table(selected_solver_row_info)  
        return selected_solver_row_info.to_dict('records')


# This method updates the graph when a new solver is selected from the dropdown
@app.callback(
    dash.dependencies.Output('output_bargraph', 'figure'),
    [dash.dependencies.Input('Solver_dropdown', 'value')])
def update_graph_from_solver_dropdown(value):
    # Checks if new files have been uploaded yet instead of hard coded
    try:
        xls_file_total_score = pd.ExcelFile('MIT_SOLVE_downloadable_excel_files/total_score_from_upload.xlsx')
        uploaded_df_total_score = xls_file_total_score.parse('Sheet1')
    # Uses the hard coded files if no files have been uploaded yet
    except:
        uploaded_df_total_score = df_total_score
    # Sort and crop top 5 values for new selected solver
    total_fig = px.bar(uploaded_df_total_score.sort_values(value, ascending=False)[:5], x=value, 
    y="Org_y", labels = {'Org_y':'MENTOR',value:'Total Score'})
    total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return total_fig

# This method will create csv files for each sheet
# from the uploaded file. The uploaded file must be in the format of
# a singular excel file consisting of 2 sheets, which are the 
# partner_data and solver_team_data in that order
@app.callback(
    dash.dependencies.Output('output-data-upload', 'children'),
    [dash.dependencies.Input('upload-data', 'contents')],
    [dash.dependencies.State('upload-data', 'filename'),
    dash.dependencies.State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        # list_of_uploaded_files is fully available here
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        new_total_score = create_total_score_excel()
        new_total_score.insert(0, "Partners", Mentors, True)
        return None


# This callback will create a new bar chart with the data from the uploaded excel
# files instead of the preloaded old excel files
@app.callback(
    dash.dependencies.Output('Solver_dropdown', 'value'),
    [dash.dependencies.Input('upload-data', 'contents')],
)
def point_graph_to_uploaded_files(contents):
    try:
        # create new df from uploaded file
        xls_file_total_score = pd.ExcelFile('MIT_SOLVE_downloadable_excel_files/total_score_from_upload.xlsx')
        uploaded_df_total_score = xls_file_total_score.parse('Sheet1')
        # Create new graph with uploaded data instead of hardcoded
        new_solvers = list(uploaded_df_total_score.columns[1:])
        # Returns a different solver its obvious whether this worked or not
        return new_solvers[8]
    except:
        return Solvers[0]

if __name__ == '__main__':
    app.run_server(debug=True)