import os
import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server # the Flask app

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

# Getting first Solver Table
solver_needs_df = pd.read_csv("excel_to_csv/solver_team_data.csv")
selected_solver_row_info = solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns')
selected_solver_row_info_list = list(solver_needs_df[solver_needs_df['Org']==Solvers[0]].dropna(axis='columns'))

# Getting first Mentor Table
mentor_data_df = pd.read_csv("excel_to_csv/partner_data.csv")
selected_mentor_row_info = mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns')
selected_mentor_row_info_list = list(mentor_data_df[mentor_data_df['Org']==Mentors[0]].dropna(axis='columns'))


# creates a dictionary to put in options of selected_solver_table
selected_solver_row_list = []
for col in selected_solver_row_info:
    ind_row_dict = {}
    ind_row_dict["label"] = col
    ind_row_dict["value"] = selected_solver_row_info[col]
    selected_solver_row_list.append(ind_row_dict)


# creates a dictionary to put in options of drop down menu
solver_list_dict = []
for solver in Solvers:
    ind_solver_dict = {}
    ind_solver_dict["label"]=solver
    ind_solver_dict["value"]=solver
    solver_list_dict.append(ind_solver_dict)

# generates tables
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

app.layout = html.Div(children=[
    html.H1(
        children='MIT_SOLVE',
        style={
            'textAlign': 'center'
            
        }
    ),

    # drop down menu
    html.Label('Select a Solver'),
        dcc.Dropdown(
            id='Solver_dropdown',
            options= solver_list_dict,
            value = solver_list_dict[0]['value'], 
           ),

    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.P(children=html.Br(), style={'textAlign': 'center'}),
    html.H2(children='Total Outputs Graph', style={'textAlign': 'center'}),

    # display graph
    dcc.Graph( 
        id='output_bargraph',
        figure= total_fig
    ),

    # generate table for solver
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

    # generate table for mentor
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


if __name__ == '__main__':
    app.run_server(debug=True)