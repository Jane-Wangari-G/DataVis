import requests
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Function to fetch driver standings data from the Ergast API
def fetch_driver_standings():
    data = []
    for year in range(1950, 2024):
        url = f"http://ergast.com/api/f1/{year}/driverStandings.json?limit=1000"
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to fetch data for {year}")
            continue

        standings = response.json().get('MRData', {}).get('StandingsTable', {}).get('StandingsLists', [])
        for season in standings:
            season_year = season['season']
            for driver_standing in season['DriverStandings']:
                driver = driver_standing['Driver']
                driver_name = f"{driver['givenName']} {driver['familyName']}"
                points = float(driver_standing['points'])

                data.append({
                    'Year': int(season_year),
                    'Driver': driver_name,
                    'Points': points
                })

    return pd.DataFrame(data)

# Fetch data
standings_data = fetch_driver_standings()

# Initialize the Dash app
app = Dash(__name__)

# App Layout
app.layout = html.Div([
    html.H1("Driver Standings Progression Over the Years", style={'textAlign': 'center'}),
    dcc.Dropdown(
        id='driver-selection',
        options=[{'label': driver, 'value': driver} for driver in standings_data['Driver'].unique()],
        multi=True,
        placeholder="Select Driver(s)",
        style={'margin-bottom': '20px'}
    ),
    dcc.Graph(id='driver-standings-chart', style={'height': '700px'})
])

# Update the chart
@app.callback(
    Output('driver-standings-chart', 'figure'),
    [Input('driver-selection', 'value')]
)
def update_driver_standings_chart(selected_drivers):
    filtered_data = standings_data
    if selected_drivers:
        filtered_data = standings_data[standings_data['Driver'].isin(selected_drivers)]

    fig = px.line(
        filtered_data,
        x='Year',
        y='Points',
        color='Driver',
        title='Driver Standings Progression Over the Years',
        labels={'Year': 'Year', 'Points': 'Points', 'Driver': 'Driver'},
        template='plotly_dark'
    )

    # Customize layout
    fig.update_layout(
        xaxis=dict(title='Year', tickmode='linear', tick0=1950, dtick=5),
        yaxis=dict(title='Points'),
        legend=dict(title="Drivers", traceorder="normal"),
        height=700
    )

    # Add driver name annotations at the end of the lines for selected drivers only
    if selected_drivers:
        latest_year = standings_data['Year'].max()
        for driver in filtered_data['Driver'].unique():
            driver_data = filtered_data[filtered_data['Driver'] == driver]
            latest_data = driver_data[driver_data['Year'] == latest_year]
            if not latest_data.empty:
                latest_points = latest_data['Points'].values[0]
                fig.add_annotation(
                    x=latest_year, y=latest_points,
                    text=driver,
                    showarrow=False
                )

    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=9739)