## Compare platform popularity

This project compares the popularity of artists on different platforms.

The retrieval stage is separated from the visualisation stage, as this requires some time consuming API calls to Spotify, the calls and responses are inconvenient for caching in a database. Instead the results are saved to a CSV file in [0_get_data.py](0_get_data.py) and then loaded in [1_compare_platform_popularity.py](1_compare_platform_popularity.py), where it is then visualised.
