from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import requests

# Fetch race results (ensure this dataset includes all drivers and required fields)
def fetch_race_results():
    data = []
    for year in range(1950, 2024):  # Include years from 1950 to 2023
        url = f"http://ergast.com/api/f1/{year}/results/1.json?limit=1000"
        response = requests.get(url)
        results = response.json()
        try:
            races = results['MRData']['RaceTable']['Races']
            for race in races:
                winner = race['Results'][0]['Driver']
                data.append({
                    'year': int(race['season']),
                    'circuitId': race['Circuit']['circuitId'],
                    'full_name': winner['givenName'] + " " + winner['familyName'],
                    'surname': winner['familyName'],
                    'name': winner['givenName'] + " " + winner['familyName'],
                    'positionOrder': 1  # Set 1 for winners
                })
        except (KeyError, IndexError):
            continue
    return pd.DataFrame(data)

# Fetch race results
heatmap_data = fetch_race_results()

# Create a list of unique drivers
all_drivers = sorted(heatmap_data['full_name'].unique())

# Initialize Dash app
app = Dash(__name__)

# Layout with a dropdown for driver selection
app.layout = html.Div([
    html.H1("F1 Driver Wins Heatmap", style={'textAlign': 'center'}),
    html.Label("Select Driver(s):"),
    dcc.Dropdown(
        id='driver-selector',
        options=[{'label': driver, 'value': driver} for driver in all_drivers],
        value=all_drivers[:5],  # Default to the first 5 drivers
        multi=True,
        clearable=True,
    ),
    dcc.Graph(id='heatmap')  # Heatmap placeholder
])

@app.callback(
    Output('heatmap', 'figure'),
    Input('driver-selector', 'value')
)
def update_driver_wins_heatmap(selected_drivers):
    # Filter dataset for selected drivers
    if not selected_drivers or len(selected_drivers) == 0:
        filtered_data = heatmap_data  # Show all drivers if none are selected
    else:
        filtered_data = heatmap_data[heatmap_data['full_name'].isin(selected_drivers)]

    if filtered_data.empty:
        return px.imshow([], title="No Data Available")

    # Create heatmap
    fig = px.density_heatmap(
        filtered_data,
        x='year',
        y='full_name',
        z='positionOrder',
        color_continuous_scale=px.colors.sequential.Plasma,
        title='Driver Wins by Year and Race',
        labels={
            'year': 'Year',
            'full_name': 'Driver',
            'positionOrder': 'Wins'
        },
        hover_data={'name': True, 'year': True, 'circuitId': True},
        template='plotly_dark'
    )

    fig.update_layout(
        coloraxis_colorbar=dict(title='Wins'),
        xaxis=dict(title='Year', tickmode='linear'),
        yaxis=dict(title='Driver', categoryorder='total ascending'),
        margin=dict(l=50, r=50, t=50, b=50)
    )

    return fig


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=9697)
