# %% HEADER
# A collection of functions to deal with lyrics.

# %% IMPORTS
from functools import cache
import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# %% CONSTANTS
# Define pronouns
PRONOUNS = {
    "first_person_sg": [
        "i",
        "me",
        "my",
        "mine",
        "myself",
    ],
    "first_person_pl": [
        "we",
        "us",
        "our",
        "ours",
        "ourselves",
    ],
    "second_person_sg_pl": [
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
    ],
    "third_person_masc": [
        "he",
        "him",
        "his",
        "himself",
    ],
    "third_person_fem": [
        "she",
        "her",
        "hers",
        "herself",
    ],
    "third_person_neut": [
        "it",
        "its",
        "its",
        "itself",
    ],
    "third_person_ep_pl": [
        "they",
        "them",
        "their",
        "theirs",
        "themself",
        "themselves",
    ],
}

# Create regex patterns for each pronoun
PRONOUN_PATTERNS = {
    pronoun_type: re.compile(r"\b({})\b".format("|".join(PRONOUNS[pronoun_type])))
    for pronoun_type in PRONOUNS
}


# %% FUNCTIONS
@cache
def is_junk_line(line: str) -> bool:
    """Determine if a line is junk.

    This is a heuristic based on a sample of Genius
    lyrics. Junk lines are those that are not song lyrics, but are instead a count
    of contributors, the statement about the lyrics being lyrics or a tag such as
    [Chorus], [Verse 1], [Verse 2], etc.

    Args:
        line (str): The line to check.

    Returns:
        bool: If the line is junk.
    """
    junk_patterns = [
        r"^\d+.*[Cc]ontributors{0,1}$",  # Contributors
        r"^.*\sLyrics$",  # (song title) Lyrics
        r"^\[.*\]$",  # [Chorus], [Verse 1], [Verse 2], ...
    ]
    junk_pattern = re.compile(r"|".join(junk_patterns))
    return bool(junk_pattern.search(line.strip()))


def clean_lyrics(raw_lines: list) -> str:
    """Clean lyrics from raw lyrics lines as scraped from Genius.

    Remove obvious junk lines, combine everything into one string and remove stuff
    within square brackets (which are usually leftovers from not found junk lines).

    Args:
        raw_lines (list): The raw lines of lyrics.

    Returns:
        str: Cleaned lyrics.
    """
    # Remove junk lines and combine everything into one comma separated string
    semi_clean_lyrics = ", ".join([
        line for line in raw_lines if not is_junk_line(line) and line.strip()
    ])

    # Remove everything withing square brackets (these are leftovers from not found
    # junk lines, when a note was spread over multiple lines)
    clean_lyrics = re.sub(r"\[[^\]]*\]", "", semi_clean_lyrics)

    return clean_lyrics


def get_compound_sentiment(sentence: str) -> dict:
    """Get compound sentiment for a sentence.

    The compound score is a number between -1.0 and +1.0. The rough meanings of the
    scores are as follows:
    -1.0 to -0.5	Strongly Negative
    -0.5 to -0.1	Mildly Negative
    -0.1 to +0.1	Neutral
    +0.1 to +0.5	Mildly Positive
    +0.5 to +1.0	Strongly Positive

    Args:
        sentence (str): The sentence to get compound sentiment for.

    Returns:
        dict: The compound sentiment for the sentence.
    """
    compound_sentiment = SentimentIntensityAnalyzer().polarity_scores(sentence)[
        "compound"
    ]
    return compound_sentiment


def count_pronouns(text: str) -> dict:
    """Count pronouns in a text.

    The text is converted to lower case before counting.

    Args:
        text (str): The text to count pronouns in.

    Returns:
        dict: The count of pronouns in the text.
    """
    pronoun_count = {
        pronoun_type: len(pattern.findall(text.lower()))
        for pronoun_type, pattern in PRONOUN_PATTERNS.items()
    }

    return pronoun_count
