import os
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import dash
import plotly.graph_objects as go
from dash.dependencies import Output, Input

# APP LAYOUT
layout1 = html.Div(children=[
    html.H1(
        children='MIT SOLVE',
        style={
            'textAlign': 'center'
            
        }
    ),

    # Upload files button
    dcc.Upload(
        id='upload-data',
        children=html.Button('Upload Excel Data File', id='upload_button', n_clicks=0),
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

    # update solvers button
     html.Div([

        html.A(html.Button('Update solvers'),
               n_clicks=0, 
               id='update-solvers-button'),
    ],
    style={
        'height': '60px',
        'textAlign': 'left',
    },
    id='solver-button-div'),

    # Solver drop down menu 
    html.Div([
                html.Label('Select a Solver'),
                dcc.Dropdown(
                id='solver-dropdown',
                value = '',  
            )
    ]), 
   

    # A few line breaks to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),    

    # 2 side by side graphs
    html.Div([
        html.Div([
            # Title for the horizontal bar graph
             html.H2(children='Total Outputs Graph', style={'textAlign': 'center'}),
             # Horizontal total outputs graph
            dcc.Graph( 
                id='output_bargraph',
                # figure= total_fig
            ),
        ], className="six columns"),

        html.Div([
            html.H3(id='individual_graph_title', children='Individual Graph', style={'textAlign': 'center'}),
            dcc.Graph(id='individual_graph', figure={'data': []})
        ], className="six columns"),
    ], className="row"),


    html.H4(id='weights_directions', children='Adjust Weight Values inside of Brackets Only --> [ ] '),
    # 2 side by side comment boxes for weights
    html.Div([
        html.Div([
            # Comment box 1
            dcc.Textarea(
                id='geo-weight',
                value='Textbox1', # initial value
                style={'display':'inline-block', 'width': '30%', 'height': '10%',},
            ),
        ], className="four columns"),
        html.Div([
            # Comment box 2
            dcc.Textarea(
                id='needs-weight',
                value='Textbox2', # initial value
                style={'display':'inline-block', 'width': '30%', 'height': '10%',},
            ),
        ], className="four columns")        
    ], className="row"),

    # 2 side by side comment boxes for weights
    html.Div([
        html.Div([
            # Comment box 3
            dcc.Textarea(
                id='challenges-weight',
                value='Textbox3', # initial value
                style={'display':'inline-block', 'width': '30%', 'height': '10%',},
            ),
        ], className="four columns"),
        html.Div([
            # Comment box 4
            dcc.Textarea(
                id='stage-weight',
                value='Textbox4', # initial value
                style={'display':'inline-block', 'width': '30%', 'height': '10%',},
            ),
        ], className="four columns"),      
    ], className="row"),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.Button('Submit Changes to Weights', id='submit-val', n_clicks=0),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.Div(id='confirmation-text',
             children='Press Submit to Edit Weights'),

    # Generates the table for the selected solver
    # selected_solver_row_info is that data of the seleced solver
    # that will go into the table
    html.H4(children='Selected Solver Information',style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='selected_solver_table',
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

      html.H4(children='Clicked on Partner Information',style={'textAlign': 'center'}),
    dash_table.DataTable(
        id='clicked_on_partner_table',
        style_cell={
            'whiteSpace': 'normal',
            'height': 'auto',
            'textAlign': 'center',
            'font_family': 'helvetica',
            'font_size': '20px',
            'color': 'green'
        },
        style_header={
        'backgroundColor': 'rgb(30, 30, 30)',
        'color': 'white',
        },
    ),

    # A few line breaks to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
   
    # Generate a checkbox that determines whether the current partner and solver are matched
    html.H3(children='Click Checkbox to Confirm Match between Selected Solver and Selected Partner',
        style={'textAlign': 'center'}
    ),
    
    html.Div([
              dcc.RadioItems(
        id='checkbox_confirm',
        value="No",
        style={
            'textAlign': 'center',
        },
        # set intitial value to 'denied' which means no match
        inputStyle={"margin-right": "20px"},
        labelStyle={'display': 'inline-block'}
    ),  
            html.Button("Confirm", id="checkbox_confirm-button")
    ]), 

    
    html.Div([ 
            html.Div([html.Button("Yes", id="confirm-yes-button")])
    ], className="row"),


    # A line break to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # Generates table for the partner that is clicked on in the graph
    # selected_partner_row_info is that data of the seleced partner
    # that will go into the table - initially this table won't be populated
  
    html.H4(children='Green = 0-1 matches, Blue = 2-3 matches, Red = 4 or more matches',style={'textAlign': 'center'}),

    # A few line breaks to make dashboard less crowded
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # Used to print out the newly calculated total score dataframe from
    # the uploaded files. Should only be used for debugging and is not set 
    # to be functional right now
    html.Div(id='output-data-upload'),

    # Print the solver matches for the selected partner below the partner table
    html.Div(id='partner-matches-list',
    children=[]),

    # Break line to space out the dashboard
    html.P(children=html.Br(), style={'textAlign': 'center'}),

    # hidden layout which is target of callbacks that don't update anything but
    # plotly dash requires outputs for all callbacks
    html.Div(id='hidden-div', style={'display':'None'}),

    # Comment box
    dcc.Textarea(
        id='textarea-for-comments',
        value='Text area for comments', # initial value
        style={'width': '50%', 'height': 200, 'Align-items': 'center'},
    ),
])
