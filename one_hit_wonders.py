#!/usr/bin/env python

import httplib
import os
import datetime
import json
import numpy as np
import pandas as pd


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
        self.__conn         = httplib.HTTPSConnection('api.spotify.com')
        self.__country_code = 'US'
        self.__print_all_tracks = False # if True, will print the top tracks for each artist

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

        df = pd.DataFrame()

        for i, band in enumerate(bands):

            print '\nArtist: {}'.format(band)

            artist_id = self.get_artist_id(band)
            top_tracks = self.get_top_tracks(artist_id)
            score, top_track_name = self.calculate_score(top_tracks)

            print 'One Hit Wonder Score: {0:.0f}'.format(score)

            data_row = pd.DataFrame({
                "Artist": band,
                "Top Track": top_track_name,
                "OHW Score": score
            }, index=[i])

            # print data_row

            df = df.append(data_row)

        df = df.sort(columns='OHW Score', ascending=False)

        self.save_dataframe(df, 'ohw score')

        return None


    def get_artist_id(self, artist_name):
        artist_name_url = artist_name.lower().replace(' ','%20')

        results = self.query_spotify("/v1/search?q={}&type=artist".format(artist_name_url))

        # at some point, confirm that we got exactly 1 result

        artist_id = results['artists']['items'][0]['id']

        return artist_id


    def get_top_tracks(self, artist_id):
        results = self.query_spotify("/v1/artists/{0}/top-tracks?country={1}".format(artist_id, self.__country_code))

        return results['tracks']


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
        sorted_tracks = sorted(top_tracks, key=lambda x: x['popularity'], reverse=True)

        top_track_name = sorted_tracks[0]['name']

        top_tracks_popularity = [sorted_tracks[0]['popularity']]

        for i, track in enumerate(sorted_tracks):
            if self.__print_all_tracks:
                print '{0}. ({1}) {2}'.format(i+1, track['popularity'], track['name'])

            if i != 0:
                if top_track_name not in track['name']:
                    top_tracks_popularity.append(track['popularity'])
                elif self.__print_all_tracks:
                    print '^^^^^^^ duplicate of top hit, will exclude'

        if not self.__print_all_tracks:
            print 'Top Hit: {}'.format(sorted_tracks[0]['name'])

        score = top_tracks_popularity[0] - np.mean(top_tracks_popularity[1:len(top_tracks_popularity)])

        return score, top_track_name


    def save_dataframe(self, df, prefix='output'):
        output_dir = os.path.dirname(os.path.realpath(__file__)) + '/csv'

        # if output directory doesn't exist, make it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = '{0}/{1} {2}.csv'.format(output_dir, prefix, datetime.datetime.now().strftime("%Y-%m-%d %H,%M,%S"))

        df.to_csv(output_file)

        print 'DataFrame saved to: {}'.format(output_file)

        return None

if __name__ == '__main__':
    ohw = OneHitWonders()
    ohw.rank_artists()
