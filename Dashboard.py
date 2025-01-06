import time
import requests
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ====================================
# Data Fetching Functions
# ====================================

def fetch_championships(start_year=1950, end_year=2023):
    championship_data = []
    for year in range(start_year, end_year + 1):
        url = f"http://ergast.com/api/f1/{year}/driverStandings/1.json"
        response = requests.get(url)
        time.sleep(0.5)
        data = response.json()
        try:
            standings = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]
            driver = standings['Driver']
            championship_data.append({
                'Year': year,
                'Driver': f"{driver['givenName']} {driver['familyName']}",
                'Nationality': driver['nationality']
            })
        except (IndexError, KeyError):
            continue
    return pd.DataFrame(championship_data)

def fetch_championship_data():
    titles = []
    for year in range(1950, 2024):
        url = f"http://ergast.com/api/f1/{year}/driverStandings/1.json"
        response = requests.get(url)
        data = response.json()
        try:
            winner = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]['Driver']
            date_of_birth = datetime.strptime(winner['dateOfBirth'], '%Y-%m-%d')
            # Calculate age at the end of the season
            age = year - date_of_birth.year - ((datetime(year, 12, 31) < date_of_birth))
            titles.append({
                'Year': year,
                'Driver': winner['givenName'] + " " + winner['familyName'],
                'Nationality': winner['nationality'],
                'Date of Birth': date_of_birth,
                'Age': age
            })
        except (KeyError, IndexError):
            continue
    return pd.DataFrame(titles)

def fetch_constructors_championships(start_year=1950, end_year=2024):
    constructors_data = []
    for year in range(start_year, end_year + 1):
        url = f"http://ergast.com/api/f1/{year}/constructorStandings/1.json"
        response = requests.get(url)
        time.sleep(0.5)
        data = response.json()
        try:
            standings = data['MRData']['StandingsTable']['StandingsLists'][0]
            constructor = standings['ConstructorStandings'][0]['Constructor']
            constructors_data.append({
                'Year': year,
                'Constructor': constructor['name']
            })
        except (IndexError, KeyError):
            continue
    return pd.DataFrame(constructors_data)

def fetch_grand_prix_winners(start_year=1950, end_year=2024):
    winners_data = []
    for year in range(start_year, end_year + 1):
        url = f"http://ergast.com/api/f1/{year}/results/1.json?limit=1000"
        response = requests.get(url)
        time.sleep(0.5)
        data = response.json()
        try:
            races = data['MRData']['RaceTable']['Races']
            for race in races:
                driver = race['Results'][0]['Driver']
                driver_name = f"{driver['givenName']} {driver['familyName']}"
                winners_data.append({
                    'Year': year,
                    'Race': race['raceName'],
                    'Driver': driver_name
                })
        except KeyError:
            continue
    return pd.DataFrame(winners_data)

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

def fetch_race_results():
    data = []
    for year in range(1950, 2024):
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
                    'positionOrder': 1
                })
        except (KeyError, IndexError):
            continue
    return pd.DataFrame(data)

def compute_constructors_stats(data):
    return (
        data.groupby('Constructor')
        .agg(
            Titles=('Year', 'count'),
            Years=('Year', lambda x: ', '.join(map(str, sorted(x.unique()))))
        )
        .reset_index()
    )

def compute_drivers_stats(data):
    return (
        data.groupby('Driver')
        .agg(
            Titles=('Year', 'count'),
            Years=('Year', lambda x: ', '.join(map(str, sorted(x.unique()))))
        )
        .reset_index()
    )

def fetch_driver_standings():
    data = []
    for year in range(1950, 2024):
        url = f"http://ergast.com/api/f1/{year}/driverStandings.json?limit=1000"
        response = requests.get(url)
        if response.status_code != 200:
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

def fetch_race_list(year):
    url = f"http://ergast.com/api/f1/{year}.json"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    data = response.json()
    races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
    return [{'label': race['raceName'], 'value': int(race['round'])} for race in races]

def fetch_lap_times(year, race):
    lap_times = []
    offset = 0
    limit = 100
    while True:
        url = f"http://ergast.com/api/f1/{year}/{race}/laps.json?limit={limit}&offset={offset}"
        response = requests.get(url)
        if response.status_code != 200:
            break

        data = response.json()
        races = data.get('MRData', {}).get('RaceTable', {}).get('Races', [])
        if not races:
            break

        laps = races[0].get('Laps', [])
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
                        'Time': lap_time
                    })

        total_laps = int(data['MRData']['total'])
        offset += limit
        if offset >= total_laps:
            break

    return pd.DataFrame(lap_times)

# Qualifying vs Race Results
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

def ensure_all_rounds_for_driver(data, year, driver):
    year_data = data[data['Year'] == year]
    max_round = year_data['Round'].max()
    all_rounds = list(range(1, max_round + 1))

    full_rounds = pd.DataFrame({
        'Year': year,
        'Round': all_rounds,
        'Driver': driver
    })

    driver_data = year_data[year_data['Driver'] == driver]
    return full_rounds.merge(driver_data, on=['Year', 'Round', 'Driver'], how='left')

# ====================================
# Fetch and process data
# ====================================

championship_data = fetch_championships()
constructor_data = fetch_constructors_championships()
grand_prix_winners = fetch_grand_prix_winners()
circuit_data = fetch_circuits()
driver_championship_data = fetch_championship_data()
heatmap_data = fetch_race_results()
standings_data = fetch_driver_standings()

driver_stats_by_nationality = championship_data.groupby('Nationality').agg(
    Titles=('Year', 'count'),
    Drivers=('Driver', 'nunique')
).reset_index()

constructors_stats = compute_constructors_stats(constructor_data)
drivers_stats = compute_drivers_stats(championship_data)

# Youngest and Oldest F1 Champions
first_wins = driver_championship_data.sort_values(by='Year').drop_duplicates(subset='Driver', keep='first')
sorted_data = first_wins.sort_values(by='Age')
youngest_champions = sorted_data.head(10)
oldest_champions = sorted_data.tail(10)

# Unique drivers for heatmap
all_drivers = sorted(heatmap_data['full_name'].unique())

# Qualifying vs Race Data
qualifying_race_data = fetch_qualifying_and_race_results(1950, 2024)
qual_default_year = qualifying_race_data['Year'].max()

# ====================================
# Initialize Dash app with a dark Bootstrap theme
# ====================================
app = Dash(__name__, external_stylesheets=[dbc.themes.CYBORG])

# ====================================
# Layout
# ====================================
app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        dbc.Col(html.H1("F1 Dashboard", className="text-center my-4"), width=12)
    ]),

    # World Drivers Championship
    dbc.Row([
        dbc.Col([
            html.H2("World Drivers Championship", className="my-4"),
            dcc.Graph(
                id='championship-bar-chart',
                # Add template='plotly_dark' to the figure
                figure=px.bar(
                    drivers_stats.sort_values(by='Titles', ascending=False),
                    x='Driver',
                    y='Titles',
                    text='Titles',
                    title='World Drivers Championships (1950-2024)',
                    labels={'Titles': 'Number of Titles', 'Driver': 'Driver'},
                    color='Titles',
                    hover_data={'Years': True},
                    color_continuous_scale='Viridis',
                    category_orders={'Driver': drivers_stats.sort_values(by='Titles', ascending=False)['Driver']},
                    template='plotly_dark'
                ).update_layout(xaxis_tickangle=-45, margin={'l': 50, 'r': 50, 't': 50, 'b': 150})
            )
        ], width=12),
    ], className="my-4"),

    # Driver Championships by Nationality
# Driver Championships by Nationality
dbc.Row([
    dbc.Col([
        html.H2("Driver Championships by Nationality", className="my-3"),  # Reduced from my-4 to my-3
        dcc.Dropdown(
            id='nationality-chart-type',
            options=[
                {'label': 'Sunburst Chart', 'value': 'sunburst'},
                {'label': 'Treemap', 'value': 'treemap'}
            ],
            value='sunburst',
            clearable=False,
            style={'width': '50%', 'margin': '0 auto', 'color': '#000'}
        ),
        dcc.Graph(
            id='nationality-chart',
            style={'height': '600px', 'width': '85%', 'margin': 'auto'}
        )
    ], width=12),
], className="my-3"),  # Reduced outer row spacing from my-4 to my-3


    # Circuits
    dbc.Row([
        dbc.Col([
            html.H2("F1 Circuits Around the World", className="my-4"),
            dcc.Graph(
                id='circuits-map',
                figure=px.scatter_geo(
                    circuit_data,
                    lat='Latitude',
                    lon='Longitude',
                    hover_name='CircuitName',
                    hover_data={'Locality': True, 'Country': True},
                    projection="natural earth",
                    title="Formula 1 Circuits Around the World",
                    template='plotly_dark'
                ).update_layout(margin={"r":0,"t":40,"l":0,"b":0})
            )
        ], width=12),
    ], className="my-4"),

    # Grand Prix Winners
    dbc.Row([
        dbc.Col([
            html.H2("F1 Grand Prix Winners", className="my-4"),
            dcc.Graph(
                id='grand-prix-winners',
                figure=px.scatter(
                    grand_prix_winners,
                    x='Year',
                    y='Race',
                    color='Driver',
                    hover_data={'Driver': True, 'Year': True, 'Race': True},
                    title='Formula 1 Grand Prix Winners (1950-2024)',
                    labels={'Race': 'Grand Prix', 'Driver': 'Winner'},
                    template='plotly_dark'
                ).update_layout(
                    height=1200,
                    yaxis=dict(
                        title='Grand Prix',
                        tickmode='linear',
                        tickfont=dict(size=8),
                        automargin=True
                    ),
                    xaxis=dict(title='Year'),
                    margin={'l': 150, 'r': 50, 't': 50, 'b': 50}
                )
            )
        ], width=12),
    ], className="my-4"),

    # Constructors Championships
    dbc.Row([
        dbc.Col([
            html.H2("World Constructors Championships", className="my-4"),
            dcc.Graph(
                id='constructors-championships',
                figure=px.bar(
                    constructors_stats.sort_values(by='Titles', ascending=False),
                    x='Constructor',
                    y='Titles',
                    text='Titles',
                    title='World Constructors Championships (1950-2024)',
                    labels={'Titles': 'Number of Titles', 'Constructor': 'Constructor'},
                    hover_data={'Years': True},
                    color='Titles',
                    color_continuous_scale='Cividis',
                    category_orders={'Constructor': constructors_stats.sort_values(by='Titles', ascending=False)['Constructor']},
                    template='plotly_dark'
                ).update_layout(xaxis_tickangle=-45, margin={'l': 50, 'r': 50, 't': 50, 'b': 150})
            )
        ], width=12),
    ], className="my-4"),

    # Youngest and Oldest Champions
    dbc.Row([
        dbc.Col([
            html.H2("Youngest and Oldest F1 Drivers' Champions", className="my-4"),
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.H3( className="my-2"),
            dcc.Graph(id='youngest-bar-chart')
        ], md=6),
        dbc.Col([
            html.H3( className="my-2"),
            dcc.Graph(id='oldest-bar-chart')
        ], md=6),
    ], className="my-4"),

    # Heatmap Section
    dbc.Row([
        dbc.Col([
            html.H2("F1 Driver Wins Heatmap", className="my-4"),
            html.Label("Select Driver(s):"),
            dcc.Dropdown(
                id='driver-selector',
                options=[{'label': driver, 'value': driver} for driver in all_drivers],
                value=all_drivers[:5],
                multi=True,
                clearable=True,
                style={'width':'100%', 'color':'#000'}
            ),
            dcc.Graph(id='heatmap')
        ], width=12),
    ], className="my-4"),

    # Driver Standings Progression
    dbc.Row([
        dbc.Col([
            html.H2("Driver Standings Progression Over the Years", className="text-center my-4"),
            dcc.Dropdown(
                id='driver-selection',
                options=[{'label': driver, 'value': driver} for driver in standings_data['Driver'].unique()],
                multi=True,
                placeholder="Select Driver(s)",
                style={'margin-bottom': '20px', 'width': '100%', 'margin': '0 auto', 'color':'#000'}
            ),
            dcc.Graph(id='driver-standings-chart', style={'height': '700px'})
        ], width=12),
    ], className="my-4"),

    # F1 Lap Time Analysis
    dbc.Row([
        dbc.Col([
            html.H2("F1 Lap Time Analysis", className="text-center my-4"),
            dbc.Row([
                dbc.Col([
                    html.Label("Select Year:"),
                    dcc.Dropdown(
                        id='year-dropdown-lap',
                        options=[{'label': year, 'value': year} for year in range(1950, 2024)],
                        value=2023,
                        clearable=False,
                        style={'width': '100%', 'color':'#000'}
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Select Race:"),
                    dcc.Dropdown(
                        id='race-dropdown',
                        options=[],
                        value=None,
                        clearable=False,
                        style={'width': '100%', 'color':'#000'}
                    ),
                ], md=3)
            ], className="my-2"),
            html.Div(id='fastest-lap-summary', style={'margin': '20px', 'fontSize': '16px'}),
            dcc.Graph(id='lap-times-chart', style={'height': '600px'})
        ], width=12),
    ], className="my-4"),

    # Qualifying vs Race Performance
    dbc.Row([
        dbc.Col([
            html.H2("Qualifying vs Race Performance", className="text-center my-4"),
            dbc.Row([
                dbc.Col([
                    html.Label("Select Year:"),
                    dcc.Dropdown(
                        id='qual-year-dropdown',
                        options=[{'label': str(y), 'value': y} for y in sorted(qualifying_race_data['Year'].unique())],
                        value=qual_default_year,
                        clearable=True,
                        placeholder="Select a year",
                        style={'width': '100%', 'color':'#000'}
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Select Driver(s):"),
                    dcc.Dropdown(
                        id='qual-driver-dropdown',
                        multi=True,
                        placeholder="Select one or more drivers",
                        style={'width': '100%', 'color':'#000'}
                    ),
                ], md=6),
            ], className="my-2"),
            dcc.Graph(id='qualifying-vs-race-chart', style={'height': '600px'})
        ], width=12)
    ], className="my-4")
])

# ====================================
# Callbacks
# ====================================

@app.callback(
    Output('nationality-chart', 'figure'),
    Input('nationality-chart-type', 'value')
)
def update_nationality_chart(chart_type):
    if chart_type == 'sunburst':
        fig = px.sunburst(
            championship_data,
            path=['Nationality', 'Driver', 'Year'],
            title="Driver Championships by Nationality",
            hover_data={'Year': True},
            template='plotly_dark'
        )
    else:
        fig = px.treemap(
            championship_data,
            path=['Nationality', 'Driver', 'Year'],
            title="Driver Championships by Nationality",
            hover_data={'Year': True},
            template='plotly_dark'
        )
    return fig

@app.callback(
    [Output('youngest-bar-chart', 'figure'),
     Output('oldest-bar-chart', 'figure')],
    Input('youngest-bar-chart', 'id')
)
def update_charts(_):
    youngest_bar_fig = px.bar(
        youngest_champions,
        x='Age',
        y='Driver',
        orientation='h',
        color='Nationality',
        text='Year',
        title="Top 10 Youngest F1 Champions",
        hover_data={'Driver': True, 'Age': True, 'Year': True, 'Nationality': True},
        template='plotly_dark'
    )
    youngest_bar_fig.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        xaxis_title="Age",
        yaxis_title="Driver"
    )

    oldest_bar_fig = px.bar(
        oldest_champions,
        x='Age',
        y='Driver',
        orientation='h',
        color='Nationality',
        text='Year',
        title="Top 10 Oldest F1 Champions",
        hover_data={'Driver': True, 'Age': True, 'Year': True, 'Nationality': True},
        template='plotly_dark'
    )
    oldest_bar_fig.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        xaxis_title="Age",
        yaxis_title="Driver"
    )

    return youngest_bar_fig, oldest_bar_fig

@app.callback(
    Output('heatmap', 'figure'),
    Input('driver-selector', 'value')
)
def update_driver_wins_heatmap(selected_drivers):
    if not selected_drivers or len(selected_drivers) == 0:
        filtered_data = heatmap_data
    else:
        filtered_data = heatmap_data[heatmap_data['full_name'].isin(selected_drivers)]

    if filtered_data.empty:
        return px.imshow([], title="No Data Available", template='plotly_dark')

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

    fig.update_layout(
        xaxis=dict(title='Year', tickmode='linear', tick0=1950, dtick=5),
        yaxis=dict(title='Points'),
        legend=dict(title="Drivers", traceorder="normal"),
        height=700
    )

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

@app.callback(
    [Output('race-dropdown', 'options'),
     Output('race-dropdown', 'value')],
    Input('year-dropdown-lap', 'value')
)
def update_race_dropdown(selected_year):
    race_options = fetch_race_list(selected_year)
    return race_options, (race_options[0]['value'] if race_options else None)

@app.callback(
    [Output('lap-times-chart', 'figure'),
     Output('fastest-lap-summary', 'children')],
    [Input('year-dropdown-lap', 'value'),
     Input('race-dropdown', 'value')]
)
def update_lap_times_chart(selected_year, selected_race):
    if not selected_race:
        return go.Figure(), "<b>No race selected.</b>"

    lap_times = fetch_lap_times(selected_year, selected_race)
    if lap_times.empty:
        return go.Figure(), "<b>No lap data available for the selected race.</b>"

    max_lap = lap_times['Lap'].max()

    fastest_lap = lap_times.loc[lap_times['Milliseconds'].idxmin()]
    fastest_lap_summary = (
        f"Fastest Lap: Driver: {fastest_lap['Driver']}, "
        f"Lap: {fastest_lap['Lap']}, Time: {fastest_lap['Time']}"
    )

    fig = px.line(
        lap_times,
        x='Lap',
        y='Milliseconds',
        color='Driver',
        title=f"Lap Time Analysis for Race {selected_race} ({selected_year})",
        labels={'Lap': 'Lap', 'Milliseconds': 'Time (ms)', 'Driver': 'Driver'},
        template='plotly_dark'
    )

    fig.update_layout(
        xaxis=dict(title='Lap', tickmode='linear', range=[1, max_lap + 1]),
        yaxis=dict(title='Time (ms)'),
        legend=dict(title="Drivers", traceorder="normal"),
        height=600
    )

    return fig, fastest_lap_summary

@app.callback(
    Output('qual-driver-dropdown', 'options'),
    Output('qual-driver-dropdown', 'value'),
    Input('qual-year-dropdown', 'value')
)
def update_qual_driver_dropdown(selected_year):
    year = selected_year or qual_default_year
    year_data = qualifying_race_data[qualifying_race_data['Year'] == year]
    drivers = sorted(year_data['Driver'].unique())

    driver_options = [{'label': driver, 'value': driver} for driver in drivers]
    return driver_options, []

@app.callback(
    Output('qualifying-vs-race-chart', 'figure'),
    Input('qual-year-dropdown', 'value'),
    Input('qual-driver-dropdown', 'value')
)
def update_qualifying_vs_race(selected_year, selected_drivers):
    year = selected_year or qual_default_year
    year_data = qualifying_race_data[qualifying_race_data['Year'] == year]

    if not selected_drivers:
        selected_drivers = year_data['Driver'].unique()

    combined_data = pd.DataFrame()
    for driver in selected_drivers:
        driver_data = ensure_all_rounds_for_driver(year_data, year, driver)
        combined_data = pd.concat([combined_data, driver_data])

    if combined_data.empty:
        return px.scatter(title="No data available for the selected filters.", template='plotly_dark')

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
        height=600,
        template='plotly_dark'
    )

    fig.update_layout(
        xaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 20.5]),
        yaxis=dict(tickmode='linear', tick0=1, dtick=1, range=[0.5, 20.5]),
        legend=dict(title="Driver")
    )

    return fig

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=9923)
