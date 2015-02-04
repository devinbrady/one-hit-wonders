#!/usr/bin/env python

from sqlobject import *

class ArtistScore(SQLObject):
    artist = StringCol()
    track  = StringCol()
    score  = DecimalCol(10,8)
    artist_id         = StringCol()
    artist_popularity = IntCol()
    top_track_id      = StringCol()
    popularity_scores = StringCol()
    random = BoolCol()

    # add source column
