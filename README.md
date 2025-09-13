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

For dealing with requests to various end points, this repository uses a database to cache requests, to make things a bit faster and not hammer servers too much. To initialise the database, follow the instructions in [`data/databases/setup.py`](data/databases/setup.py).

### Querying endpoints

Functions query several endpoints, check out their definitions to figure out which ones. Typically the endpoints like one request per second, so the functions will sleep for a bit between requests to avoid hammering the server and causing 429 errors.

To get API keys for endpoints, you can use the following links:

- Last.fm: https://www.last.fm/api/authentication
- Musicbrainz: https://musicbrainz.org/doc/MusicBrainz_API, though an API key is not required

When working through the scripts, you will find out where to put .txt files with the API keys.

## Projects

All projects are in the [`projects`](projects) folder.

### [`compare_popularity`](projects/compare_popularity/compare_popularity.py)

Compare the popularity of artists on [Last.fm](https://www.last.fm/) and [spotify](https://open.spotify.com/us/) to see how different the two platforms are. The output is a scatterplot like this:

...

This gives an idea of why it might not be a good idea to use only Spotify or Last.fm listeners as a proxy for artist popularity.

---

### [`predict_releases`](projects/predict_releases/predict_releases.py)

Visualise [musicbrainz](https://musicbrainz.org/) data to visualise when albums were released and when to expect the next one, based on some simple metrics:

![Album release dates](assets/images/Expected_release_dates.png)

This can be used to get hyped up about upcoming releases. On spot checking announced release dates, this seems to work reasonably well.

---

### [`visualise_similar_artists`](projects/visualise_similar_artists/visualise_similar_artists.py)

Visualise [Last.fm](https://www.last.fm/) data to compare the popularity of similar artists to produce a graph like this:

![Artist similarity](assets/images/Aephanemer_artist_similarity.png)

This can be used to find artists to listen to. Though I am unsure how Last.fm's similarity score is calculated, it feels about right.

---

### [`visualise_tours`](projects/visualise_tours/visualise_tours.py)

Visualise [setlist.fm](https://setlist.fm/) data to get an idea of what time of year tours start, resulting in something like:

...

---

## Contributing

Contributions are welcome! Feel free to open an issue or pull request.
