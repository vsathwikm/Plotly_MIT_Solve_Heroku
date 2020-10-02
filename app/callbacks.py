import base64
import datetime
import io




# for creating the new total_score.xlsx
from utils.create_total_score import create_total_score_excel
from utils import utils_app
from utils import zebra
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
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc

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
    if not os.path.exists(config['outputs']): 
        os.makedirs(config['outputs'])

    if list_of_contents is not None:
        number_sheets = utils_app.parse_contents(list_of_contents[0], list_of_names[0], list_of_dates[0])
        if number_sheets == 3: 
            partner_solver_weights = pd.read_excel(config['outputs'] + config['partner-solver-inital-weights'], sheet_name= 'Partner Solver Weights')
            geo_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'geo_weights']], columns='Org_x', index='Org_y' )
            needs_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'needs_weights']], columns='Org_x', index='Org_y' )
            challenge_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'challenge_weights']], columns='Org_x', index='Org_y' )
            stage_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'stage_weights']], columns='Org_x', index='Org_y' )
        
            # List_of_uploaded_files is fully available here
            new_total_score = create_total_score_excel(config['outputs'],
                                                        geo_weights_pivot,
                                                        needs_weights_pivot,
                                                        challenge_weights_pivot, 
                                                        stage_weights_pivot )

                   # new_total_score.insert(0, "Partners", Partners, True)
            children = "Generated outputs"
            solver_df =  pd.read_csv(config['solver_location'])
            partners_df = pd.read_csv(config['partner_location'])
            with pd.ExcelWriter(config['output_weights'], mode='w') as writer: 
                solver_df.to_excel(writer, sheet_name='Solver Team Data', index=False)
                partners_df.to_excel(writer, sheet_name='Partner Data', index=False)
                partner_solver_weights.to_excel(writer, sheet_name='Partner Solver Weights', index=False)
        
        else: 
            children = "Input file must be an excel file with three sheets- Solver Team Data, Partner Data, Initial Weights"     
    else: 
        children = "Input file must be an excel file with three sheets- Solver Team Data, Partner Data, Initial Weights"    
    return children

# copied 
@app.callback(
    dash.dependencies.Output('output-gen-weights', 'children'),
    [dash.dependencies.Input('gen-weights', 'contents')],
    [dash.dependencies.State('gen-weights', 'filename'),
    dash.dependencies.State('gen-weights', 'last_modified')])
def update_output2(list_of_contents, list_of_names, list_of_dates):
    '''
    param: contents - all of the files uploaded
    param: filename - name of the uploaded file
    param: last_modified - the date in which the file was last modified
    return: irrelavent output, will never be printed out and is used to 
    comply with needing an Output for every callback
    '''

    if not os.path.exists(config['outputs']):  
        os.makedirs(config['outputs'])

    if list_of_contents is not None:
        number_sheets = utils_app.parse_contents(list_of_contents[0], list_of_names[0], list_of_dates[0])
        solver_df =  pd.read_csv(config['solver_location'])
        partners_df = pd.read_csv(config['partner_location'])
        if number_sheets <= 2: 
            partner_solver_weights = zebra.inital_partner_solver_weights(solver_df, partners_df)
            num_partners = len(partners_df['Org'])
            partner_names = partners_df['Org'].values
            none_list = ['None' for x in range(0,num_partners)]
            count_list = [0 for x in range(0, num_partners)]
            partners_match_count = pd.DataFrame(data=[partner_names, none_list, count_list], index=['Partners', 'Solvers', 'Count']).T
            with pd.ExcelWriter(config['output_weights'], mode='w') as writer: 
                solver_df.to_excel(writer, sheet_name='Solver Team Data', index=False)
                partners_df.to_excel(writer, sheet_name='Partner Data', index=False)
                partner_solver_weights.to_excel(writer, sheet_name='Partner Solver Weights', index=False)
                partners_match_count.to_excel(writer, sheet_name='Partner Match', index=False)
                
            children = list_of_names
            return children 
        else: 
            children = ['Nothing to return']
            return children
    children = list_of_names
    return children


@app.server.route('/download-weights/')
def download_weights():
    """ Download all files in the outputs folder 
    :return: Zip file containing all the files in the outputs folder
    :rtype: zip file
    """

    
    return send_file(config['output_weights'],
            mimetype = 'xlsx',
            attachment_filename= config['partner-solver-inital-weights'],
            as_attachment = True)



# This method allows for you to download all of the generated excel files as a zip file
# Files are challenge_match.xlsx, geo_match.xlsx, needs_match.xlsx, stage_match.xlsx,
# total_score_from_upload.xlsx and mit_solve_confirmed_matches.xlsx
# TODO make sure the correct files are being uploaded - think wrong ones are right now
@app.server.route('/download_all/')
def download_all():
    """ Download all files in the outputs folder 
    :return: Zip file containing all the files in the outputs folder
    :rtype: zip file
    """
    solver_df =  pd.read_csv(config['solver_location'])
    partners_df = pd.read_csv(config['partner_location'])
    partner_solver_weights = pd.read_excel(config['outputs'] + config['partner-solver-inital-weights'])
    with pd.ExcelWriter(config['output_weights'], mode='w') as writer: 
                solver_df.to_excel(writer, sheet_name='Solver Team Data', index=False)
                partners_df.to_excel(writer, sheet_name='Partner Data', index=False)
                partner_solver_weights.to_excel(writer, sheet_name='Partner Solver Weights', index=False)

    shutil.make_archive(config['zipf_name'], 'zip', 'outputs/')
    return send_file(config['zipped'],
            mimetype = 'zip',
            attachment_filename= config['zipped'],
            as_attachment = True)



@app.callback(
    [dash.dependencies.Output('solver-dropdown', 'value'), 
    dash.dependencies.Output('solver-dropdown', 'options')], 
    [dash.dependencies.Input('update-solver-btn', 'n_clicks'),
    dash.dependencies.Input('upload-data', 'contents')],
    [dash.dependencies.State('upload-data', 'filename'),
    dash.dependencies.State('upload-data', 'last_modified')]
    )
def dropdown_options(n_clicks, list_of_contents, list_of_names, list_of_dates):
    """ Populate dropdown menu with Solver names 

    :param n_clicks: Click count of the update solver button
    :type n_clicks: Int
    :param list_of_contents: Binary data of the user uploaded files 
    :type list_of_contents: Binary data
    :param list_of_names: Names of user uploaded files
    :type list_of_names: Str
    :param list_of_dates: Dates when user uploaded files
    :type list_of_dates: Str
    :return: Names of all Solvers uploaded by user
    :rtype: List
    """
    
    if n_clicks is None: 
        PreventUpdate
    else: 

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
    Output('output_bargraph', 'figure'),
    [Input('solver-dropdown', 'value'),
     Input('submit-val', 'n_clicks')])
def update_graph_from_solver_dropdown(value, n_clicks):
    """ Selecting a Solver from the dropdown menu plots of bar graph with top 5 partner matches

    :param value: Solver's name as selected from dropdown
    :type value: Str
    :param n_clicks: Click count of the update solver button
    :type n_clicks: Int
    :return: Plotly bar chart showing the top 5 Partner matches for the selected Solver
    :rtype: Figure
    """
    time.sleep(0.1)
    # while not os.path.exists(config['total_score_location']): 
    #     time.sleep(0.01)
    # Checks if new files have been uploaded yet instead of hard coded
    uploaded_df_total_score = pd.read_excel(config['total_score_location'], sheet_name="Sheet1")

    # Sort and crop top 5 values for new selected solver
    total_fig = px.bar(uploaded_df_total_score.sort_values(value, ascending=False)[:5],
                       x=value, 
                       y="Org_y",
                       labels = {'Org_y':'PARTNER',
                                  value:'Total Score'})

    total_fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return total_fig


# This method will update the table displaying more information
# on the partner that is clicked on in the graph and also create the 
# additional individual graph
@app.callback(
    [Output('individual_graph', 'figure'),
    Output('individual_graph_title', 'children')],
    [Input('output_bargraph', 'clickData'),
     Input('submit-val', 'n_clicks') ],
    [State('solver-dropdown', 'value')]
    )
def update_individual_graph(clickData, n_clicks, solver_name):
    '''
    param: clickData (Plotly Dash Object) - data that is collected from clicking on graph
    param: solver_name (str) - name of the selected solver from the dropdown menu
    return: figure (Plotly Express Bar Chart) - individual graph of category values
    return: children (str) - customized title for individual graph
    '''
    # Check to make sure a partnere is selected
    if clickData != None:
        # Must get value for partner compared to solver in: geo, needs, stage, challenge
        partner_solver_weights = pd.read_excel(config['outputs'] +config['partner-solver-inital-weights'], sheet_name='Partner Solver Weights')

        partner_name = clickData['points'][0]['y']

        geo_df = pd.read_excel(config['geo_match'])
        geo_value = float(geo_df[geo_df["Org_y"]==partner_name].iloc[0][solver_name])
        
        needs_df = pd.read_excel(config['needs_match'])
        needs_value = float(needs_df[needs_df["Org_y"]==partner_name].iloc[0][solver_name])

        stage_df = pd.read_excel(config['stage_match'])
        stage_value = float(stage_df[stage_df["Org_y"]==partner_name].iloc[0][solver_name])

        challenge_df = pd.read_excel(config['challenge_match'])
        challenge_value = float(challenge_df[challenge_df["Org_y"]==partner_name].iloc[0][solver_name])
        cw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['challenge_weights'].values[0]
        gw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['geo_weights'].values[0]
        nw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['needs_weights'].values[0]
        sw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['stage_weights'].values[0]
        
        challenge_term = float(cw)*float(config['challenge_weight'])*challenge_value
        needs_term =  float(nw)*float(config['needs_weight'])*needs_value
        geo_stage_term =  float(sw)*float(gw)*float(config['geo_stage_weight'])*geo_value*stage_value
        geo_term = float(gw)*geo_value
        stage_term = float(sw)*stage_value
        total_score = challenge_term + needs_term + geo_stage_term 

        partner_values_dict = {'Labels': ['Challenges Score', 'Needs Score', 'Geo Score * Stage Score',
        'Geo Score', 'Stage Score'], 'Scores': [challenge_term, needs_term, geo_stage_term, geo_term, stage_term ]}

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





@app.callback([ Output("geo-weight", "value"),
                Output("stage-weight", "value"), 
                Output("challenge-weight", "value"), 
                Output("needs-weight", "value")],
                [Input('output_bargraph', 'clickData'),
                 Input('solver-dropdown', 'value')])
def read_weights(clickData, solver): 
   
    # if clickData: 
        partner_name = clickData['points'][0]['y']
        
        if os.path.exists(config['outputs'] +config['partner-solver-inital-weights']): 
         
            partner_solver_weights = pd.read_excel(config['outputs'] +config['partner-solver-inital-weights'], sheet_name='Partner Solver Weights')
            partner_solver_pair = partner_solver_weights[(partner_solver_weights['Org_x'] == solver) & (partner_solver_weights['Org_y'] == partner_name)]
            
            geo_weights = partner_solver_pair[['geo_weights']].astype(str).values.tolist()
            needs_weights = partner_solver_pair[['needs_weights']].astype(str).values.tolist()
            stage_weights = partner_solver_pair[['stage_weights']].astype(str).values.tolist()
            challenge_weights = partner_solver_pair[['challenge_weights']].astype(str).values.tolist()
            
            return [geo_weights[0][0], stage_weights[0][0], challenge_weights[0][0], needs_weights[0][0]]
        else: 
            return ["1","1","1","1"]

@app.callback(Output("hidden-div2", "children"),
                [Input("submit-val", "n_clicks"), 
                Input("geo-weight", "value"),
                Input("stage-weight", "value"), 
                Input("challenge-weight", "value"), 
                Input("needs-weight", "value"),
                Input('output_bargraph', 'clickData')],
                [State('solver-dropdown', 'value')]
               )
def write_weights(clicks, gw, sw, cw, nw, clickData, solver_name): 

    partner_name = clickData['points'][0]['y']
    partner_solver_weights = pd.read_excel(config['outputs']+config['partner-solver-inital-weights'], sheet_name='Partner Solver Weights')
    
    # Add the entered weighted to weight matrix
    partner_solver_row = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['geo_weights'].index
    partner_solver_weights.loc[partner_solver_row, 'geo_weights'] = gw
    partner_solver_weights.loc[partner_solver_row, 'challenge_weights'] = cw
    partner_solver_weights.loc[partner_solver_row, 'needs_weights'] = nw
    partner_solver_weights.loc[partner_solver_row, 'stage_weights'] = sw
    partner_solver_weights.to_excel(config['outputs'] +config['partner-solver-inital-weights'], sheet_name='Partner Solver Weights', index=False)
    return None 

@app.callback(Output("hidden-div", "children"),
                [Input("submit-val", "n_clicks"), 
                Input("geo-weight", "value"),
                Input("stage-weight", "value"), 
                Input("challenge-weight", "value"), 
                Input("needs-weight", "value"),
                Input('output_bargraph', 'clickData')],
                [State('solver-dropdown', 'value')]
               )
def update_total_score(clicks, gw, sw, cw, nw, clickData, solver_name):

        partner_name = clickData['points'][0]['y']
       
        # Get total score from excel sheet
        total_score_df = pd.read_excel(config['total_score_location'], sheet_name="Sheet1")
        
        geo_df = pd.read_excel(config['geo_match'])
        geo_value = float(geo_df[geo_df["Org_y"]==partner_name].iloc[0][solver_name])
        
        needs_df = pd.read_excel(config['needs_match'])
        needs_value = float(needs_df[needs_df["Org_y"]==partner_name].iloc[0][solver_name])

        stage_df = pd.read_excel(config['stage_match'])
        stage_value = float(stage_df[stage_df["Org_y"]==partner_name].iloc[0][solver_name])

        challenge_df = pd.read_excel(config['challenge_match'])
        challenge_value = float(challenge_df[challenge_df["Org_y"]==partner_name].iloc[0][solver_name])

        challenge_term = float(cw)*float(config['challenge_weight'])*challenge_value
        needs_term =  float(nw)*float(config['needs_weight'])*needs_value
        geo_stage_term =  float(sw)*float(gw)*float(config['geo_stage_weight'])*geo_value*stage_value
        total_score = challenge_term + needs_term + geo_stage_term 

        total_score_df[solver_name][(total_score_df['Org_y'] == partner_name)] = str(total_score)
        total_score_df.to_excel(config['total_score_location'], index=False)

        return None




# Click on the partner button to generate partners list and save the match in the document
@app.callback(dash.dependencies.Output('confirm-yes-button', 'style'),
            [dash.dependencies.Input('confirm-yes-button', 'n_clicks'),
             dash.dependencies.Input('output_bargraph', 'clickData'),
            dash.dependencies.Input('solver-dropdown', 'value')])
def partner_select(n_clicks, partner_state,  solver): 
    if n_clicks is None: 
        raise PreventUpdate
    else:   
        style={
                    'height': '60px',
                    'textAlign': 'center',
                    'background-color': 'white'
            }
        
        partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match") 
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        if "output_bargraph" in changed_id: 
            partner_name =  partner_state['points'][0]['y']       
            # Check partner is already partnered with solver 
            check_solver = zebra.check_solver(partner_match_count, partner_name, solver)
            if check_solver == 1: 
                style={
                        'height': '60px',
                        'textAlign': 'center',
                        'background-color':'green'
                    }
            
            else: 
                style={
                        'height': '60px',
                        'textAlign': 'center',
                        'background-color':'white'
                    }
                
        elif "confirm-yes-button" in changed_id:        
            partner_name =  partner_state['points'][0]['y']       
            outputs = zebra.update_colval(partner_match_count, solver, partner_name, "Partners", "Solvers")
            if outputs != 1: 
                partner_match_output = outputs[0]
                partner_match_output.to_excel(config['partner_match'], sheet_name="Partner Match", index=False)
                style={
                        'height': '60px',
                        'textAlign': 'center',
                        'background-color': 'green'
                }
          
    return style



@app.callback(dash.dependencies.Output('confirm-msg', 'children'), 
            [dash.dependencies.Input('confirm-delete-button', 'n_clicks'),
              dash.dependencies.Input('output_bargraph', 'clickData'), 
              dash.dependencies.State('solver-dropdown', 'value'),])
def partner_delete(n_clicks, partner_state, solver  ): 
    if n_clicks is None: 
        raise PreventUpdate
    else:    
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        
        msg = " "        
        if "confirm-delete-button" in changed_id: 
            partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match")
            partner_name =  partner_state['points'][0]['y']       
            outputs = zebra.delete_colval(partner_match_count, solver, partner_name, "Partners", "Solvers")
            if outputs != 0: 
                partner_match_output = outputs[0]
                partner_match_output.to_excel(config['partner_match'], sheet_name="Partner Match", index=False)
                msg = "Deleted value"
            else: 
                msg = "Nothing to delete"
    return msg


# @app.callback(dash.dependencies.Output('confirm-yes-button', 'style'), 
#             [dash.dependencies.Input('solver-dropdown', 'value'), 
#              dash.dependencies.Input('output_bargraph', 'clickData')])
# def check_partner(solver, table_partner):

#     partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match")
#     if table_partner:     
#         partner_name =  table_partner['points'][0]['y']

#  # Check partner is already partnered with solver 
#     check_solver = zebra.check_solver(partner_match_count, partner_name, solver)
#     if check_solver == 1: 
#         style={
#                 'height': '60px',
#                 'textAlign': 'center',
#                 'color':'green'
#             }
#     else:
#         style={
#                 'height': '60px',
#                 'textAlign': 'center',
#                 'color':'black'
#             }

#     return style

# # Click on the partner button to generate partners list and save the match in the document
# @app.callback(dash.dependencies.Output('clicked_on_partner_table', 'style_cell'), 
#             [dash.dependencies.Input('confirm-yes-button', 'n_clicks'),
#             dash.dependencies.Input('solver-dropdown', 'value'), 
#              dash.dependencies.Input('output_bargraph', 'clickData')])
# def partner_select(n_clicks, solver,  table_partner): 
#     if n_clicks is None: 
#         raise PreventUpdate
#     else: 

#         style_cell={
#                 'whiteSpace': 'normal',
#                 'height': 'auto',
#                 'textAlign': 'center',
#                 'font_family': 'helvetica',
#                 'font_size': '20px',
#             }    
#         partner_name =  table_partner['points'][0]['y']
#         # Make partners list if it does not exist 
#         if not os.path.exists(config['track_partners']): 
#             partners_list = pd.read_excel(config['total_score_location'])['Org_y'].values.tolist()
        
#             solvers =[ '' for x in range(0,len(partners_list))]
#             count = [0 for x in range(0,len(partners_list))]
#             partners_trackers = pd.DataFrame(data=[partners_list, solvers, count],
#                                             index=['partners','solvers', 'counter']).T
#             partners_trackers.to_csv(config['track_partners'], index=False)
#         else: 
#             partners_trackers = pd.read_csv(config['track_partners'])
            
#         # check if confirmed matches file exists, if not then create it
#         # while creating, label partner-solver matches
#         # also make additions to the partners list
#         if not os.path.exists(config['confirmed_matches']): 
#             total_score = pd.read_excel(config['total_score_location'])
#             for col in total_score:
#                 if not col == 'Org_y':
#                     total_score[col].values[:] = 0 

#             total_score[solver][total_score['Org_y'] == partner_name] = 1
#             partners_trackers['counter'][partners_trackers['partners'] == partner_name] += 1
#             partners_trackers['solvers'][partners_trackers['partners']==partner_name] += ', '+solver  
        
#             total_score.to_csv(config['confirmed_matches'], index=False)
#             partners_trackers.to_csv(config['track_partners'], index=False)
            
#             solvers_for_partner = int(total_score.loc[total_score['Org_y']==partner_name].sum(axis=1).values) 
#             if solvers_for_partner <= config['partner_inter'] : 
#                 style_cell['color'] = 'green'
#             elif solvers_for_partner > config['partner_inter']  and solvers_for_partner <= config['max_matches']: 
#                 style_cell['color'] = 'blue'
#             else: 
#                 style_cell['color'] = 'red'

#             return style_cell

#         else: 
#             total_score = pd.read_csv(config['confirmed_matches'])
            
        
#             total_score[solver][total_score['Org_y']== partner_name] = 1
#             partners_trackers['counter'][partners_trackers['partners'] == partner_name] += 1
#             partners_trackers['solvers'][partners_trackers['partners']==partner_name] += ', '+solver  

#             solvers_for_partner = int(total_score.loc[total_score['Org_y']==partner_name].sum(axis=1).values) 
#             partners_trackers.to_csv(config['track_partners'], index=False)
#             total_score.to_csv(config['confirmed_matches'], index=False)
            
#             if solvers_for_partner <= config['partner_inter'] : 
#                 style_cell['color'] = 'green'
#             elif solvers_for_partner > config['partner_inter']  and solvers_for_partner <= config['max_matches']: 
#                 style_cell['color'] = 'blue'
#             else: 
#                 style_cell['color'] = 'red'

#             return style_cell    

    
    # # if table_partner:     
        
    # # # Check partner is already partnered with solver 
    #     check_solver = zebra.check_solver(partner_match_count, partner_name, solver)
    #     print(check_solver, "solver vlaue")
    #     if check_solver == 1: 
    #         style={
    #                 'height': '60px',
    #                 'textAlign': 'center',
    #                 'color':'green'
    #             }
    #     else: 
    #         style={
    #                 'height': '60px',
    #                 'textAlign': 'center',
    #                 'color':'black'
    #             }

    #     print(table_partner)   
    #     if not table_partner:     
