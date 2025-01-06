import requests
import pandas as pd
import plotly.express as px
import time

# Fetch data for all races and their winners
def fetch_race_winners():
    races = []
    for year in range(1950, 2024):
        url = f'http://ergast.com/api/f1/{year}/results.json?limit=1000'
        response = requests.get(url)
        time.sleep(1)  # Delay to avoid hitting API rate limits
        data = response.json()
        try:
            race_data = data['MRData']['RaceTable']['Races']
            for race in race_data:
                race_name = race['raceName']
                circuit_name = race['Circuit']['circuitName']
                round_number = race['round']
                winner_data = race['Results'][0]['Driver']
                winner_name = f"{winner_data['givenName']} {winner_data['familyName']}"
                races.append({
                    'Year': year,
                    'Race': race_name,
                    'Circuit': circuit_name,
                    'Round': int(round_number),
                    'Winner': winner_name
                })
        except (IndexError, KeyError):
            print(f"No race data available for the year {year}")
    return pd.DataFrame(races)

# Fetch and prepare the data
df = fetch_race_winners()

# Check if the dataframe is empty
if df.empty:
    print("No data available for visualization.")
    exit()

# Interactive plot using Plotly with range slider
def create_visualization(df):
    fig = px.scatter(
        df,
        x='Year',
        y='Race',
        color='Winner',
        hover_data=['Winner', 'Year', 'Race'],
        title='Formula 1 Grand Prix Winners (1950-2023)',
        labels={
            'Year': 'Year',
            'Race': 'Grand Prix',
            'Winner': 'Driver'
        }
    )

    fig.update_layout(
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=10, label="Last 10 years", step="year", stepmode="backward"),
                    dict(count=20, label="Last 20 years", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            rangeslider=dict(visible=True),
            type="linear"
        ),
        yaxis_title="Grand Prix",
        title_font_size=24,
        font_family="Arial",
        font_color="darkblue",
        title_x=0.5,
        plot_bgcolor="#f4f4f4",
        paper_bgcolor="#ffffff"
    )

    fig.update_traces(marker=dict(size=10, line=dict(width=2, color='DarkSlateGrey')))

    fig.show()

# Call the visualization function
create_visualization(df)
