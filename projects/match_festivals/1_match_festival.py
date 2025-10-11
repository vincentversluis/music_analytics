# %% HEADER
# An attempt to find festivals that have lineups that would fit a given band, based on
# the historical lineups of festivals
# TODO: Write a class with a mine function
# TODO: Docstrings and _type_ and _description_
# TODO: Play with Jaccard index
# TODO: Log instead of print
# TODO: README in this project with some more demonstrations
# TODO: Repo readme

"""Counter({
2: 91842,
3: 26249,
4: 9904,
5: 4262,
6: 2074,
7: 1037,
8: 558,
9: 289,
10: 180,
11: 109,
12: 61,
13: 44,
14: 20,
15: 9,
17: 8,
16: 5,
19: 4,
20: 3,
21: 2,
23: 1,
22: 1}).
"""

# %% IMPORTS
from collections import defaultdict
from itertools import chain
import json
from math import ceil
import pickle
from pprint import pprint
import re

from loguru import logger
import matplotlib.pyplot as plt
from mlxtend.frequent_patterns import association_rules, fpgrowth
from mlxtend.preprocessing import TransactionEncoder
import networkx as nx
import pandas as pd
from sklearn.metrics import jaccard_score

# %% INPUTS
scr_path = "../../data/festivals.json"
save_path = "../../data/match_festivals_rules.pickle"

artist_of_interest = "Hiraes"

# Deep mining
max_rule_length = 5  # max([len(lineup) for lineup in lineups])
min_support_n = 4  # Define support as number of shared lineups rather than a fraction

# Shallow mining
max_rule_length = 3  # max([len(lineup) for lineup in lineups])
min_support_n = 8  

# %% CLASS
class FestivalRecommender:
    def __init__(self):
        self.festivals: dict = {}
        self.festival_names: list = []
        self.frequent_itemsets: pd.DataFrame = pd.DataFrame()
        self.rules: pd.DataFrame = pd.DataFrame()
        self.mining_settings: dict = {}
    
    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"Saved recommender to {path}")
        
    @classmethod
    def load(cls, path: str, verbose: bool = False):
        with open(path, "rb") as f:
            obj = pickle.load(f)

        logger.info(f"Loaded recommender from {path}")

        if verbose:
            print("Loading summary:")
            obj.summary()

        return obj

    def summary(self):
        pprint({
            "festivals": len(self.festivals),
            "rules": len(self.rules),
            "settings": self.mining_settings
        })
        print()
    
    def mine_rules(self, festivals: dict, min_support_n: int = 4, max_rule_length: int = 5) -> None:
        # ! This takes a while if the data results in a large and very sparse set
        # Only keep festivals with more than one artist, then make it into a dict
        festivals = [festival for festival in festivals if len(festival["artists"]) > 1]
        self.festivals = {festival['name']: [artist['name'] for artist in festival['artists']] for festival in festivals}

        # Get lineup, festival names and artists
        self.festival_names = list(self.festivals.keys())
        lineups = self.festivals.values()
        artists = set(chain.from_iterable(lineups))
        logger.info(f"Found {len(lineups):,} lineups containing {len(artists):,} artists")

        # Encode all lineups into a binary matrix
        logger.info("Construct sparse dataframe from lineups")
        te = TransactionEncoder()
        te_array = te.fit(lineups).transform(lineups)
        df = pd.DataFrame(te_array, columns=te.columns_)

        # Remove artists that will not be in any rules as they are not in enough lineups
        # Calculate min support from minimum number of lineups artists need to shares
        min_support = min_support_n / len(df)

        # Calculate number of lineups artists need to share from min_support
        min_lineups = ceil(min_support * len(lineups))
        logger.info(f"Look for paired artists in at least {min_lineups} lineups")

        artist_counts = df.sum(axis=0)
        df = df.loc[:, artist_counts >= min_lineups]
        logger.info(f"Found {df.shape[0]:,} lineups with {df.shape[1]:,} artists left after cleaning")

        # Convert to sparse to be kinder on memory
        df = df.astype(pd.SparseDtype("bool", fill_value=False))

        self.mining_settings = {
            "min_support": min_support,
            "min_support_n": min_support_n,
            "max_rule_length": max_rule_length
        }

        # Use fpgrowth as it works with large sparse matrices better
        logger.info("Find frequent itemsets")
        self.frequent_itemsets = fpgrowth(df, min_support=min_support, use_colnames=True, max_len=max_rule_length)
        logger.info(f"Found {len(self.frequent_itemsets)} frequent itemsets")

        # Generate the association rules
        logger.info("Generate association rules")
        self.rules = association_rules(self.frequent_itemsets, metric="lift", min_threshold=1.0)
        logger.info(f"Created {len(self.rules)} rules")

    def recommend_festivals(
        self,
        artist: str, 
        min_lift: float = 1.0,
        exclude_played: bool = True,
        return_raw: bool = False
    ) -> list:
        """Find festivals where an artist would fit in the lineup.
        
        The result is a list of tuples with the festival name and score. By default the score
        is calculated as an average for a festival by name, by removing the year from the
        name as passed in the festivals dict. Raw results may be returned by setting
        return_raw to True, festivals at which the artist has already played are included.
        
        Note: The correctness of exclude_played obviously depends on the completeness of the
        data in the festivals dict. Data from concerts-metal.com very likely does not include
        all artists, so be ware.

        Args:
            artist (str): _description_
            min_lift (float, optional): _description_. Defaults to 2.0.
            exclude_played (bool, optional): _description_. Defaults to True.
            return_raw (bool, optional): Returns the raw calculation results and does not
                aggregate festival editions. Defaults to False.

        Returns:
            list: _description_
        """    
        # Get co appearing artists from rules
        co_artists = set().union(*self.rules[
            self.rules['antecedents'].apply(lambda x: artist in x) &
            (self.rules['lift'] >= min_lift)
        ]['consequents'])

        # Score each festival by overlap with co-performers
        scored = []
        for festival, artists in self.festivals.items():
            score = len(set(artists) & co_artists)
            scored.append((festival, score))

        # Return raw results if asked, otherwise aggregate
        if return_raw:
            return scored   
        
        ### Tidy up ###
        # Remove year from festival names
        scored = [(re.sub(r"\s\d{4}$", "", festival), score) for festival, score in scored]
        
        # Identify festivals the artist already played if asked
        if exclude_played:
            played_festivals = {re.sub(r"\s\d{4}$", "", festival) for festival, artists in self.festivals.items() if artist in artists}
            scored = [(festival, score) for festival, score in scored if festival not in played_festivals]

        # Calculate average score per festival
        scores = defaultdict(list)
        for name, score in scored:
            scores[name].append(score)
        recommendations = [(name, sum(vals) / len(vals)) for name, vals in scores.items()]
        
        # Remove zero scores and sort
        recommendations = [(name, score) for name, score in recommendations if score > 0]
        recommendations.sort(key=lambda x: x[1], reverse=True)
        
        # Make an explicit note if no recommendations are found
        if not recommendations:
            print(f"No recommendations found for {artist} with given parameters")
            
        return recommendations

    def plot_similarity_graph(
        self,
        N: int = 20,
        remove_isolated_nodes: bool = True,
        node_size: int = 300,
        font_size: int = 16,
        min_similarity: float = 0.1,
        edge_scale: float = 8.0,
        figsize: tuple = (16, 16),
    ) -> None:
        
        # Build binary artist–festival matrix from self.festivals
        logger.info(f"Building binary artist–festival matrix with {len(self.festivals)} festivals")
        df = pd.DataFrame([
            {artist: 1 for artist in lineup}
            for lineup in self.festivals.values()
        ], index=self.festival_names).fillna(0).astype("Sparse[int]")

        top_artists = df.sum(axis=0).sort_values(ascending=False).head(N).index.tolist()
        G = nx.Graph()

        # Add nodes
        for artist in top_artists:
            G.add_node(artist)

        # Add edges based on Jaccard similarity
        logger.info(f"Calculating Jaccard similarity for {len(top_artists)} artists")
        for i, artist_a in enumerate(top_artists):
            a_values = df[artist_a].sparse.to_dense().values
            for j in range(i + 1, len(top_artists)):
                artist_b = top_artists[j]
                b_values = df[artist_b].sparse.to_dense().values
                sim = jaccard_score(a_values, b_values)
                if sim >= min_similarity:
                    G.add_edge(artist_a, artist_b, weight=sim)

        # Remove isolated nodes
        if remove_isolated_nodes:
            logger.info("Removing isolated nodes from graph")
            isolated_nodes = [node for node, degree in G.degree() if degree == 0]
            G.remove_nodes_from(isolated_nodes)

        # Layout and edge weights
        pos = nx.spring_layout(G, k=0.3)
        edge_weights = [G[u][v]['weight'] * edge_scale for u, v in G.edges]

        # Plot
        logger.info(f"Plotting graph with {len(G)} nodes and {len(G.edges)} edges")
        plt.figure(figsize=figsize)
        nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color='#6495ed', alpha=0.9)
        nx.draw_networkx_edges(G, pos, width=edge_weights, edge_color='#444444', alpha=0.6)
        nx.draw_networkx_labels(G, pos, font_size=font_size, font_color='black', font_weight='bold')
        plt.title("Co-appearing artists at festivals", fontsize=font_size + 2)
        plt.axis('off')
        plt.tight_layout()
        plt.show()

# %%
recommender = FestivalRecommender.load(save_path)
recommender.plot_similarity_graph()

# %%
# Start from saved recommender
recommender = FestivalRecommender.load(save_path, verbose=True)
artist_of_interest = "Slipknot"

# Recommend festivals
recommendations = recommender.recommend_festivals(artist_of_interest)
for festival, score in recommendations[:10]:
    print(f"{festival}: score {score:.2f}")


# %%
max_rule_length = 5
min_support_n = 4

# Load data
with open(scr_path, encoding="utf-8") as f:
    festivals = json.load(f)

# Mine rules
recommender = FestivalRecommender()
recommender.mine_rules(
    festivals=festivals, 
    min_support_n=min_support_n, 
    max_rule_length=max_rule_length)

# Recommend festivals
artist_of_interest = "Hiraes"
recommendations = recommender.recommend_festivals(artist_of_interest)
for festival, score in recommendations[:10]:
    print(f"{festival}: score {score:.2f}")
    
# Save and load for demo
recommender.save(save_path)

# %%
# Find artists that have similarity to a given artist

# %%

# %%

# %%

# %%

# %%

# %%
    