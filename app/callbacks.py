import base64
import datetime
import io



# for creating the new total_score.xlsx
from utils.create_total_score import create_total_score_excel
from utils import utils_app

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

import shutil

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
import yaml 
from dash.exceptions import PreventUpdate
import time
import os 


with open("config.yml") as config_file: 
     config = yaml.load(config_file, Loader=yaml.FullLoader)

from app import app 




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
    '''
    param: contents - all of the files uploaded
    param: filename - name of the uploaded file
    param: last_modified - the date in which the file was last modified
    return: irrelavent output, will never be printed out and is used to 
    comply with needing an Output for every callback
    '''
    if os.path.exists(config['outputs']): 
        shutil.rmtree(config['outputs'])
        os.makedirs(config['outputs'])
    else: 
        os.makedirs(config['outputs'])

    if list_of_contents is not None:
       
        # list_of_uploaded_files is fully available here
        children = [
            utils_app.parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
       
        new_total_score = create_total_score_excel(config['outputs'])
        # new_total_score.insert(0, "Partners", Partners, True)
        return None

# This method allows for you to download all of the generated excel files as a zip file
# Files are challenge_match.xlsx, geo_match.xlsx, needs_match.xlsx, stage_match.xlsx,
# total_score_from_upload.xlsx and mit_solve_confirmed_matches.xlsx
# TODO make sure the correct files are being uploaded - think wrong ones are right now
@app.server.route('/download_all/')
def download_all():
    
    zipf = zipfile.ZipFile(config['zipf_name'],'w', zipfile.ZIP_DEFLATED)
   
    for root,dirs, files in os.walk(config['outputs']):
        for file in files:
            zipf.write(config['outputs']+file)
    zipf.close()
    return send_file(config['zipf_name'],
            mimetype = 'zip',
            attachment_filename= config['zipf_name'],
            as_attachment = True)


# @app.callback(
#     [dash.dependencies.Output('solver-dropdown', 'value'), 
#     dash.dependencies.Output('solver-dropdown', 'options')], 
#     [dash.dependencies.Input('update-solvers-button', 'n_clicks')]
#     )
# def dropdown_options(clicks):
#     solver_needs_df = pd.read_csv(config['solver_location'])
#     solvers = solver_needs_df['Org'].values.tolist()
#     options = []
#     for x in solvers: 
#         single_dict = {'label': x, 'value': x }
#         options.append(single_dict)

    
#     dropvalue = "Select.."
#     return [dropvalue, options]


@app.callback(
    [dash.dependencies.Output('solver-dropdown', 'value'), 
    dash.dependencies.Output('solver-dropdown', 'options')], 
    [dash.dependencies.Input('upload-data', 'contents')],
    [dash.dependencies.State('upload-data', 'filename'),
    dash.dependencies.State('upload-data', 'last_modified')]
    )
def dropdown_options(list_of_contents, list_of_names, list_of_dates):
    time.sleep(0.1)
    solver_needs_df = pd.read_csv(config['solver_location'])
    solvers = solver_needs_df['Org'].values.tolist()
    options = []
    for x in solvers: 
        single_dict = {'label': x, 'value': x }
        options.append(single_dict)

    
    dropvalue = "Select.."
    return [dropvalue, options]


# This method updates the graph when a new solver is selected from the dropdown
@app.callback(
    dash.dependencies.Output('output_bargraph', 'figure'),
    [dash.dependencies.Input('solver-dropdown', 'value')])
def update_graph_from_solver_dropdown(value):
    '''
    param: solver_name (str) - name of the selected solver from the dropdown menu
    return: figure (Plotly Express Bar Chart) - the graph for total scores displayed on the dashboard
    '''
    
    # Checks if new files have been uploaded yet instead of hard coded
    xls_file_total_score = pd.ExcelFile(config['total_score_location'])
    uploaded_df_total_score = xls_file_total_score.parse('Sheet1')

    # Sort and crop top 5 values for new selected solver
    total_fig = px.bar(uploaded_df_total_score.sort_values(value, ascending=False)[:5], x=value, 
    y="Org_y", labels = {'Org_y':'PARTNER',value:'Total Score'})
    total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return total_fig


# This method will update the table displaying more information
# on the partner that is clicked on in the graph and also create the 
# additional individual graph
@app.callback(
    [dash.dependencies.Output('individual_graph', 'figure'),
    dash.dependencies.Output('individual_graph_title', 'children')],
    [dash.dependencies.Input('output_bargraph', 'clickData'),],
    [dash.dependencies.Input('solver-dropdown', 'value')]
    )
def update_individual_graph(clickData, solver_name):
    '''
    param: clickData (Plotly Dash Object) - data that is collected from clicking on graph
    param: solver_name (str) - name of the selected solver from the dropdown menu
    return: figure (Plotly Express Bar Chart) - individual graph of category values
    return: children (str) - customized title for individual graph
    '''
    # Check to make sure a partnere is selected
    if clickData != None:
        # Must get value for partner compared to solver in: geo, needs, stage, challenge
    
        partner_name = clickData['points'][0]['y']

        geo_df = pd.read_excel(config['geo_match'])
        geo_value = float(geo_df[geo_df["Org_y"]==partner_name].iloc[0][solver_name])
        

        needs_df = pd.read_excel(config['needs_match'])
        needs_value = float(needs_df[needs_df["Org_y"]==partner_name].iloc[0][solver_name])

        stage_df = pd.read_excel(config['stage_match'])
        stage_value = float(stage_df[stage_df["Org_y"]==partner_name].iloc[0][solver_name])

        challenge_df = pd.read_excel(config['challenge_match'])
        challenge_value = float(challenge_df[challenge_df["Org_y"]==partner_name].iloc[0][solver_name])

        partner_values_dict = {'Labels': ['Challenges Score', 'Needs Score', 'Geo Score * Stage Score',
        'Geo Score', 'Stage Score'], 'Scores': [10*challenge_value, needs_value, 100*geo_value*stage_value,
        10*geo_value, 10*stage_value]}

        ind_fig = px.bar(partner_values_dict, x='Scores', y='Labels')
        return_string = "Individual Graph for '" + str(partner_name) + "'"
        
        return [ind_fig, return_string]
    
    figure={'data': []}
    return [figure, '']


# This method updates the table displaying more information on a solver
# everytime a new solver is selected from the dropdown
@app.callback(
    [dash.dependencies.Output('selected_solver_table', 'columns'), 
    dash.dependencies.Output('selected_solver_table', 'data')],
    [dash.dependencies.Input('solver-dropdown', 'value')])
def update_solver_table(value):
    '''
    param: solver_name (str) - name of the selected solver from the dropdown menu
    return: data (dict) - a dictionary containing data that will populate the solver table
    '''
    # Checks if new files have been uploaded yet instead of hard coded
    
    solver_needs_df = pd.read_csv(config['solver_location'])
    selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==value].dropna(axis='columns')

    columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in selected_solver_row_info.columns
        ]
    data = selected_solver_row_info.to_dict('records')
    return [columns, data]


# This method updates the table displaying more information on a partner
# everytime a new solver is selected from the dropdown
@app.callback(
    [dash.dependencies.Output('clicked_on_partner_table', 'columns'), 
    dash.dependencies.Output('clicked_on_partner_table', 'data')],
    [dash.dependencies.Input('output_bargraph', 'clickData')])
def update_partner_table(clickData):
    '''
    param: solver_name (str) - name of the selected solver from the dropdown menu
    return: data (dict) - a dictionary containing data that will populate the solver table
    '''
    # Checks if new files have been uploaded yet instead of hard coded
    partner_name = clickData['points'][0]['y']
    partners_df = pd.read_csv(config['partner_location'])
    selected_partner_row_info = partners_df[partners_df['Org']==partner_name].dropna(axis='columns')

    columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in selected_partner_row_info.columns
        ]
    data = selected_partner_row_info.to_dict('records')
    return [columns, data]
   
# Click on the partner button to generate partners list and save the match in the document
@app.callback(dash.dependencies.Output('clicked_on_partner_table', 'style_cell'), 
            [dash.dependencies.Input('confirm-yes-button', 'n_clicks'),
            dash.dependencies.Input('solver-dropdown', 'value'), 
             dash.dependencies.Input('output_bargraph', 'clickData')])
def partner_select(n_clicks, solver,  table_partner): 
    if n_clicks is None: 
        raise PreventUpdate
    else: 

        style_cell={
                'whiteSpace': 'normal',
                'height': 'auto',
                'textAlign': 'center',
                'font_family': 'helvetica',
                'font_size': '20px',
            }    
        partner_name =  table_partner['points'][0]['y']

        # Make partners list if it does not exist 
        if not os.path.exists(config['track_partners']): 
            partners_list = pd.read_excel(config['total_score_location'])['Org_y'].values.tolist()
        
            solvers =[ '' for x in range(0,len(partners_list))]
            count = [0 for x in range(0,len(partners_list))]
            partners_trackers = pd.DataFrame(data=[partners_list, solvers, count],
                                            index=['partners','solvers', 'counter']).T
            partners_trackers.to_csv(config['track_partners'], index=False)
        else: 
            partners_trackers = pd.read_csv(config['track_partners'])
            
        # check if confirmed matches file exists, if not then create it
        # while creating, label partner-solver matches
        # also make additions to the partners list
        if not os.path.exists(config['confirmed_matches']): 
            total_score = pd.read_excel(config['total_score_location'])
            for col in total_score:
                if not col == 'Org_y':
                    total_score[col].values[:] = 0 

            total_score[solver][total_score['Org_y'] == partner_name] = 1
            partners_trackers['counter'][partners_trackers['partners'] == partner_name] += 1
            partners_trackers['solvers'][partners_trackers['partners']==partner_name] += ', '+solver  
        
            total_score.to_csv(config['confirmed_matches'], index=False)
            partners_trackers.to_csv(config['track_partners'], index=False)
            
            solvers_for_partner = int(total_score.loc[total_score['Org_y']==partner_name].sum(axis=1).values) 
            if solvers_for_partner <= config['partner_inter'] : 
                style_cell['color'] = 'green'
            elif solvers_for_partner > config['partner_inter']  and solvers_for_partner <= config['max_matches']: 
                style_cell['color'] = 'blue'
            else: 
                style_cell['color'] = 'red'

            return style_cell

        else: 
            total_score = pd.read_csv(config['confirmed_matches'])
            
        
            total_score[solver][total_score['Org_y']== partner_name] = 1
            partners_trackers['counter'][partners_trackers['partners'] == partner_name] += 1
            partners_trackers['solvers'][partners_trackers['partners']==partner_name] += ', '+solver  

            solvers_for_partner = int(total_score.loc[total_score['Org_y']==partner_name].sum(axis=1).values) 
            partners_trackers.to_csv(config['track_partners'], index=False)
            total_score.to_csv(config['confirmed_matches'], index=False)
            
            if solvers_for_partner <= config['partner_inter'] : 
                style_cell['color'] = 'green'
            elif solvers_for_partner > config['partner_inter']  and solvers_for_partner <= config['max_matches']: 
                style_cell['color'] = 'blue'
            else: 
                style_cell['color'] = 'red'

            return style_cell    


@app.callback(Output("weights-hidden", "children"), 
              [Input("generate-weights", "n_clicks")])
def generate_weights(n_clicks): 
    if n_clicks is None: 
        PreventUpdate
    else: 

        if not os.path.exists(config['weights']): 

            data_df = pd.read_excel(config['total_score_location'], index=False)
            unpivoted_inital_table = pd.melt(data_df, id_vars="Org_y")
            zero_column = unpivoted_inital_table['value']
            unpivoted_inital_table = unpivoted_inital_table.assign(geo_score=zero_column, 
                                    challenge_score=zero_column,
                                    needs_score=zero_column, 
                                    stage_score=zero_column)
            partners_solvers_weights =  unpivoted_inital_table.drop(columns='value')
            partners_solvers_weights = partners_solvers_weights.rename(columns={"variable":"solver",
                                                                                 "geo_score":"geo_weights",
                                                                                 "challenge_score": "challenge_weights",
                                                                                 "needs_score":"needs_weights",
                                                                                 "stage_score":"stage_weights"})
            cols = ["geo_weights", "challenge_weights", "needs_weights", "stage_weights"] 
            for col in cols:
                partners_solvers_weights[col].values[:] = 1                                                                    
            partners_solvers_weights.to_csv(config['weights'])
        return None 
