from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

def fetch_championship_data():
    titles = []
    for year in range(1950, 2024):  # Fetch data from 1950 to 2023
        url = f"http://ergast.com/api/f1/{year}/driverStandings/1.json"
        response = requests.get(url)
        data = response.json()
        try:
            winner = data['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings'][0]['Driver']
            date_of_birth = datetime.strptime(winner['dateOfBirth'], '%Y-%m-%d')
            titles.append({
                'Year': year,
                'Driver': winner['givenName'] + " " + winner['familyName'],
                'Nationality': winner['nationality'],
                'Date of Birth': date_of_birth,
                'Age': year - date_of_birth.year - ((datetime(year, 12, 31) < date_of_birth))
            })
        except (KeyError, IndexError):
            continue
    return pd.DataFrame(titles)

# Fetch and process the data
championship_data = fetch_championship_data()

# Keep only the first win for each driver
first_wins = championship_data.sort_values(by='Year').drop_duplicates(subset='Driver', keep='first')

# Sort data by age to identify youngest and oldest champions
sorted_data = first_wins.sort_values(by='Age')

# Extract youngest and oldest champions
youngest_champions = sorted_data.head(10)
oldest_champions = sorted_data.tail(10)

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Youngest and Oldest F1 Drivers' Champions", style={'textAlign': 'center'}),

    html.Div([
        html.H3("Youngest Champions"),
        dcc.Graph(id='youngest-bar-chart'),
    ]),

    html.Div([
        html.H3("Oldest Champions"),
        dcc.Graph(id='oldest-bar-chart'),
    ]),
])

@app.callback(
    [Output('youngest-bar-chart', 'figure'),
     Output('oldest-bar-chart', 'figure')],
    Input('youngest-bar-chart', 'id')  # Dummy input to trigger the callback
)
def update_charts(_):
    # Youngest Champions Bar Chart
    youngest_bar_fig = px.bar(
        youngest_champions,
        x='Age',
        y='Driver',
        orientation='h',
        color='Nationality',  # Use Nationality for color
        text='Year',
        title="Top 10 Youngest F1 Champions",
        hover_data={'Driver': True, 'Age': True, 'Year': True, 'Nationality': True}
    )
    youngest_bar_fig.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        xaxis_title="Age",
        yaxis_title="Driver"
    )

    # Oldest Champions Bar Chart
    oldest_bar_fig = px.bar(
        oldest_champions,
        x='Age',
        y='Driver',
        orientation='h',
        color='Nationality',  # Use Nationality for color
        text='Year',
        title="Top 10 Oldest F1 Champions",
        hover_data={'Driver': True, 'Age': True, 'Year': True, 'Nationality': True}
    )
    oldest_bar_fig.update_layout(
        yaxis=dict(categoryorder='total ascending'),
        xaxis_title="Age",
        yaxis_title="Driver"
    )

    return youngest_bar_fig, oldest_bar_fig


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False, port=9560)
