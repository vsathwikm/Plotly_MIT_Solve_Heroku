import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import server, app
from layouts import layout1
import callbacks

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/' or pathname=='index':
         return layout1
    else:
        return '404'

if __name__ == '__main__':
    app.run_server(host='127.0.0.1', port=8080, debug=True)
    # app.run_server(debug=True)
