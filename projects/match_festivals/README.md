## Match festivals

This project compares the historical lineups of festivals to find which festivals are a good match for a given band, based on the historical lineups of festivals.

The data is retrieved from [concerts-metal.com](https://en.concerts-metal.com/festivals.html). As the scraping process is relatively slow, the scraped data is saved to a JSON file in [0_get_data.py](0_get_data.py) and used in the scripts [1_match_festival.py](1_match_festival.py) and [1_visualise_twins.py](1_visualise_twins.py).

### [1_visualise_twins.py](1_visualise_twins.py)

This script visualises the 'twinning' of bands at festivals, as in artists that appear at the same festival as another artist several times. Outputs are visualisations as shown in the [match festivals](../../README.md#match_festivals) section of the main README.

### [1_match_festival.py](1_match_festival.py)

This scripts drives the matching process, which is based on the [fpgrowth](https://mlxtend.readthedocs.io/en/stable/generated/mlxtend.frequent_patterns.fpgrowth.html) and [association_rules](https://mlxtend.readthedocs.io/en/stable/generated/mlxtend.frequent_patterns.association_rules.html) functions from [mlxtend](https://mlxtend.readthedocs.io/en/stable/). The logic is wrapped into the `FestivalRecommender` class, available in [festival_recommender.py](festival_recommender.py). Check out the [1_match_festival.py](1_match_festival.py) for some example coding or read below.

The `FestivalRecommender` class contains some methods that make the mining process easier and offers some functions that can then be used to explore the rules and recommend fitting festivals and similar artists.

The main input is a dictionary with festival names as keys and lists of artists as values:

```text
festivals = {
    'Summer Breeze 2022': ['Blind Guardian', 'Eisbrecher', 'Within Temptation', '1914', ...]
    'Wacken Open Air 2024': ['Amon Amarth', 'Korn', 'Scorpions', 'Accept', 'Alcatrazz', ...]
    'Into The Grave 2025': ['Powerwolf', 'Savatage', 'W.A.S.P.', '3 Inches Of Blood', ...]
    ...
    }
```

Initialise the recommender and mine rules with the dict of festivals as input, with some optional parameters:

```python
# Initialise recommender and mine rules
recommender = FestivalRecommender()
recommender.mine_rules(
    festivals=festivals, 
    min_support_n=8, 
    max_rule_length=3
    )
```

Note that the `min_support_n` parameter is used to calculate the minimum number of lineups an artist needs to share to be considered for a rule, rather than defining a min_support value as a fraction.

Depending on the size of the data this may take a while to run.

Use the `save` and `load` functions to save and load the mined rules to and from a file and skip the mining process.

```python
# Save rules
recommender.save('rules.pickle')

# Load previously mined rules
recommender.load('rules.pickle')
```

---

The main intended use is to recommend festivals for a given band, based on the historical lineups of festivals. The `recommend_festivals` function takes an artist name as input and returns a list of tuples with the festival name and score.

```python
# Find recommendations
recommendations = recommender.recommend_festivals("Kanonenfieber")

for festival, score in recommendations[:10]:
    print(f"{festival}: score {score:.2f}")
```

```text
Graspop Metal Meeting: score 4.50
Brutal Assault: score 4.50
South of Heaven Open Air: score 4.00
Wacken Open Air: score 3.60
Metaldays: score 3.50
Alcatraz Metal Festival: score 3.50
Hellfest: score 3.00
Gefle Metal Festival: score 3.00
Tolminator: score 3.00
Bloodstock Open Air: score 2.50
```

These represent festivals Kanonenfieber has not yet played at, but artists that have played on the same festival as Kanonenfieber have. A higher score means more co-appearing artists at other festivals have appeared at the same festival, so Kanonenfieber would be a good fit for the festival, based on that fact. Note that this only includes data from 2022 to 2025, so the artist might have performed at the suggested festival before that.

`recommend_festivals` takes several optional parameters. The `min_lift` parameter is used to filter out rules that do not have a lift score above a certain threshold and make the matching process more strict. The `exclude_played` parameter by default ignores festivals that the artist has already played at, regardless of the year of that festival. Setting `exclude_played=False` will include these festivals and might not give useful information. The `return_raw` parameter returns the raw calculation results per festivaland does no aggregations, which might be useful if you want to play around with the results.

---

The `plot_similarity_graph` function exploits the fact that the association rules are statistically significant and makes it possible to find artists that are statistically related, through festivals they have played at together.

```python
# Plot similarity graph
recommender.plot_similarity_graph(
    top_n=50, 
    )
```

![Suspiciously often co-appearing artists at festivals between 2022 and 2025](../../assets/images/Coappearing_artists_Jaccard.png)

This function plots the links between all artists and the `top_n` most performing artists at festivals and others. By default isolated nodes are removed and only edges with a `min_similarity` of 0.1 are plotted.

The core of the network is composed of artists that appear at many festivals, with other artists that had a shorter festival season towards the outside of the network. Artists that had relatively only few appearances are not plotted, as they have no statistically significant enough relationship.

---

The `find_coappearing_artists` function finds artists that appear at the same festivals as a given artist.

```python
# Find coappearances
coappearances = recommender.find_coappearing_artists("Gutalax", min_similarity=0.01)

for artist, score in coappearances[:10]:
    print(f"{artist}: score {score:.2f}")
```

```text
Suffocation: score 0.13
Gaerea: score 0.09
Angelus Apatrida: score 0.07
Leprous: score 0.07
Tankard: score 0.07
Dark Funeral: score 0.07
Asphyx: score 0.07
Zeal & Ardor: score 0.07
Blind Guardian: score 0.06
Destruction: score 0.06
```

The displayed scores are the Jaccard similarity score between the top artists and the given artist, based on the festivals they played at together.
