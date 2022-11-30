# -*- coding: utf-8 -*-
"""
@author: stephkiss
"""
import requests
from bs4 import BeautifulSoup
import dash
from dash import dcc, html, Input, Output , dash_table
import re


#Base Dash app initialised
app = dash.Dash()
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

                                data_dict.append({'local_authority':authority, 'site_name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'measurement_descr':desc, 'value':measurement})
                        else:
                            abbrev = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species']['@SpeciesCode']
                            desc = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species']['@SpeciesDescription']
                            measurement = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site'][j]['Species']['@AirQualityIndex']
                            data_dict.append({'local_authority':authority, 'site_name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'measurement_descr':desc, 'value':measurement})

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

                                data_dict.append({'local_authority':authority, 'site_name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'measurement_descr':desc, 'value':measurement})
                        else:
                            abbrev = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species']['@SpeciesCode']
                            desc = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species']['@SpeciesDescription']
                            measurement = data['DailyAirQualityIndex']['LocalAuthority'][i]['Site']['Species']['@AirQualityIndex']
                            data_dict.append({'local_authority':authority, 'site_name':sitename, 'latitude':lat, 'longitude':lon, 'measurement_code':abbrev, 'measurement_descr':desc, 'value':measurement})

                else:
                    continue
        else:
            continue
 

    return data_dict

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
        df = get_air_qual_map()

        return text, summary, df
        
    else:
        return [[],[], []]
    

#Simple layout with text components and data table to display particulates
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='London Air Quality',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    html.Button('Get forecast', id='click-button', n_clicks=0, style={
            'verticalAlign': 'middle',
            'marginLeft': '45%',
            'width':'10%',
            'marginRight': '45%',
            'color': colors['text']
        }),
    dcc.Loading(
                    id="ls-loading-2",
                    children=[html.Div(id ='summary-text', style={
        'textAlign': 'center',
        'color': colors['text']
    }),
    html.Plaintext(id='body-text', style={
            'textAlign': 'center',
            'color': colors['text']
        }) 

    ,dash_table.DataTable(
        id='pollutant-table',
        style_cell={'textAlign': 'center',
            'verticalAlign': 'middle'
            }
    )],
                    type="circle",
                )
    
])
  

    
    
#Run app with built-in backend
if __name__ == '__main__':
    app.run_server(debug=True)

