# %% HEADER

# TODO: Add stuff to README.md

# %% IMPORTS
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import db_utils
import arrow

# %% INPUTS
years_back = 10
db_path = 'db.sqlite3'

# %% GET 
setlists = db_utils.get_raw_setlists(db_path)

# %%
df = pd.DataFrame([
    {
        'band': setlist['artist']['name'],
        'concert_date': setlist['eventDate'],
        'tour': setlist.get('tour', {}).get('name')
    }
    for setlist 
    in setlists
])
df['concert_date'] = df['concert_date'].apply(lambda x: arrow.get(x, 'DD-MM-YYYY'))

# Get the first concert date and last concert date for each band
df = df.groupby(['band', 'tour'])['concert_date'].agg(
    first_date='min',
    last_date='max'
).reset_index()
df.rename(columns={
        'first_date': 'tour_first_date', 
        'last_date': 'tour_last_date'
        }, inplace=True)
# Sort by first concert date
df = df.sort_values(['band', 'tour_first_date'])

# Calculate the time between the first concert and date of the previous tour
df['prev_tour_last_date'] = df.groupby('band')['tour_last_date'].shift()
df['time_between_tours'] = df['tour_first_date'] - df['prev_tour_last_date']

# Turn the time between tours into days
df

# %% Only keep tours that started in the last so many years
df = df[df['concert_date'] >= arrow.get(f'{arrow.now().year - years_back}-01-01')]
df

# %%
# Make concert_date a datetime using arrow and replace year with 2000
df['concert_date'] = df['concert_date'].apply(lambda x: x.datetime.replace(year=2000))
df.rename(columns={'concert_date': 'first_concert'}, inplace=True)
df

# %%
plt.figure(figsize=(10, 6))
plt.scatter(df['first_concert'], df['band'], color='black', s=100)

# Format x-axis to show only month in MMM format
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b'))

# Optional: set major ticks to monthly intervals
plt.gca().xaxis.set_major_locator(mdates.MonthLocator())

# Add labels and title
plt.xlabel('Month')
plt.ylabel('Band')
plt.title(f'First concert of a tour in the last {years_back} years')
plt.grid(True)
plt.tight_layout()
plt.show()


# %%
