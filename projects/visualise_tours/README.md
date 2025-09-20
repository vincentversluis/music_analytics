# Visualise tours

This project attempts to visualise when bands start a new tour in a specific part of the world, using data from [concerts-metal.com](https://concerts-metal.com/).

The retrieval stage is separated from the visualisation stage in [0_get_data_concerts-metal.py](0_get_data_concerts-metal.py), as this requires some time consuming API calls to [Last.fm](https://www.last.fm/) for finding bands to investigate and [concerts-metal.com](https://concerts-metal.com/) for getting data on concerts. The data is saved to a csv file and loaded in [1_visualise_tours.py](1_visualise_tours.py), where it is then visualised, resulting in something like this:

![First date of tours](../../assets/images/First_date_of_tours.png)

## Choice of data source

For data on tours by metal artists, there are two main sources:

- [concerts-metal.com](https://concerts-metal.com/), which is a crowdsourced website on concerts and festival dates and lineups, that focuses on metal and adjacent artists.
- [Setlist.fm](https://setlist.fm/), which is a website that focuses on providing setlists for concerts in general, but also lists where and when a concert took place.

Though Setlist.fm features a very convenient API and fun concert details (such as obviously the setlist, but also event coordinates), the available data makes it slightly tricky to work with for my intended use. It is not straightforward to label a concert as part of a tour, incidental gig  or festival performance, and it is also not easy to assign concerts to a specific tour.

The concerts-metal.com data is more straightforward to work with, as it pretty much features the data I need, though there is no API, which means old school scraping fun and parsing delight is needed.

On spot checking the available data on specific concerts, it does turn out that for more obscure bands (or really old concerts), both sources do not always have an entry for the concert at all. This means for sake of completeness, the sources should be seen as complementary and it is worth it considering combining the data.

On the whole, using the concerts-metal.com data is the convenient choice to make, as gaps in information should not pose a problem for the intended use.

The coding for scraping Setlist.fm was kept as a future reference.

## Aggregation rules

The intention is to aggregate data by artist by tour. The scraped data (partly made up sample) looks like this for Arch Enemy:

| Date       | Country | Tour Name                    | City           | Venue             |
|------------|---------|------------------------------|----------------|-------------------|
| ...        | ...     | ...                          | ...            | ...               |
| ...        | ...     | War Eternal - American Tour  | ...            | ...               |
| ...        | ...     | War Eternal - American Tour  | ...            | ...               |
| 05/11/2014 | us      | War Eternal - American Tour  | Worcester      | The Palladium     |
| 29/10/2014 | ru      | Arch Enemy - Tour 2014       | Moscow         | GlavClub          |
| 25/10/2014 | us      | War Eternal - American Tour  | Worcester      | The Palladium     |
| 25/10/2014 | us      | War Eternal - American Tour  | Worcester      | The Palladium     |
| 24/10/2014 | us      | War Eternal - American Tour  | New York       | Best Buy Theater  |
| 23/10/2014 | us      | War Eternal - American Tour  | Baltimore      | Soundstage        |
| 18/10/2014 | jp      | Loud Park Festival 2014      | Saitama        | Super Arena       |
| 17/10/2014 | jp      | Loud Park Festival 2014      | Saitama        | Super Arena       |
| 03/10/2014 | ru      | Arch Enemy - Tour 2014       | Yekaterinburg  | Tele-Club         |
| 02/10/2014 | ru      | Arch Enemy - Tour 2014       | Kurgan         | DKM Hall          |
| 30/09/2014 | ru      | Arch Enemy - Tour 2014       | Samara         | Zvezda            |
| ...        | ...     | Arch Enemy - Tour 2014       | ...            | ...               |
| ...        | ...     | Arch Enemy - Tour 2014       | ...            | ...               |
| ...        | ...     | Arch Enemy - Tour 2014       | ...            | ...               |
| ...        | ...     | ...                          | ...            | ...               |

The rules for combining multiple concerts into one tour are simple:

- A concert has at least 6 concerts, this means the Japan concerts on 18/10/2014 and 19/10/2014 are not part of a tour. These are concerts that are probably incidental gigs or festival performances.
