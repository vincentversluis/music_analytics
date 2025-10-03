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

- [Genius](https://docs.genius.com/)
- [Last.fm](https://www.last.fm/api/authentication)
- [Musicbrainz](https://musicbrainz.org/doc/MusicBrainz_API), though an API key is not required
- [Setlist.fm](https://api.setlist.fm/docs/1.0/index.html)
- [Spotify](https://developer.spotify.com/documentation/web-api), for a client ID and secret

When working through the scripts, you will find out where to put .txt files with the API keys.

### Other sources

Other sources of data for projects in this repository:

- [concerts-metal.com](https://en.concerts-metal.com/), which is scraped using `Selenium`
- [Encyclopaedia Metallum](https://www.metal-archives.com/), which is scraped using `Selenium`
- [Genius](https://genius.com/), which is also queried using endpoins, but also scraped using `requests` and `BeautifulSoup`

## Projects

All projects can be found in the [`projects`](projects) folder.

---

### [`compare_lyrics`](projects/compare_lyrics/)

Compare the lyrics of songs by some of my current favourite artists. This uses data from [Genius](https://genius.com/) and results in several plots showing the top and bottom scoring artists for each metric, along with the distribution per metric. To create this I did remove some data points, such as non-English lyrics, so check out the coding for particulars.

A comparison per song results in this plot:

![Lyrics comparison by song](assets/images/Compare_lyrics_metrics_by_song.png)

Lyrically doom metal (Counting Hours, Saturnus) seems to have shorter lyrics than melodic death metal (Aether Realm, Shylmagoghnar). At the same time, or perhaps as an effect, the doom metal (Ocean of Grief, Mar de Grises) vocabulary is more complex, as it uses more different words as can be seen by the lexical diversity metric.

Though typically metal is thought of to have an negative (-1.0) sentiment, some bands actually have a definite average positive (+1.0) sentiment.

---

A comparison aggregated per artist results in this plot:

![Lyrics comparison by song](assets/images/Compare_lyrics_metrics_by_artist.png)

Some artists' lyrical perspective (the use of pronoun _I_ (1.0) versus _we_ (0.0)) leans heavily towards the first person (Der Weg einer Freiheit, White Zombie). Likewise, some artists have a highly directed (the use of pronoun _you_) lyricism (Carcass, Destinity).

Emotionally, metal is usually assumed to be angry or sad, though some bands seem to distinguish themselves with more joyful (Omnium Gatherum) and less angry (Necrophagist) or sad lyrics (Fractal Gates).

---

[COMING SOON]

Using the above metrics, combined with keyword analysis and more quantified emotions, results in a dataset that can be used to cluster artists and analyse artist similarity by lyrics. Clustering artists resuls in this plot:

![clustering](assets/images/Clustering_artists_by_lyrics.png)

In which several artists are highlighted with their nearest neighbours.

...

---

Using the above metrics, it is possible to find similar artists by lyrics. After applying [PCA](https://en.wikipedia.org/wiki/Principal_component_analysis) to the dataframe with lyrics metrics to acquire array `X` with an array of artists `artists`, this function finds the top N similar artists to Insomnium _lyrically_:

```python
find_similar_artists_by_lyrics('Insomnium', X, artists, top_n=10)
```

resulting in this list of tuples with artists and their Euclidean distance to Insomnium lyrics:

```text
[('Mors Principium Est', 0.486),
 ('Swallow the Sun', 0.487),
 ('Wintersun', 0.505),
 ('Harakiri for the Sky', 0.544),
 ('Heaven Shall Burn', 0.559),
 ('Dark Tranquillity', 0.655),
 ('Bloodred Hourglass', 0.668),
 ('Soilwork', 0.675),
 ('Edge of Sanity', 0.682),
 ('Unearth', 0.731)]
```

, which feels about right when reading the lyrics of the found artists.

---

### [`compare_platform_popularity`](projects/compare_platform_popularity/)

Compare the popularity of artists on music platforms [Last.fm](https://www.last.fm/) and [Spotify](https://open.spotify.com/us/) to see if one can be used as a proxy for the other. With a collection of several hundred pretty random artists in different genres, the output is a scatterplot like this:

![Platform comparison](assets/images/Compare_platform_popularity.png)

This illustrates that the number of Spotify followers and Last.fm listeners is a reasonable proxy for artist popularity for different genres, though Spotify popularity is not as good a proxy for either of them. Note that the number of Spotify _listeners_ is not easily scraped and is therefore not included in this analysis.

---

### [`compare_platform_similarity`](projects/compare_platform_popularity/)

The music platforms [Last.fm](https://www.last.fm/) and [Encyclopaedia Metallum](https://www.metal-archives.com/) offer similar artists to a chosen artist. Last.fm appears to do this by analysing users' scrobbles, whilst Encyclopaedia Metallum uses crowdsourced suggestions. To see if the suggestions are consistent, this project compares the given suggestions for three artists of different fame, ranked by the platform's similarity score or suggestion count. The output is a scatterplot like this:

![Platform comparison](assets/images/Compare_platform_similarity.png)

This illustrates that the different platforms have some consensus on the top similar artists, though beyond this, the ranking can differ significantly, with some (to me) amusing descrepancies.

---

### [`match_festivals`](projects/match_festivals/)

(coming soon)

Analyse festival data from [concerts-metal.com](https://en.concerts-metal.com/festivals.html) and find which festivals are a good match for a specific band, using [market basket analysis](https://en.wikipedia.org/wiki/Affinity_analysis).

...

The result can be used by artists to find a good festival to aim to perform at.

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

### [`visualise_tours`](projects/visualise_tours/)

Visualise [concerts-metal.com](https://en.concerts-metal.com/) data to get an idea of what time of year tours start for various bands, resulting in something like:

![First date of tours](assets/images/First_date_of_tours.png)

This gives an idea of when bands start a new tour in a specific part of the world.

---

## Contributing

This is a project to showcase some of my skills in data analysis, so contributions cannot be accepted, but feel free to fork and ask questions.
