import requests
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

# Function to fetch lap times from the Ergast API with pagination
def fetch_lap_times(year, race):
    lap_times = []
    offset = 0
    limit = 100

    while True:
        # Fetch laps with pagination
        url = f"http://ergast.com/api/f1/{year}/{race}/laps.json?limit={limit}&offset={offset}"
        print(f"Fetching data from URL: {url}")
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Error: Unable to fetch data for {year}, Race {race}. Status Code: {response.status_code}")
            break

        data = response.json()
        races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
        if not races:
            print(f"No data found for {year}, Race {race}")
            break

        laps = races[0].get('Laps', [])
        print(f"Offset: {offset}, Laps in this page: {len(laps)}")
        if laps:
            for lap in laps:
                lap_number = int(lap['number'])
                for timing in lap.get('Timings', []):
                    driver_id = timing['driverId']
                    lap_time = timing['time']
                    minutes, seconds = map(float, lap_time.split(":"))
                    total_milliseconds = int((minutes * 60 + seconds) * 1000)

                    lap_times.append({
                        'Driver': driver_id,
                        'Lap': lap_number,
                        'Milliseconds': total_milliseconds,
                        'Time': lap_time  # Keep the formatted time for display
                    })

        # Check if we have fetched all laps
        total_laps = int(data['MRData']['total'])
        offset += limit
        if offset >= total_laps:
            break

    print(f"Total laps fetched for {year}, Race {race}: {len(lap_times)}")
    return pd.DataFrame(lap_times)

# Function to fetch the list of races for a given year
def fetch_race_list(year):
    url = f"http://ergast.com/api/f1/{year}.json"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    data = response.json()
    races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
    return [{'label': race['raceName'], 'value': int(race['round'])} for race in races]

# Initialize the Dash app
app = Dash(__name__)

# App Layout
app.layout = html.Div([
    html.H1("F1 Lap Time Analysis", style={'textAlign': 'center'}),
    html.Label("Select Year:"),
    dcc.Dropdown(
        id='year-dropdown',
        options=[{'label': year, 'value': year} for year in range(1950, 2024)],
        value=2023,
        clearable=False
    ),
    html.Label("Select Race:"),
    dcc.Dropdown(
        id='race-dropdown',
        options=[],
        value=None,
        clearable=False
    ),
    html.Div(id='fastest-lap-summary', style={'margin': '20px', 'fontSize': '16px'}),
    dcc.Graph(id='lap-times-chart', style={'height': '600px'})
])

# Update race dropdown based on selected year
@app.callback(
    Output('race-dropdown', 'options'),
    Output('race-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_race_dropdown(selected_year):
    race_options = fetch_race_list(selected_year)
    return race_options, race_options[0]['value'] if race_options else None

# Update lap times chart and fastest lap summary based on year and race
@app.callback(
    [Output('lap-times-chart', 'figure'),
     Output('fastest-lap-summary', 'children')],
    [Input('year-dropdown', 'value'),
     Input('race-dropdown', 'value')]
)
def update_lap_times_chart(selected_year, selected_race):
    if not selected_race:
        return go.Figure(), "<b>No race selected.</b>"

    lap_times = fetch_lap_times(selected_year, selected_race)
    if lap_times.empty:
        return go.Figure(), "<b>No lap data available for the selected race.</b>"

    # Ensure the x-axis covers all laps dynamically
    max_lap = lap_times['Lap'].max()

    # Find the fastest lap
    fastest_lap = lap_times.loc[lap_times['Milliseconds'].idxmin()]
    fastest_lap_summary = (
        f"Fastest Lap: Driver: {fastest_lap['Driver']}, "
        f"Lap: {fastest_lap['Lap']}, Time: {fastest_lap['Time']}"
    )

    # Create line chart
    fig = px.line(
        lap_times,
        x='Lap',
        y='Milliseconds',
        color='Driver',
        title=f"Lap Time Analysis for Race {selected_race} ({selected_year})",
        labels={'Lap': 'Lap', 'Milliseconds': 'Time (ms)', 'Driver': 'Driver'},
        template='plotly_dark'
    )

    # Adjust layout for interactivity and correct lap scaling
    fig.update_layout(
        xaxis=dict(title='Lap', tickmode='linear', range=[1, max_lap + 1]),
        yaxis=dict(title='Time (ms)'),
        legend=dict(title="Drivers", traceorder="normal"),
        height=600
    )

    return fig, fastest_lap_summary


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=9472)