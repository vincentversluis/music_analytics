## Compare platform similarity

This project compares the similarity of metal artists on the music platforms [Last.fm](https://www.last.fm/) and [Encyclopaedia Metallum](https://www.metal-archives.com/).

The data retrieval stage is separated from the visualisation stage, as this requires some time browser interaction with Encyclopaedia Metallum, which is inconvenient to do combined with the visualisation stage. The result of this interaction is saved to a CSV file in [0_get_data.py](0_get_data.py). Last.fm data is retrieved in [1_compare_platform_similarity.py](1_compare_platform_similarity.py), where it is then visualised together with the data from Encyclopaedia Metallum.
