# for file reading
import base64
import datetime
import io

# for auth
import dash_auth

# will turn excel into csv
from split_xlsx import ExceltoCSV

# for app
import os
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import dash

# adding basic Auth 
VALID_USERNAME_PASSWORD_PAIRS = {
    'mit': 'solve'
}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

from flask import Flask 
  
app = Flask(__name__) 

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server # the Flask app
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

# total score df
df_total_score = pd.read_csv('total_Score.csv')
# list of solvers
Solvers = list(df_total_score.columns[1:])
# List of mentors
Mentors = list(df_total_score["Unnamed: 0"])
# bar graph of total score for a specific solver
total_fig = px.bar(df_total_score, x=Solvers[0], y="Unnamed: 0",
labels = {'Unnamed: 0':'MENTOR',Solvers[0]:'Total Score'})
total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
# Format the bar graph
total_fig.update_layout(
    autosize=False,
    width=900,
    height=1000,
    margin=dict(
        l=50,
        r=50,
        b=100,
        t=100,
        pad=4
    )
    #paper_bgcolor="LightSteelBlue",
)

# Getting first Solver Table from dropdown bar
solver_needs_df = pd.read_csv("excel_to_csv/solver_team_data.csv")
selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns')
selected_solver_row_info_list = list(solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns'))

# Getting first Mentor Table - will be blank initially
mentor_data_df = pd.read_csv("excel_to_csv/partner_data.csv")
selected_mentor_row_info = mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns')
selected_mentor_row_info_list = list(mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns'))


# Creates a dictionary of all the Solver info to put in the options of selected_solver_table
selected_solver_row_list = []
for col in selected_solver_row_info:
    ind_row_dict = {}
    ind_row_dict["label"] = col
    ind_row_dict["value"] = selected_solver_row_info[col]
    selected_solver_row_list.append(ind_row_dict)


# Creates a dictionary to put all Solvers as options of drop down menu
solver_list_dict = []
for solver in Solvers:
    ind_solver_dict = {}
    ind_solver_dict["label"]=solver
    ind_solver_dict["value"]=solver
    solver_list_dict.append(ind_solver_dict)

# Method that generates tables
# Used to for the selected_solver_table and clicked_on_mentor_table
def generate_table(dataframe, max_rows=10):
    return html.Table([
        html.Thead(
            html.Tr([html.Th(col) for col in dataframe.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(dataframe.iloc[i][col]) for col in dataframe.columns
            ]) for i in range(min(len(dataframe), max_rows))
        ])
    ])


# Method used to parse files from upload button
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
            'Please upload on excel sheets.'
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
    # Returns an html table of the df to be printed currently
    # return html.Div([
    #     html.H5(filename),
    #     dash_table.DataTable(
    #         data=df.to_dict('records'),
    #         columns=[{'name': i, 'id': i} for i in df.columns]
    #     ),
    # ])
    return None

# APP LAYOUT
app.layout = html.Div(children=[
    html.H1(
        children='MIT SOLVE',
        style={
            'textAlign': 'center'
            
        }
    ),

    # Upload files
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload Files'),
        style={
            # 'width': '50%',
            'height': '60px',
            # 'lineHeight': '60px',
            # 'borderWidth': '1px',
            # 'borderStyle': 'dashed',
            # 'borderRadius': '5px',
            'textAlign': 'center',
            # 'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),


    # Drop down menu
    html.Label('Select a Solver'),
        dcc.Dropdown(
            id='Solver_dropdown',
            options= solver_list_dict,
            value = solver_list_dict[0]['value'], 
           ),

    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.H2(children='Total Outputs Graph', style={'textAlign': 'center'}),

    # Display graph for total score
    dcc.Graph( 
        id='output_bargraph',
        figure= total_fig
    ),

    # Generates the table for the selected solver from the dropdown
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


    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # Generates table for the clicked on mentor
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

    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # printing df from uploaded file
    html.Div(id='output-data-upload'),

])

# This method will update the table displaying more information
# on any mentor that is clicked on in the graph
@app.callback(
    dash.dependencies.Output('clicked_on_mentor_table', 'data'),
    [dash.dependencies.Input('output_bargraph', 'clickData')])
def display_click_data(clickData):
    if clickData != None:
        mentor_name = clickData['points'][0]['label']
        mentor_data_df = pd.read_csv("excel_to_csv/partner_data.csv")
        selected_mentor_row_info = mentor_data_df[mentor_data_df['Org']==mentor_name].dropna(axis='columns')
        generate_table(selected_mentor_row_info)  
        return selected_mentor_row_info.to_dict('records')


# This method updates the table displaying more information on a solver
# everytime a new solver is selected from the dropdown
@app.callback(
    dash.dependencies.Output('selected_solver_table', 'data'),
    [dash.dependencies.Input('Solver_dropdown', 'value')])
def update_solver_table(value):
    solver_needs_df = pd.read_csv("excel_to_csv/solver_team_data.csv")
    selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==value].dropna(axis='columns')
    generate_table(selected_solver_row_info)  
    return selected_solver_row_info.to_dict('records')


# This method updates the graph when a new solver is selected from the dropdown
@app.callback(
    dash.dependencies.Output('output_bargraph', 'figure'),
    [dash.dependencies.Input('Solver_dropdown', 'value')])
def update_graph(value):
    total_fig = px.bar(df_total_score, x=value, y="Unnamed: 0",
    labels = {'Unnamed: 0':'MENTOR',value:'Total Score'})
    total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return total_fig


# This method will create csv files for each sheet
# from the uploaded file. The file must be in the format of
# a singular excel file consisting of 2 sheets, which are the 
# partner_data and solver_team_data
@app.callback(
    dash.dependencies.Output('output-data-upload', 'children'),
    [dash.dependencies.Input('upload-data', 'contents')],
    [dash.dependencies.State('upload-data', 'filename'),
    dash.dependencies.State('upload-data', 'last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            # parse_contents prints out the files as tables
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        # list_of_uploaded_files is fully available here
        #print(list_of_uploaded_files)
        return children
    



if __name__ == '__main__':
    app.run_server(debug=True)