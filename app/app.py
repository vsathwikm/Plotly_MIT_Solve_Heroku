import dash
from flask import Flask 
import dash_auth



# # for adding basic Auth 
# VALID_USERNAME_PASSWORD_PAIRS = {
#     'mit': 'solve2020'
# }

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# styles = {
#     'pre': {
#         'border': 'thin lightgrey solid',
#         'overflowX': 'scroll'
#     }
# }


# # the Flask app
# app = Flask(__name__) 
# app = dash.Dash(__name__, external_stylesheets=external_stylesheets, server=app)

import dash

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'])
server = app.server


# server = app.server 
# auth = dash_auth.BasicAuth(
#     app,
#     VALID_USERNAME_PASSWORD_PAIRS
# )
