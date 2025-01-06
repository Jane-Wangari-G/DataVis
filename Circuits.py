import requests
import pandas as pd
import plotly.express as px

# Fetch all circuits
def fetch_circuits():
    url = "http://ergast.com/api/f1/circuits.json?limit=1000"
    response = requests.get(url)
    data = response.json()
    circuits_data = data['MRData']['CircuitTable']['Circuits']

    circuits = []
    for c in circuits_data:
        loc = c['Location']
        circuits.append({
            'CircuitName': c['circuitName'],
            'Latitude': float(loc['lat']),
            'Longitude': float(loc['long']),
            'Locality': loc['locality'],
            'Country': loc['country']
        })
    return pd.DataFrame(circuits)

df = fetch_circuits()

# Create a scatter_geo map
fig = px.scatter_geo(
    df,
    lat='Latitude',
    lon='Longitude',
    hover_name='CircuitName',
    hover_data={'Locality': True, 'Country': True, 'Latitude': False, 'Longitude': False},
    projection="natural earth",
    title="Formula 1 Circuits Around the World"
)

fig.update_layout(
    margin={"r":0,"t":40,"l":0,"b":0},
    title_font_size=24,
    font_family="Arial",
    font_color="darkblue"
)

fig.show()
