# Used to graph electricity data from Bayou Energy for the user.


from fastapi import FastAPI, Query, Path
from pydantic import BaseModel
import numpy as np
import requests
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, callback, Output, Input
# While the Bayou pulls aren't working I've included some dummy data that we can use

dummonth = ["January 2024", "December 2023", "November 2023", "October 2023", "September 2023", "August 2023", "July 2023", "June 2023", "May 2023", "April 2023", "March 2023", "February 2023"]
dumelec = [52.831, 52.655, 94.642, 25.031, 42.981, 25.413, 73.575, 90.008, 92.173, 13.962, 47.757, 87.798]
dumgas = [27001, 53099, 18340, 61400, 68329, 63334, 81523, 90973, 71470, 63650, 37285, 63207]
dumelecc = [108.53, 61.20, 164.28, 135.03, 156.93, 173.56, 157.22, 98.54, 173.10, 129.48, 115.60, 94.74]
dumgasc = [75.50, 40.07, 90.60, 86.42, 57.33, 12.75, 85.91, 72.98, 44.37, 17.13, 51.56, 10.84]

dumdict = {
    'Service Months': dummonth,
    'Electricity Consumption': dumelec,
    'Gas Consumption': dumgas,
    'Electricity Cost': dumelecc,
    'Gas Cost': dumgasc
           }

df = pd.DataFrame(dumdict)
app = Dash(__name__, requests_pathname_prefix='/electricity_graph/')

app.layout = html.Div([
# We can reformat this going forward
    html.Div(className='row', children=[
        dcc.RadioItems(options=[
                            {'label': 'Electricity Consumption', 'value': 'Electricity Consumption'},
                            {'label': 'Gas Consumption', 'value': 'Gas Consumption'},
                            {'label': 'Electricity Cost', 'value': 'Electricity Cost'},
                            {'label': 'Gas Cost', 'value': 'Gas Cost'}
                        ],
                       value='Electricity Consumption',
                       inline=True,
                       id='radios')
    ]),
    html.Div(id='elec_graph'),
])

@app.callback(
    Output('elec_graph', 'children'),
    Input('radios','value')
)
def update_graph(radio_value):
    dff = dfupdate(radio_value, df)
    fig = px.bar(dff,
                        x="Service Months",
                        y=radio_value,
                        height=800,
                        width=800)
    fig.update_layout(transition_duration = 100)
    fig.update_layout(mapbox_style="open-street-map")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_layout(showlegend=True)
    graph = dcc.Graph(
        figure = fig,
        id = 'fig2test'
    )
    return graph

def dfupdate(radio_value, df):
    if radio_value == "Electricity Consumption":
        dfslice = df[['Service Months', 'Electricity Consumption']]
    elif radio_value == "Gas Consumption":
        dfslice = df[['Service Months', 'Gas Consumption']]
    elif radio_value == "Electricity Cost":
        dfslice = df[['Service Months', 'Electricity Cost']]
    elif radio_value == "Gas Cost":
        dfslice = df[['Service Months', 'Gas Cost']]
    return dfslice

if __name__ == '__main__':
    app.run_server(debug=True)