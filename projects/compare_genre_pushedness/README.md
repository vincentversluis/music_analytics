## Compare genre pushedness

This project compares the pushedness of artists of different genres on Spotify.

Pushedness is defined as the number of monthly listeners divided by the number of followers and can be seen as a measure of how well an artist is suggested by the Spotify suggestion algorithm.

The retrieval stage is separated from the visualisation stage, as this requires some time consuming API calls to Spotify and Last.fm. Tthe results are saved in [0_get_data.py](0_get_data.py) and then loaded in [1_compare_genre_pushedness.py](1_compare_genre_pushedness.py), where it is then visualised. To generalise the results within genres, the outlying 5% of top and bottom pushed artists are removed and only artists with at least 10,000 monthly listeners are kept.
