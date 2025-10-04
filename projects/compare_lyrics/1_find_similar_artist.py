# %% HEADER
# Find similar artists to a given artist using Euclidian distance after scaling and PCA

# %% IMPORTS
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import pairwise_distances
from sklearn.preprocessing import MinMaxScaler


# %% FUNCTIONS
def find_similar_artists_by_lyrics(artist: str, X: np.ndarray, artists: np.ndarray, 
                         top_n: int | None = None) -> list:
    """Find similar artists to a given artist using KNN.

    Args:
        artist (str): The artist to find similar artists for.
        X (np.ndarray): The PCA-transformed features.
        artists (np.ndarray): The artist labels.
        top_n (int): The number of similar artists to find. Defaults to None, which means all.

    Returns:
        list: The top N similar artists to the given artist.
    """
    # Set top_n to all if not specified
    if top_n is None:
        top_n = len(artists) - 1  # Exclude self-match
        
    target_index = np.where(artists == artist)[0][0]
    target_vector = X[target_index].reshape(1, -1)

    # Compute Euclidean distances
    distances = pairwise_distances(X, target_vector, metric='euclidean').flatten()

    # Exclude self-match
    distances[target_index] = np.inf

    # Get top N nearest indices
    nearest_indices = np.argsort(distances)[:top_n]
    nearest_artists = artists[nearest_indices]
    nearest_distances = distances[nearest_indices]

    # Display results
    return [(artist, float(round(dist, 3))) for i, (artist, dist) in enumerate(zip(nearest_artists, nearest_distances), 1)]
        

# %% ANALYSE DATA
artist_agg_df = pd.read_pickle('../../data/lyrics_analysis_artist_agg_df.pickle')

# Keep only numeric columns
artist_col = artist_agg_df[['artist']]
numeric_df = artist_agg_df.select_dtypes(include='number')
artist_agg_df = pd.concat([artist_col, numeric_df], axis=1)

# Scale values
scaler = MinMaxScaler()
scaled_values = scaler.fit_transform(artist_agg_df.drop(columns='artist'))
scaled_df = pd.DataFrame(scaled_values, columns=numeric_df.columns)
scaled_df['artist'] = artist_agg_df['artist'].values

# Drop non-numeric columns
artist_col = scaled_df[['artist']]
numeric_df = scaled_df.select_dtypes(include='number')

# Do PCA
X = scaled_df.drop(columns='artist')
pca = PCA(n_components=0.95)  # Keep enough components to explain .95 variance
X_pca = pca.fit_transform(X)
pca_df = pd.DataFrame(X_pca)
pca_df['artist'] = scaled_df['artist'].values

# Find similar artists
artist = 'Insomnium'
X = pca_df.drop(columns='artist').values
artists = pca_df['artist'].values

# Use the function
find_similar_artists_by_lyrics('Insomnium', X, artists, top_n=None)

# %%
