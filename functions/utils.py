# %% HEADER
# General utility functions
# TODO: Docstrings

# %% IMPORTS
import arrow
from dateutil import parser


# %% FUNCTIONS
def get_parsed_date(date):
    date = parser.parse(date, default=arrow.get("2020-07-31"))
    date = arrow.get(date)
    return date
