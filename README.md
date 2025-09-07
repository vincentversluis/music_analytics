# Music analytics

Some analytics related to music.

## Getting started

Clone the repo and install the requirements:

```bash
git clone https://github.com/vincentversluis/music_analytics.git
cd music_analytics
pip install -r requirements.txt
```

This project uses the friendly-for-data-analysts VS Code Jupyter code cells extension, so use this repo in VS Code and install the extension.

For dealing with requests, this repository uses a database to cache requests. To initialise the database, follow the instructions in [`data/databases/setup.py`](data/databases/setup.py). 


## Projects

The projects are in the [`projects`](projects) folder.

### [`visualise_similar_artists`](projects/visualise_similar_artists/visualise_similar_artists.py)

Visualise [last.fm](https://www.last.fm/) data to compare the popularity of similar artists to produce a graph like this:

![Artist similarity](assets/images/Aephanemer_artist_similarity.png)
