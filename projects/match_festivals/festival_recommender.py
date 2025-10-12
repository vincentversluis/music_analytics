"""A recommender system for music festivals based on artist co-appearances."""

# %% IMPORTS
from collections import defaultdict
from itertools import chain
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


# %% CLASS
class FestivalRecommender:
    """A modular recommender system for music festivals based on artist co-appearances.

    This class uses the association rules mining algorithm from mlxtend to mine rules
    from a dataset of festivals and their artists. The rules are then used to recommend
    festivals for a given artist. The recommendations are based on the Jaccard
    similarity of the artists in the festival lineup.

    Attributes:
        festivals (dict): A dictionary with festival names as keys and lists of artists
            as values.
        festival_names (list): A list of festival names.
        frequent_itemsets (pd.DataFrame): A DataFrame with frequent itemsets.
        rules (pd.DataFrame): A DataFrame with association rules.
        mining_settings (dict): A dictionary with mining settings.

    For example usage, see the example notebook in the project folder and the README.
    """

    def __init__(self):
        """Initialise the object. Attributes are loaded throughout the methods."""
        self.festivals: dict = {}
        self.festival_names: list = []
        self.frequent_itemsets: pd.DataFrame = pd.DataFrame()
        self.rules: pd.DataFrame = pd.DataFrame()
        self.mining_settings: dict = {}

    def save(self, path: str) -> None:
        """Save object to a pickle file.

        Args:
            path (str): The path to the pickle file.
        """
        with open(path, "wb") as f:
            pickle.dump(self, f)
        logger.info(f"Saved recommender to {path}")

    @classmethod
    def load(cls, path: str, verbose: bool = False) -> None:
        """Load object from a pickle file.

        Args:
            path (str): The path to the pickle file.
            verbose (bool, optional): If a summary of the loaded object should be
                printed. Defaults to False.
        """
        logger.info(f"Loading recommender from {path}")
        with open(path, "rb") as f:
            obj = pickle.load(f)
        logger.info(f"Loaded recommender from {path}")

        if verbose:
            print("Loading summary:")
            obj.summary()

        return obj

    def summary(self) -> None:
        """Show a summary of the object."""
        pprint({
            "festivals": len(self.festivals),
            "rules": len(self.rules),
            "settings": self.mining_settings,
        })
        print()

    def mine_rules(
        self,
        festivals: dict[str, list[str]],
        min_support_n: int = 4,
        max_rule_length: int = 5,
    ) -> None:
        """Mine association rules.

        This uses a sparse dataframe with binary festival-artist matrix to mine rules
        based on the association rules algorithm from mlxtend. The rules and frequent
        itemsets are stored in the object.

        This takes minimum support as a number of lineups an artist needs to share to
        be considered for a rule, rather than defining a min_support value as a
        fraction, as this applies to the real world usage of this project more.

        Note: This takes a while if the data results in a large and very sparse set.

        Args:
            festivals (dict[str, list[str]]): Festivals with name as key and artists as
                values.
            min_support_n (int, optional): Minimum number of lineups an artist needs to
                share to be considered for a rule. Defaults to 4.
            max_rule_length (int, optional): Maximum length of a rule. Defaults to 5.
        """
        # Only keep festivals with more than one artist, then make it into a dict
        self.festivals = {
            festival: artists
            for festival, artists in festivals.items()
            if len(artists) > 1
        }

        # Get lineup, festival names and artists
        self.festival_names = list(self.festivals.keys())
        lineups = self.festivals.values()
        artists = set(chain.from_iterable(lineups))
        logger.info(
            f"Found {len(lineups):,} lineups containing {len(artists):,} artists"
        )

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
        logger.info(
            f"Found {df.shape[0]:,} lineups with {df.shape[1]:,} artists after cleaning"
        )

        # Convert to sparse to be kinder on memory
        df = df.astype(pd.SparseDtype("bool", fill_value=False))

        self.mining_settings = {
            "min_support": min_support,
            "min_support_n": min_support_n,
            "max_rule_length": max_rule_length,
        }

        # Use fpgrowth as it works with large sparse matrices better
        logger.info("Find frequent itemsets")
        self.frequent_itemsets = fpgrowth(
            df, min_support=min_support, use_colnames=True, max_len=max_rule_length
        )
        logger.info(f"Found {len(self.frequent_itemsets)} frequent itemsets")

        # Generate the association rules
        logger.info("Generate association rules")
        self.rules = association_rules(
            self.frequent_itemsets, metric="lift", min_threshold=1.0
        )
        logger.info(f"Created {len(self.rules)} rules")

    def recommend_festivals(
        self,
        artist: str,
        min_lift: float = 1.0,
        exclude_played: bool = True,
        return_raw: bool = False,
    ) -> list:
        """Find festivals where an artist would fit in the lineup.

        The result is a list of tuples with the festival name and score. By default the
        score is calculated as an average for a festival by name, by removing the year
        from the name as passed in the festivals dict. Raw results may be returned by
        setting return_raw to True, festivals at which the artist has already played are
        included.

        Note: The correctness of exclude_played obviously depends on the completeness of
        the data in the festivals dict. Data from concerts-metal.com very likely does
        not include all artists, so be ware.

        Args:
            artist (str): The artist's name.
            min_lift (float, optional): Minimum lift score. Defaults to 2.0.
            exclude_played (bool, optional): If festivals the artist has already played
                at should be excluded. Defaults to True.
            return_raw (bool, optional): Returns the raw calculation results and does
                not aggregate festival editions. Defaults to False.

        Returns:
            list: The recommended festivals with the score.
        """
        # Get co appearing artists from rules
        co_artists = set().union(
            *self.rules[
                self.rules["antecedents"].apply(lambda x: artist in x)
                & (self.rules["lift"] >= min_lift)
            ]["consequents"]
        )

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
        scored = [
            (re.sub(r"\s\d{4}$", "", festival), score) for festival, score in scored
        ]

        # Identify festivals the artist already played if asked
        if exclude_played:
            played_festivals = {
                re.sub(r"\s\d{4}$", "", festival)
                for festival, artists in self.festivals.items()
                if artist in artists
            }
            scored = [
                (festival, score)
                for festival, score in scored
                if festival not in played_festivals
            ]

        # Calculate average score per festival
        scores = defaultdict(list)
        for name, score in scored:
            scores[name].append(score)
        recommendations = [
            (name, sum(vals) / len(vals)) for name, vals in scores.items()
        ]

        # Remove zero scores and sort
        recommendations = [
            (name, score) for name, score in recommendations if score > 0
        ]
        recommendations.sort(key=lambda x: x[1], reverse=True)

        # Make an explicit note if no recommendations are found
        if not recommendations:
            print(f"No recommendations found for {artist} with given parameters")

        return recommendations

    def plot_similarity_graph(
        self,
        top_n: int = 20,
        remove_isolated_nodes: bool = True,
        node_size: int = 300,
        font_size_artists: int = 16,
        font_size_title: int = 32,
        min_similarity: float = 0.1,
        edge_scale: float = 8.0,
        figsize: tuple = (16, 16),
        title: str = "Co-appearing artists at festivals",
    ) -> None:
        """Plot artists that have co-appeared at festivals.

        Args:
            top_n (int, optional): How many top artists to consider. Defaults to 20.
            remove_isolated_nodes (bool, optional): If isolated nodes should be removed.
                Defaults to True.
            min_similarity (float, optional): Minimum similarity threshold. Defaults to
                0.1.
            node_size (int, optional): Plotted node size. Defaults to 300.
            font_size_artists (int, optional): Plotted artist name font size. Defaults
                to 16.
            font_size_title (int, optional): Plotted title font size. Defaults to 32.
            edge_scale (float, optional): Ploting edge weight scale. Defaults to 8.0.
            figsize (tuple, optional): Plot figure size. Defaults to (16, 16).
            title (str, optional): Plot title.
        """
        # Build binary artist-festival matrix from self.festivals
        logger.info(
            f"Building binary artist-festival matrix with {len(self.festivals)} festivals"
        )
        df = (
            pd.DataFrame(
                [
                    {artist: 1 for artist in lineup}
                    for lineup in self.festivals.values()
                ],
                index=self.festival_names,
            )
            .fillna(0)
            .astype("Sparse[int]")
        )

        top_artists = (
            df.sum(axis=0).sort_values(ascending=False).head(top_n).index.tolist()
        )
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
        edge_weights = [G[u][v]["weight"] * edge_scale for u, v in G.edges]

        # Plot
        logger.info(f"Plotting graph with {len(G)} nodes and {len(G.edges)} edges")
        plt.figure(figsize=figsize)
        nx.draw_networkx_nodes(
            G, pos, node_size=node_size, node_color="#6495ed", alpha=0.9
        )
        nx.draw_networkx_edges(
            G, pos, width=edge_weights, edge_color="#444444", alpha=0.6
        )
        nx.draw_networkx_labels(
            G, pos, font_size=font_size_artists, font_color="black", font_weight="bold"
        )
        plt.title(title, fontsize=font_size_title)
        plt.axis("off")
        plt.tight_layout()
        plt.show()

    def find_coappearing_artists(
        self,
        artist: str,
        top_n: int = 100,
        min_similarity: float = 0.1,
        return_scores: bool = True,
    ) -> list:
        """Find artists similar to a given artist based on Jaccard similarity.

        Args:
            artist (str): Target artist name.
            top_n (int): Number of top artists to consider.
            min_similarity (float): Minimum similarity threshold.
            return_scores (bool): Whether to return similarity scores.

        Returns:
            list: List of similar artists (optionally with scores).
        """
        if not self.festivals:
            raise ValueError("Festival data is empty. Run mine_rules() first.")

        logger.info(
            f"Building binary artist–festival matrix with {len(self.festivals)} festivals"
        )
        df = (
            pd.DataFrame(
                [{a: 1 for a in lineup} for lineup in self.festivals.values()],
                index=self.festival_names,
            )
            .fillna(0)
            .astype("Sparse[int]")
        )

        if artist not in df.columns:
            raise ValueError(f"Artist '{artist}' not found in dataset.")

        top_artists = (
            df.sum(axis=0).sort_values(ascending=False).head(top_n).index.tolist()
        )
        top_artists = [a for a in top_artists if a != artist]

        a_values = df[artist].sparse.to_dense().values
        similar = []

        logger.info(
            f"Calculating Jaccard similarity for {len(top_artists)} artists vs '{artist}'"
        )
        for other in top_artists:
            b_values = df[other].sparse.to_dense().values
            sim = jaccard_score(a_values, b_values)
            if sim >= min_similarity:
                similar.append((other, sim) if return_scores else other)

        similar.sort(key=lambda x: x[1] if return_scores else 0, reverse=True)
        return similar
