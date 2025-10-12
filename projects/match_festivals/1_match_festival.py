# %% HEADER
# An attempt to find festivals that have lineups that would fit a given band, based on
# the historical lineups of festivals. This assumes the user uses VS Code with the Jupyter
# extension to run the code as code cells separated by # %%

# %% IMPORTS
import json

from festival_recommender import FestivalRecommender

# %%
# Load data (put your own data there)
with open("../../data/festivals.json", encoding="utf-8") as f:
    festivals = json.load(f)

# Prep data for recommender, only keep festivals with more than one artist
festivals = {
    festival["name"]: [artist["name"] for artist in festival["artists"]]
    for festival in festivals
}

# Initialise recommender and mine rules
recommender = FestivalRecommender()
recommender.mine_rules(festivals=festivals, min_support_n=8, max_rule_length=3)

# %%
# Load previously mined rules
recommender = FestivalRecommender.load("../../data/match_festivals_rules_large.pickle")

# %%
# Recommend festivals
recommendations = recommender.recommend_festivals("Kanonenfieber")
for festival, score in recommendations[:10]:
    print(f"{festival}: score {score:.2f}")

# %%
recommender.plot_similarity_graph(
    N=50,
    min_similarity=0.1,
    title="Suspicioulsy often co-appearing artists at festivals between 2022 and 2025",
)

# %%
# Find artists that have similarity to a given artist
coappearances = recommender.find_coappearing_artists("Gutalax", min_similarity=0.01)

for artist, score in coappearances[:10]:
    print(f"{artist}: score {score:.2f}")

# %%
