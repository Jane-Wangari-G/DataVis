import time
import requests
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# Fetch qualifying and race data for all years
def fetch_qualifying_and_race_results(start_year=1950, end_year=2024):
    data = []
    for year in range(start_year, end_year + 1):
        url = f"http://ergast.com/api/f1/{year}/results.json?limit=1000"
        response = requests.get(url)
        time.sleep(0.5)  # Avoid API rate limits
        year_data = response.json()

        try:
            races = year_data['MRData']['RaceTable']['Races']
            for race in races:
                race_name = race['raceName']
                round_number = int(race['round'])
                for result in race['Results']:
                    driver = result['Driver']
                    driver_name = f"{driver['givenName']} {driver['familyName']}"
                    qualifying_position = int(result['grid'])
                    race_position = int(result['position'])

                    data.append({
                        'Year': int(year),
                        'Round': round_number,
                        'Race': race_name,
                        'Driver': driver_name,
                        'Qualifying Position': qualifying_position,
                        'Race Position': race_position
                    })
        except KeyError:
            continue

    return pd.DataFrame(data)

# Fetch the full dataset (1950–2024)
qualifying_race_data = fetch_qualifying_and_race_results(1950, 2024)
default_year = qualifying_race_data['Year'].max()

# Ensure all rounds for a driver in a specific year are included
def ensure_all_rounds_for_driver(data, year, driver):
    """
    Ensures all rounds (1–max_round) for the selected driver in the selected year are included.
    Missing rounds will have NaN for qualifying and race positions.
    """
    # Get all rounds for the selected year
    year_data = data[data['Year'] == year]
    max_round = year_data['Round'].max()
    all_rounds = list(range(1, max_round + 1))

    # Create a DataFrame with all rounds for the selected driver
    full_rounds = pd.DataFrame({
        'Year': year,
        'Round': all_rounds,
        'Driver': driver
    })

    # Merge with existing data
    driver_data = year_data[year_data['Driver'] == driver]
    return full_rounds.merge(driver_data, on=['Year', 'Round', 'Driver'], how='left')

# Initialize Dash app
app = Dash(__name__)

app.layout = html.Div([
    html.H1("Qualifying vs Race Performance", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Select Year:"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(year), 'value': year} for year in qualifying_race_data['Year'].unique()],
            value=default_year,
            clearable=True,
            placeholder="Select a year"
        ),
    ], style={'width': '20%', 'display': 'inline-block', 'marginRight': '20px'}),

    html.Div([
        html.Label("Select Driver(s):"),
        dcc.Dropdown(
            id='driver-dropdown',
            multi=True,
            placeholder="Select one or more drivers"
        ),
    ], style={'width': '40%', 'display': 'inline-block'}),

    dcc.Graph(id='qualifying-vs-race-chart', style={'height': '600px'})
])

@app.callback(
    Output('driver-dropdown', 'options'),
    Output('driver-dropdown', 'value'),
    Input('year-dropdown', 'value')
)
def update_driver_dropdown(selected_year):
    year = selected_year or default_year
    year_data = qualifying_race_data[qualifying_race_data['Year'] == year]
    drivers = sorted(year_data['Driver'].unique())

    driver_options = [{'label': driver, 'value': driver} for driver in drivers]
    return driver_options, []

@app.callback(
    Output('qualifying-vs-race-chart', 'figure'),
    Input('year-dropdown', 'value'),
    Input('driver-dropdown', 'value')
)
def update_qualifying_vs_race(selected_year, selected_drivers):
    year = selected_year or default_year
    year_data = qualifying_race_data[qualifying_race_data['Year'] == year]

    # If no drivers selected, display data for all drivers
    if not selected_drivers:
        selected_drivers = year_data['Driver'].unique()

    # Prepare combined data for all selected drivers
    combined_data = pd.DataFrame()
    for driver in selected_drivers:
        driver_data = ensure_all_rounds_for_driver(year_data, year, driver)
        combined_data = pd.concat([combined_data, driver_data])

    # If no data is found, return an empty figure
    if combined_data.empty:
        return px.scatter(title="No data available for the selected filters.")

    # Create scatter plot
    fig = px.scatter(
        combined_data,
        x='Qualifying Position',
        y='Race Position',
        color='Driver',
        hover_data=['Round', 'Race'],
        title=f'Qualifying Position vs Race Performance ({year})',
        labels={
            'Qualifying Position': 'Qualifying Position (Starting Grid)',
            'Race Position': 'Race Position (Finish)'
        },
        height=600
    )

    # Update axes for better display
    fig.update_layout(
        xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 20.5]),
        yaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 20.5]),
        legend=dict(title="Driver")
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=8720)
