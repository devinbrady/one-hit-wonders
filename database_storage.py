import os
import psycopg2
from artist_score import ArtistScore
from sqlobject import *

def setup():
    sqlhub.processConnection = connectionForURI(connection_string())
    ArtistScore.createTable(ifNotExists=True)


def connection_string():
    env_url = os.environ.get('DATABASE_URL')
    if env_url and not env_url.isspace(): return env_url

    db_filename = os.path.abspath('ohw.db')
    if os.path.exists(db_filename): os.unlink(db_filename)
    return 'sqlite:' + db_filename
