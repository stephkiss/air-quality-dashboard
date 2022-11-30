# -*- coding: utf-8 -*-
"""
@author: stephkiss
"""
import requests
import json
from bs4 import BeautifulSoup
import dash
from dash import dcc, html, Input, Output , State 
import dash_bootstrap_components as dbc
import re
import pandas as pd
import geopandas as gpd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np


#Base Dash app initialised
app = dash.Dash(__name__, title='London Air Quality Dashboard', external_stylesheets=[dbc.themes.COSMO])
colors = {
    'background': '#FFFFFF',
    'text': '#000000'
}

def get_responses():
    """Function to get quick air quality forecasts from TfL"""
    
    response=requests.get("https://api.tfl.gov.uk/AirQuality")
    print("Status={}".format(response.status_code))
    data=response.json()
    currentForecast=data["currentForecast"][0]
    summary =  currentForecast["forecastSummary"]
    text=currentForecast["forecastText"]
    
    nO2Band, o3Band, pM10Band, pM25Band, sO2Band = currentForecast["nO2Band"], currentForecast["o3Band"], currentForecast["pM10Band"], currentForecast["pM25Band"],currentForecast["sO2Band"]
    data_dict = [{'nO2Band': nO2Band, 'o3Band':o3Band, 'pM10Band':pM10Band, 'pM25Band':pM25Band, 'sO2Band':sO2Band}]

    soup = BeautifulSoup(text, "html.parser")
    text=soup.get_text()
    text = re.sub('<br/s*?>', '\n', text) #cleaning text
    print(text)

    return text, summary, data_dict

def get_air_qual_map():
    """Function to load detailed latest particulate measurements for London from Imperial College"""

    response=requests.get("http://api.erg.ic.ac.uk/AirQuality//Daily/MonitoringIndex/Latest/GroupName=London/Json")
    print("Status={}".format(response.status_code))
    print(response)
    data=response.json()

    data_dict = []
    for i in range(len(data['DailyAirQualityIndex']['LocalAuthority'])): #for each local authority
        authority = data['DailyAirQualityIndex']['LocalAuthority'][i]['@LocalAuthorityName']

        print(authority)
        if 'Site' in data['DailyAirQualityIndex']['LocalAuthority'][i].keys():
            if isinstance(data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'], list):
                for j in range(len(data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'])): #for each site
                    sitename  = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['@SiteName']
                    lat = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['@Latitude']
                    lon = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['@Longitude']

                    if 'Species' in data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j].keys(): #For each measurements
                        if isinstance(data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species'], list):
                            for k in range(len(data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species'])):
                                abbrev = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species'][k]['@SpeciesCode']
                                desc = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species'][k]['@SpeciesDescription']
                                measurement = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species'][k]['@AirQualityIndex']

                                data_dict.append({'local_authority':authority, 'Site name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'Description':desc, 'value':measurement})
                        else:
                            abbrev = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species']['@SpeciesCode']
                            desc = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species']['@SpeciesDescription']
                            measurement = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species']['@AirQualityIndex']
                            data_dict.append({'local_authority':authority, 'Site name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'Description':desc, 'value':measurement})

                    else:
                        continue
            else:
                sitename  = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['@SiteName']
                lat = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['@Latitude']
                lon = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['@Longitude']
            
                if 'Species' in data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'].keys(): #For each measurements
                        if isinstance(data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species'], list):
                            for k in range(len(data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species'])):
                                abbrev = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species'][k]['@SpeciesCode']
                                desc = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species'][k]['@SpeciesDescription']
                                measurement = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species'][k]['@AirQualityIndex']

                                data_dict.append({'local_authority':authority, 'Site name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'Description':desc, 'value':measurement})
                        else:
                            abbrev = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species']['@SpeciesCode']
                            desc = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species']['@SpeciesDescription']
                            measurement = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species']['@AirQualityIndex']
                            data_dict.append({'local_authority':authority, 'Site name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'Description':desc, 'value':measurement})

                else:
                    continue
        else:
            continue
 

    return data_dict

def blank_figure():
    """Create empty figure as placeholder"""
    figure={
                        'data': [],
                        'layout': go.Layout(
                            xaxis={
                                'showticklabels': False,
                                'ticks': '',
                                'showgrid': False,
                                'zeroline': False
                            },
                            yaxis={
                                'showticklabels': False,
                                'ticks': '',
                                'showgrid': False,
                                'zeroline': False
                            }, 
                            hovermode=False
                        )
                }
         
    return figure

#GET request to TfL to gather some air quality information
@app.callback(
    [Output(component_id='body-text', component_property='children'),
    Output(component_id='summary-text', component_property='children')
    , Output(component_id='pollutant-table', component_property='data')
    ],
    Input(component_id='click-button', component_property='n_clicks')
)
def show_text_on_click(click):
    if click:
        text, summary, _ = get_responses()
        df = pd.DataFrame(get_air_qual_map())

        return text, summary, df.to_json(orient='split')
        
    else:
        return [[],[], []]
    
@app.callback(
    Output(component_id='graph-london', component_property='figure')
    ,
    [Input(component_id='click-button-map', component_property='n_clicks'), 
    Input(component_id='pollutant-table', component_property='data')], 
    [State('measurement-choice', 'value')]
)
def show_map_after_filter(click, df, value):
    if click:
        df = pd.read_json(df,  orient='split')
        df['Level']=pd.to_numeric(df['value']) #filter dataset on particulate type
        df2 = df[df['measurement_code']==value]

        fp = "statistical-gis-boundaries-london/ESRI/London_Borough_Excluding_MHW.shp"
        map_df = gpd.read_file(fp)
        map_df = map_df.to_crs(4326) #convert to lat/long
        gdf = gpd.GeoDataFrame(
            df2, geometry=gpd.points_from_xy(df2.longitude, df2.latitude),crs=4326)

        fig = (
        px.scatter_mapbox(
            gdf,
            lat=gdf.geometry.y,
            lon=gdf.geometry.x,
            color="Level",
            hover_data=["Description", "Level", "Site name"],
        )
        .update_traces(marker={"size": 15})
        .update_layout(
            mapbox={
                "style": "open-street-map",
                "zoom": 8,
                "layers": [
                    {
                        "source": json.loads(map_df.geometry.to_json()),
                        "type": "line",
                        "color": "blue",
                        "line": {"width": 0.5},
                    }
                ],
            }
        )
    )
    else:
        fig = blank_figure()
    return fig
    


@app.callback(
    [Output(component_id='measurement-choice', component_property='options'), 
    Output(component_id='measurement-choice', component_property = 'style'), 
    Output(component_id='click-button', component_property = 'style'), 
    Output(component_id='click-button-map', component_property = 'style'), 
    Output(component_id='left-card', component_property = 'style'), 
    Output(component_id='right-card', component_property = 'style')
    ],
    [Input(component_id='click-button', component_property='n_clicks'), 
    Input(component_id='pollutant-table', component_property='data')] 
)
def show_unique_codes(click, df): #only display certain elements after button has been pressed
    if click:
        df = pd.read_json(df,  orient='split')
        options = list(np.unique(df['measurement_code']))

        return [{'label':o, 'value':o} for o in options], {'display': 'block'}, {'display': 'none'}, {'display': 'block'}, {'display': 'block'}, {'display': 'block'}
    else: 
        return [],  {'display': 'none'}, {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, {'display': 'none'}


#Simple column layout with text components
left_column_text = dbc.Card(id='left-card', children=
    [ dbc.CardHeader(id='card-header', children="Today's forecast"), 

        dbc.Row([
            html.Label('Forecast summary:', style={"font-weight": "bold"}), 
            html.Div(id ='summary-text'), 
            html.Label('Detailed forecast:', style={"font-weight": "bold"}),
            html.Div(id='body-text')
        ]

        )
    ], 
    color='info', 
    outline=True, 
    className='mini_container'
)

#Display map and dropdown options in a column
right_column_map = dbc.Card(id='right-card', children=
    [ dbc.CardHeader(id='card-header-2', children="Map of pollutant levels in London "), 
        dbc.Row([
            html.Div([
            html.Label('Choose pollutant to display:'),   
            dcc.Dropdown(id='measurement-choice',                 
                                placeholder="Select a pollutant" 
                                )
        ], style= {'width': '30%', 'padding':'10px'})], justify='center'),
        dbc.Row([
            dbc.Col(
                html.Button('Get map', id='click-button-map', n_clicks=0, className = 'loginButton')                
                )]),

        dbc.Row([                             
            dcc.Graph(id='graph-london')]
        )
    ], 
    color='info', 
    outline=True, 
    className = 'mini_container'
)
app.layout =dbc.Container([
    
    html.H1(
        children='London Air Quality dashboard',
        style={
            'textAlign': 'center',
            'color': colors['text'], 
            'font-family': 'monospace'
        }
    ),
    html.Hr(), 
    dbc.Row(
        dbc.Col(
            html.Button('Get forecast', id='click-button', n_clicks=0, className='loginButton') 
            )
        ), 
    dbc.Row(    
        [    
        dbc.Col(dcc.Loading(id="ls-loading-1",children = left_column_text, type='circle'), md=4), 
        dbc.Col(dcc.Loading(id="ls-loading-2",children = right_column_map, type='circle'), md=8)
        ] 
            ) ,
    dbc.Row(    
        [    
        dcc.Store(
                id='pollutant-table') #persist data in session 
        ], align='center'
            )]
    )

    
#Run app with built-in backend 
if __name__ == '__main__':
    app.run_server(debug=True)

