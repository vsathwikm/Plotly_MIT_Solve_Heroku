import dash
from flask import Flask 
import dash_auth



# for adding basic Auth 
VALID_USERNAME_PASSWORD_PAIRS = {
    'mit': 'solve2020'
}


# server = Flask(__name__) # define flask app.server

app = dash.Dash(__name__, suppress_callback_exceptions=True, external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.config.suppress_callback_exceptions = True
server = app.server
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
    