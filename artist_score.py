#!/usr/bin/env python

from sqlobject import *

class ArtistScore(SQLObject):
    artist = StringCol()
    track  = StringCol()
    score  = IntCol()
