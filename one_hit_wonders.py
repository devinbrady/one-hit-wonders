#!/usr/bin/env python

import httplib
import datetime
import json
import numpy as np
import database_storage
from random import randint
from artist_score import ArtistScore


# todo:
# make function for getting artists from playlists
# store list of artists to text file
# query playlists with "one hit wonder" in title
# print non-ascii characters like in the Gotye track

# done:
# filter out duplicates in get_top_tracks
# handle Spotify API errors more gracefully
# store score to dataframe, export to CSV

class OneHitWonders:

    def __init__(self):
        self.__conn             = httplib.HTTPSConnection('api.spotify.com')
        self.__country_code     = 'US'
        self.__print_all_tracks = False # if True, will print the top tracks for each artist

        database_storage.setup()

    def rank_artists(self):
        # bands = ['Toni Basil']
        bands = ['Harvey Danger'
            # , 'Radiohead'
            # , 'Lou Bega'
            # , 'Gotye'
            , 'Toni Basil'
            # , 'Belle & Sebastian'
            # , 'Vanilla Ice'
            # , 'Devo'
            # , 'Patrick Swayze'
            # , 'B*Witched'
            # , 'Macy Gray'
            # , 'The Monroes'
            # , 'HTRK'
            # , 'Dexys Midnight Runners'
            ]

        for i, band in enumerate(bands):
            # print '\nArtist: {}'.format(band)
            self.calculate_and_store(self.get_artist(band))

        return None


    def calculate_and_store(self, artist, random=True):
        if ArtistScore.selectBy(artist_id=artist["id"]).count() != 0: return None

        top_tracks = self.get_top_tracks(artist["id"]) # [{'popularity': 61, 'id': u'7cz70nyRXlCJOE85whEkgU', 'name': u'Flagpole Sitta'},...]

        if top_tracks:
            score = self.calculate_score(top_tracks)

            # print artist["name"] + ' One Hit Wonder Score: {0:.0f}'.format(score)

            # UnicodeEncodeError: 'ascii' codec can't encode character u'\xf3' in position 5: ordinal not in range(128)

            artist_score = ArtistScore(artist=artist["name"]
            , track=top_tracks[0]['name']
            , score=score
            , artist_id=artist["id"]
            , artist_popularity=artist["popularity"]
            , top_track_id=top_tracks[0]['id']
            , popularity_scores=",".join([str(track['popularity']) for track in top_tracks])
            , random=random
            )


    def get_artist(self, artist_name):
        artist_name_url = artist_name.lower().replace(' ','%20')

        results = self.query_spotify("/v1/search?q={}&type=artist".format(artist_name_url))

        # at some point, confirm that we got exactly 1 result

        return results['artists']['items'][0]

    def random_artist(self):
        base_query = "/v1/search?q=year%3A0000-9999&type=artist&market=" + self.__country_code
        results = self.query_spotify(base_query)
        total = results["artists"]["total"]

        results = self.query_spotify("{0}&limit=1&offset={1}".format(base_query, randint(0,total)))["artists"]["items"]

        return results[0] if len(results) > 0 else None

    # Gets relevant info about top tracks, sorts by popularity,
    # and removes duplicate tracks before returning.
    def get_top_tracks(self, artist_id):
        results = self.query_spotify("/v1/artists/{0}/top-tracks?country={1}".format(artist_id, self.__country_code))['tracks']

        if len(results) > 1:
            relevant_info  = lambda track: {'popularity':track['popularity'], 'id':track['id'], 'name':track['name']}
            tracks_info    = [relevant_info(track) for track in results]

            sorted_tracks  = sorted(tracks_info, key=lambda x: x['popularity'], reverse=True)

            top_track      = sorted_tracks[0]
            is_duplicate   = lambda track: top_track['id'] != track['id'] and top_track['name'] in track['name']
            unique_tracks  = [track for track in sorted_tracks if not is_duplicate(track)]

            if len(unique_tracks) > 1 return unique_tracks


    def query_spotify(self, url):
        self.__conn.request('GET', url)

        r1 = self.__conn.getresponse()

        # if HTML status isn't 200, throw error
        if r1.status != 200:
            error_str = 'Bad HTML status from Spotify: {0} {1}'.format(r1.status, r1.reason)
            raise RuntimeError(error_str)

        results = json.loads(r1.read())

        return results


    def calculate_score(self, top_tracks):
        top_tracks_popularity = [track['popularity'] for track in top_tracks]
        return top_tracks_popularity[0] - np.mean(top_tracks_popularity[1:len(top_tracks_popularity)])


    def get_top_ohws(self):
        artist_scores = ArtistScore.select('all', orderBy='score desc', limit=10)

        for artist_score in artist_scores:
            print '{0},{1},{2}'.format(artist_score.artist, artist_score.track, artist_score.score)

        return None

if __name__ == '__main__':
    ohw = OneHitWonders()
    ohw.rank_artists()
    ohw.get_top_ohws()
