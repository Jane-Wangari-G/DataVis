from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import requests


def fetch_championship_data():
    titles = []
    for year in range(1950, 2024):  # Fetch data from 1950 to 2023
        url = f"http://ergast.com/api/f1/{year}/driverStandings/1.json"
        response = requests.get(url)
        data = response.json()
        try:
            winner = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]['Driver']
            titles.append({
                'Year': year,
                'Driver': winner['givenName'] + " " + winner['familyName'],
                'Nationality': winner['nationality'],
                'Country': winner.get('permanentNumber', "Unknown")  # Optional
            })
        except (KeyError, IndexError):
            continue
    return pd.DataFrame(titles)


def prepare_data(df):
    # Aggregate data for visualization
    country_data = df.groupby('Nationality').agg(
        Titles=('Year', 'count'),
        Drivers=('Driver', 'nunique'),
        Years=('Year', lambda x: ', '.join(map(str, x))),
        DriversList=('Driver', lambda x: ', '.join(x.unique()))
    ).reset_index()
    return country_data


# Fetch and prepare the data
championship_data = fetch_championship_data()
country_data = prepare_data(championship_data)

app = Dash(__name__)

app.layout = html.Div([
    html.H1("F1 Drivers' Championships by Nationality", style={'textAlign': 'center'}),

    dcc.Graph(id='sunburst-chart'),

    html.Div([
        html.Label("Select Visualization Type:"),
        dcc.Dropdown(
            id='chart-type',
            options=[
                {'label': 'Sunburst Chart', 'value': 'sunburst'},
                {'label': 'Treemap', 'value': 'treemap'}
            ],
            value='sunburst',
            clearable=False
        )
    ], style={'width': '50%', 'margin': 'auto'}),
])


@app.callback(
    Output('sunburst-chart', 'figure'),
    Input('chart-type', 'value')
)
def update_chart(chart_type):
    if chart_type == 'sunburst':
        fig = px.sunburst(
            championship_data,
            path=['Nationality', 'Driver', 'Year'],
            values='Year',
            color='Nationality',
            hover_data={'Year': True},
            title="F1 Drivers' Championships by Nationality"
        )
    else:
        fig = px.treemap(
            championship_data,
            path=['Nationality', 'Driver', 'Year'],
            values='Year',
            color='Nationality',
            hover_data={'Year': True},
            title="F1 Drivers' Championships by Nationality"
        )

    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return fig


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=9354)