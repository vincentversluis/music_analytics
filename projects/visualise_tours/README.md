## Visualise tours

This project attempts to visualise when bands start a new tour in a specific part of the world.

The retrieval stage is separated from the visualisation stage, as this requires some time consuming API calls to Setlist.fm, the calls and responses are inconvenient for caching in a database. Instead the results are saved to a CSV file in [0_get_data.py](0_get_data.py) and then loaded in [1_visualise_tours.py](1_visualise_tours.py), where it is then visualised.
