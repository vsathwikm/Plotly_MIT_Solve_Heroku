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

# writing to excel files
import openpyxl
import yaml 
from dash.exceptions import PreventUpdate
import time
import os 
import numpy as np
from openpyxl import load_workbook
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
        if number_sheets == 4: 
            partner_solver_weights = pd.read_excel(config['outputs'] + config['partner-solver-inital-weights'], sheet_name= 'Partner Solver Weights')
            geo_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'geo_weights']], columns='Org_x', index='Org_y' )
            needs_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'needs_weights']], columns='Org_x', index='Org_y' )
            challenge_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'challenge_weights']], columns='Org_x', index='Org_y' )
            stage_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'stage_weights']], columns='Org_x', index='Org_y' )
            tech_weights_pivot = pd.pivot(partner_solver_weights[['Org_y', 'Org_x', 'tech_weights']], columns='Org_x', index='Org_y' )
            
            # List_of_uploaded_files is fully available here
            new_total_score = create_total_score_excel(config['outputs'],
                                                        geo_weights_pivot,
                                                        needs_weights_pivot,
                                                        challenge_weights_pivot, 
                                                        stage_weights_pivot, 
                                                        tech_weights_pivot )
            
                   # new_total_score.insert(0, "Partners", Partners, True)
            children = "Generated outputs"
            solver_df =  pd.read_csv(config['solver_location'])
            partners_df = pd.read_csv(config['partner_location'])
            solver_options = solver_df['Org']
            solver_options = solver_options.to_frame(name='Solvers')
            matches = ['None' for x in range(0, solver_options.shape[0])]
            solver_options['matches'] = matches
            solver_options.to_excel(config['solver_options'], sheet_name='Solver Options', index=False)       
           
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
        if number_sheets < 3: 
            

            partner_solver_weights = zebra.inital_partner_solver_weights(solver_df, partners_df)
            num_partners = len(partners_df['Org'])
            partner_names = partners_df['Org'].values
            none_list = ['None' for x in range(0,num_partners)]
            count_list = [0 for x in range(0, num_partners)]
            comments_list = ['None' for x in range(0, num_partners)]
            partners_match_count = pd.DataFrame(data=[partner_names, none_list, count_list, comments_list], index=['Partners', 'Solvers', 'Count', 'Comments']).T
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
    geo_df = pd.read_excel(config['geo_match']).sort_values(value,  ascending=False)[:50] 
    needs_df = pd.read_excel(config['needs_match']).sort_values(value,  ascending=False)[:50]
    stage_df = pd.read_excel(config['stage_match']).sort_values(value,  ascending=False)[:50]
    challenge_df = pd.read_excel(config['challenge_match']).sort_values(value,  ascending=False)[:50]
    tech_df = pd.read_excel(config['tech_match']).sort_values(value,  ascending=False)[:50]
    partners_for_solver = uploaded_df_total_score.sort_values(value,  ascending=False)[:50]

    total_score_df  = partners_for_solver['Org_y'].to_frame()

    total_score_df = total_score_df.assign(geo_score=geo_df[ value].values*config['geo_weight'], 
                                            needs_score=needs_df[value].values*config['needs_weight'],
                                            stage_score=stage_df[value].values*config['stage_weight'],
                                            challenge_score=challenge_df[value].values*config['challenge_weight'],
                                            tech_score=tech_df[value].values*config['tech_weight'])
    total_score_df['total_score'] = total_score_df.sum(axis=1, skipna=True)

    total_fig = px.bar(total_score_df.sort_values('total_score', ascending=True),
                    x=['geo_score', 'needs_score', 'stage_score', 'challenge_score', 'tech_score'], 
                    y="Org_y",
                    title = "Output graph for {}".format(value),
                    labels = {'Org_y':'PARTNER',
                                value:'Total Score'},
                    hover_data=["total_score"]            
                    )

    total_fig.update_layout(height=1200)
    # total_fig.update_layout(xaxis={'categoryorder':'total ascending', 'dtick':1}, height=1200)
    return total_fig


# This method will update the table displaying more information
# on the partner that is clicked on in the graph and also create the 
# additional individual graph
@app.callback(
    [Output('individual_graph', 'figure'),
    Output('individual_graph_title', 'children')],
    [Input('output_bargraph', 'clickData'),
     Input('submit-val', 'n_clicks'),
    Input('solver-dropdown', 'value')]
    )
def update_individual_graph(clickData, n_clicks, solver_name):
    '''
    param: clickData (Plotly Dash Object) - data that is collected from clicking on graph
    param: solver_name (str) - name of the selected solver from the dropdown menu
    return: figure (Plotly Express Bar Chart) - individual graph of category values
    return: children (str) - customized title for individual graph
    '''
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    if "solver-dropdown" in changed_id: 
        figure={'data': []}
        return [figure, '']

    # Check to make sure a partnere is selected
    if clickData != None and ("n_clicks" in changed_id or "output_bargraph" in changed_id):
        
        # Must get value for partner compared to solver in: geo, needs, stage, challenge
        partner_solver_weights = pd.read_excel(config['outputs'] +config['partner-solver-inital-weights'], sheet_name='Partner Solver Weights')
        
        partner_name = clickData['points'][0]['y']

        geo_df = pd.read_excel(config['geo_match'])
        geo_value = float(geo_df[geo_df["Org_x"]==partner_name].iloc[0][solver_name])
        needs_df = pd.read_excel(config['needs_match'])
        needs_value = float(needs_df[needs_df["Org_x"]==partner_name].iloc[0][solver_name])

        stage_df = pd.read_excel(config['stage_match'])
        stage_value = float(stage_df[stage_df["Org_x"]==partner_name].iloc[0][solver_name])

        challenge_df = pd.read_excel(config['challenge_match'])
        challenge_value = float(challenge_df[challenge_df["Org_x"]==partner_name].iloc[0][solver_name])

        tech_df = pd.read_excel(config['tech_match'])
        tech_value = float(tech_df[tech_df["Org_x"]==partner_name].iloc[0][solver_name])

        cw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['challenge_weights'].values[0]
        gw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['geo_weights'].values[0]
        nw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['needs_weights'].values[0]
        sw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['stage_weights'].values[0]
        tw = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['tech_weights'].values[0]
        
        challenge_term = float(cw)*float(config['challenge_weight'])*challenge_value
        needs_term =  float(nw)*float(config['needs_weight'])*needs_value
        geo_term = float(gw)*float(config['geo_weight'])*geo_value
        stage_term = float(sw)*float(config['stage_weight'])*stage_value
        tech_term = float(tw)*float(config['tech_weight'])*tech_value
        total_score = challenge_term + needs_term + geo_term + stage_term + tech_term 
       
        partner_values_dict = {'Labels': ['Challenges Score', 'Needs Score',
        'Geo Score', 'Stage Score', 'Tech Score'], 'Scores': [challenge_term, needs_term, geo_term, stage_term, tech_term ]}

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
    selected_solver_row_info  = solver_needs_df[solver_needs_df['Org']==value]
    single_row = solver_needs_df[solver_needs_df['Org'] == value].T.reset_index()
    single_row  = single_row.rename(columns = {single_row.columns[1]:'Row'})
    single_row = single_row.replace("Noval", np.nan)
    single_row = single_row.dropna(axis=0)
    columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in single_row.columns
        ]
    data = single_row.to_dict('records')
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
    selected_partner_row_info  = partners_df[partners_df['Org']==partner_name]
    single_row = partners_df[partners_df['Org'] == partner_name].T.reset_index()
    single_row  = single_row.rename(columns = {single_row.columns[1]:'Row'})
    single_row = single_row.replace("Noval", np.nan)
    single_row = single_row.dropna(axis=0)
    columns=[
            {"name": i, "id": i, "deletable": False, "selectable": True} for i in single_row.columns
        ]
    data = single_row.to_dict('records')
    return [columns, data]





@app.callback([ Output("geo-weight", "value"),
                Output("stage-weight", "value"), 
                Output("challenge-weight", "value"), 
                Output("needs-weight", "value"),
                Output("tech-weight", "value")],
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
            tech_weights = partner_solver_pair[['tech_weights']].astype(str).values.tolist()

            return [geo_weights[0][0], stage_weights[0][0], challenge_weights[0][0], needs_weights[0][0], tech_weights[0][0]]
        else: 
            return ["1","1","1","1","1"]

@app.callback(Output("hidden-div2", "children"),
                [Input("submit-val", "n_clicks"), 
                Input("geo-weight", "value"),
                Input("stage-weight", "value"), 
                Input("challenge-weight", "value"), 
                Input("needs-weight", "value"),
                Input("tech-weight", "value"),
                Input('output_bargraph', 'clickData')],
                [State('solver-dropdown', 'value')]
               )
def write_weights(clicks, gw, sw, cw, nw, tw, clickData, solver_name): 

    partner_name = clickData['points'][0]['y']
    partner_solver_weights = pd.read_excel(config['outputs']+config['partner-solver-inital-weights'], sheet_name='Partner Solver Weights')
    
    # Add the entered weighted to weight matrix
    partner_solver_row = partner_solver_weights[(partner_solver_weights['Org_x'] == solver_name) & (partner_solver_weights['Org_y'] == partner_name)]['geo_weights'].index
    partner_solver_weights.loc[partner_solver_row, 'geo_weights'] = gw
    partner_solver_weights.loc[partner_solver_row, 'challenge_weights'] = cw
    partner_solver_weights.loc[partner_solver_row, 'needs_weights'] = nw
    partner_solver_weights.loc[partner_solver_row, 'stage_weights'] = sw
    partner_solver_weights.loc[partner_solver_row, 'tech_weights'] = tw
    partner_solver_weights.to_excel(config['outputs'] +config['partner-solver-inital-weights'], sheet_name='Partner Solver Weights', index=False)
    return None 

@app.callback(Output("hidden-div", "children"),
                [Input("submit-val", "n_clicks"), 
                Input("geo-weight", "value"),
                Input("stage-weight", "value"), 
                Input("challenge-weight", "value"), 
                Input("needs-weight", "value"),
                Input("tech-weight", "value"),
                Input('output_bargraph', 'clickData')],
                [State('solver-dropdown', 'value')]
               )
def update_total_score(clicks, gw, sw, cw, nw, tw,  clickData, solver_name):

        partner_name = clickData['points'][0]['y']
       
        # Get total score from excel sheet
        total_score_df = pd.read_excel(config['total_score_location'], sheet_name="Sheet1")
        
        geo_df = pd.read_excel(config['geo_match'])
        geo_value = float(geo_df[geo_df["Org_x"]==partner_name].iloc[0][solver_name])
        
        needs_df = pd.read_excel(config['needs_match'])
        needs_value = float(needs_df[needs_df["Org_x"]==partner_name].iloc[0][solver_name])

        stage_df = pd.read_excel(config['stage_match'])
        stage_value = float(stage_df[stage_df["Org_x"]==partner_name].iloc[0][solver_name])

        challenge_df = pd.read_excel(config['challenge_match'])
        challenge_value = float(challenge_df[challenge_df["Org_x"]==partner_name].iloc[0][solver_name])

        tech_df = pd.read_excel(config['tech_match'])
        tech_value = float(tech_df[tech_df["Org_x"]==partner_name].iloc[0][solver_name])

        challenge_term = float(cw)*float(config['challenge_weight'])*challenge_value
        needs_term =  float(nw)*float(config['needs_weight'])*needs_value
        # geo_stage_term =  float(sw)*float(gw)*float(config['geo_stage_weight'])*geo_value*stage_value
        geo_term = float(gw)*float(config['geo_weight'])*geo_value
        stage_term = float(sw)*float(config['stage_weight'])*stage_value
        
        tech_term = float(tw)*float(config['tech_weight'])*tech_value


        total_score = challenge_term + needs_term + geo_term + stage_term + tech_term

        total_score_df[solver_name][(total_score_df['Org_y'] == partner_name)] = str(total_score)
        

        total_score_df.to_excel(config['total_score_location'], index=False)
        return None




# Click on the partner button to generate partners list and save the match in the document
@app.callback(Output('confirm-yes-button', 'style'),
            [Input('confirm-yes-button', 'n_clicks'),
             Input('output_bargraph', 'clickData'),
             Input('solver-dropdown', 'value'),
             Input('confirm-delete-button', 'n_clicks')])
def partner_select(n_clicks, partner_state,  solver, delete_button): 
    # if n_clicks is None: 
    #     raise PreventUpdate
    # else:   
    style={
                    # 'height': '60px',
                    'textAlign': 'center',
                    'background-color': ' #1a1c23'
            }
        
    partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match") 
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    solver_options = pd.read_excel(config['solver_options'])
    
    if "output_bargraph" in changed_id: 
        partner_name =  partner_state['points'][0]['y'] 
   
        # Check partner is already partnered with solver 
        # check_solver = zebra.check_solver(partner_match_count, partner_name, solver)
        
        list_matches = solver_options[solver_options['Solvers'] == solver]['matches'].tolist()[0].split(',')
        if partner_name in list_matches: 
            
            style={
                    # 'height': '60px',
                    'textAlign': 'center',
                    'background-color':'green'
                }
        
        else: 
            style={
                    # 'height': '60px',
                    'textAlign': 'center',
                    'background-color':' #1a1c23'
                }
        

    elif "confirm-yes-button" in changed_id:        
        partner_name =  partner_state['points'][0]['y']       
        outputs = zebra.update_colval(partner_match_count, solver, partner_name, "Partners", "Solvers")
        solver_match_update = zebra.update_colval(solver_options, partner_name, solver, "Solvers", "matches")
        if outputs != 1:
            print("outputs is not 1") 
            partner_match_output = outputs[0]
            partner_match_output.to_excel(config['partner_match'], sheet_name="Partner Match", index=False)
            solver_match_update[0].to_excel(config['solver_options'], index=False)     
            
            match_row = pd.DataFrame({'partner': [partner_name], 'solver': [solver],  'match': ['yes'],  'datetime': [str(datetime.datetime.now())],})
            writer = pd.ExcelWriter(config['history'], engine='openpyxl')
            writer.book = load_workbook(config['history'])
            writer.sheets = dict((ws.title, ws) for ws in writer.book.worksheets)
            reader = pd.read_excel(config['history'])
            match_row.to_excel(writer,index=False,header=False,startrow=len(reader)+1)
            writer.close()


                    

        style={
                    # 'height': '60px',
                    'textAlign': 'center',
                    'background-color': 'green'
            }        
    elif "confirm-delete-button" in changed_id: 
        style={
                    # 'height': '60px',
                    'textAlign': 'center',
                    'background-color': ' #1a1c23'
            }
            
    return style


## DELETE BUTTON
@app.callback(Output('confirm-msg', 'children'), 
            [Input('confirm-delete-button', 'n_clicks'),
              Input('output_bargraph', 'clickData'), 
              Input('solver-dropdown', 'value')])
def partner_delete(n_clicks, partner_state, solver  ): 
    if n_clicks is None: 
        raise PreventUpdate
    else:   
        solver_options = pd.read_excel(config['solver_options'], )
        partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match")
        changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
        msg = " "        
        if "confirm-delete-button" in changed_id: 
            partner_name =  partner_state['points'][0]['y']       
            outputs = zebra.delete_colval(partner_match_count, solver, partner_name, "Partners", "Solvers")
            delete_partner = zebra.delete_colval(solver_options, partner_name, solver, "Solvers", "matches")    
            if outputs != 0: 
                partner_match_output = outputs[0]
                partner_match_output.to_excel(config['partner_match'], sheet_name="Partner Match", index=False)
                delete_partner[0].to_excel(config['solver_options'], index=False)  
                msg = "Deleted value"
              
            else: 
                msg = "Nothing to delete"
              
    return msg


@app.callback(Output('clicked_on_partner_table', 'style_cell'),
            [Input('confirm-yes-button', 'n_clicks'),
             Input('confirm-delete-button', 'n_clicks'),
             Input('output_bargraph', 'clickData'), 
             Input('solver-dropdown', 'value')])
def style_partner_table(yes_button, delete_button, partner_click, solver): 
    partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match")
    style_cell={
                'whiteSpace': 'normal',
                'height': 'auto',
                'textAlign': 'center',
                'font_family': 'helvetica',
                'font_size': '12px',
            }   
    if partner_click:
        partner_name=  partner_click['points'][0]['y']  
        col_indx = partner_match_count[partner_match_count['Partners'] == partner_name].index.values[0]
        cell_val = partner_match_count.at[col_indx, "Solvers"]
        cell_val = cell_val.split(',')
        count = len(cell_val)
        
        if count <= 2: 
            style_cell['color'] = 'green'
        elif count >2 and count <= 4:
            style_cell['color'] = 'blue'
        else:
            style_cell['color'] = 'red'
        
    return style_cell


@app.callback(Output('comment-status','children' ),
              [Input('comment-box', 'value'), 
              Input('confirm-comment-button','n_clicks'),
              Input('output_bargraph', 'clickData'), 
              Input('solver-dropdown', 'value')])
def add_comments(comments, comment_btn, partner_state, solver ): 
    partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match")
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    partner_name = partner_state['points'][0]['y']
    if 'confirm-comment-button' in changed_id: 
        col_indx = partner_match_count[partner_match_count['Partners'] == partner_name].index.values[0]
        partner_match_count.at[col_indx, "Comments"] = comments        
        partner_match_count.to_excel(config['partner_match'], sheet_name="Partner Match", index=False)
        children = "Added comment"
        return children
    else: 
        children = " "
        return children


@app.callback(Output('comment-box','value' ),
              [Input('output_bargraph', 'clickData'), 
              Input('solver-dropdown', 'value')])
def popluate_comment_box(partner_state, solver): 
    partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match")
    changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]
    partner_name = partner_state['points'][0]['y']
    
    if "output_bargraph" in changed_id: 
        col_indx = partner_match_count[partner_match_count['Partners'] == partner_name].index.values[0]
        comments = partner_match_count.at[col_indx, "Comments"] 
        return comments
    

@app.callback(
    Output('download-link', 'href'),
    [Input('download-link', 'n_clicks')])
def download_update(n_clicks): 
    return  '/dash/urldownload'
@app.server.route('/dash/urldownload')
def download_update():
    
    solver_df =  pd.read_csv(config['solver_location'])
    partners_df = pd.read_csv(config['partner_location'])
    partner_solver_weights = pd.read_excel(config['outputs'] + config['partner-solver-inital-weights'])
    partner_match_count = pd.read_excel(config['partner_match'], sheet_name="Partner Match")
   
    with pd.ExcelWriter(config['output_weights'], mode='w') as writer: 
                solver_df.to_excel(writer, sheet_name='Solver Team Data', index=False)
                partners_df.to_excel(writer, sheet_name='Partner Data', index=False)
                partner_solver_weights.to_excel(writer, sheet_name='Partner Solver Weights', index=False)
                partner_match_count.to_excel(writer, sheet_name="Partner Match", index=False)
    shutil.make_archive(config['zipf_name'], 'zip', 'outputs/')
    return send_file(config['zipped'],
            mimetype = 'zip',
            attachment_filename= config['zipped'],
            as_attachment = True)


@app.callback(
    Output('get-initial-weights', 'href'),
    [Input('get-initial-weights', 'n_clicks')])
def download_weights(n_clicks): 
    return  '/dash/download-weights/'
@app.server.route('/dash/download-weights/')
def download_weights():
    """ Download all files in the outputs folder 
    :return: Zip file containing all the files in the outputs folder
    :rtype: zip file
    """

    
    return send_file(config['output_weights'],
            mimetype = 'xlsx',
            attachment_filename= config['partner-solver-inital-weights'],
            as_attachment = True)

