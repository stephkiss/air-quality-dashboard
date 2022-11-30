# -*- coding: utf-8 -*-
"""
@author: stephkiss
"""
import requests
from bs4 import BeautifulSoup
import dash
from dash import  html
import re

#GET request to TfL to gather some air quality information
response=requests.get("https://api.tfl.gov.uk/AirQuality")
print("Status={}".format(response.status_code))
data=response.json()
currentForecast=data["currentForecast"][0]
text=currentForecast["forecastText"]
soup = BeautifulSoup(text)
text=soup.get_text()
text = re.sub('<br/s*?>', '\n', text)

#Initialise app
app = dash.Dash()
colors = {
    'background': '#FFFFFF',
    'text': '#000000'
}

#Create simple layout with text centered
app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='London Air Quality',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),
    html.Div(children='A web application to display London air quality forecasts.', style={
        'textAlign': 'center',
        'color': colors['text']
    }),
    html.Plaintext(text)
])
    
    
#Run app   
if __name__ == '__main__':
    app.run_server(debug=True)

