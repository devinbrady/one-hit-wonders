#!/usr/bin/env python

import httplib
import os
import datetime
import json
import numpy as np
from sqlobject import *
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

        self.setup_db()

    def rank_artists(self):
        # bands = ['Toni Basil']
        # bands = ['Harvey Danger'
        #     , 'Radiohead'
        #     , 'Lou Bega'
        #     # , 'Gotye'
        #     , 'Toni Basil'
        #     , 'Belle & Sebastian'
        #     , 'Vanilla Ice'
        #     , 'Devo'
        #     , 'Patrick Swayze'
        #     , 'B*Witched'
        #     , 'Macy Gray'
        #     , 'The Monroes'
        #     , 'HTRK'
        #     , 'Dexys Midnight Runners'
        #     , 'Primitive Radio Gods'
        #     # , 'Los Del Rio'
        #     ]

        wikipedia = self.load_data('One Hit Wonders (sample) - Sheet1.csv')
        bands = wikipedia['Artist']

        # ohw_playlists = self.get_playlists('One Hit Wonders')
        # bands = self.get_playlist_artists('spotifybrazilian', '2wUnnQjLQsbl90brPUNFFx')

        for i, band in enumerate(bands):
            if ArtistScore.selectBy(artist=band).count() == 0:
                print '\nArtist: {}'.format(band)

                artist_id = self.get_artist_id(band)
                top_tracks = self.get_top_tracks(artist_id)
                score, top_track_name = self.calculate_score(top_tracks)

                print 'One Hit Wonder Score: {0:.0f}'.format(score)

                ArtistScore(artist=band, track=top_track_name, score=score)

        return None


    def get_playlists(self, search_string):

        search_string_encoded = search_string.lower().replace(' ','%20')

        results = self.query_spotify("/v1/search?q={}&type=playlist".format(search_string_encoded))

        print results

        playlist_ids = ['1']

        return playlist_ids

    def get_playlist_artists(self, user_id, playlist_id):

        results = self.query_spotify("/v1/users/{user_id}/playlists/{playlist_id}/tracks".format(user_id=user_id, playlist_id=playlist_id))
        
        print results
        
        playlist_artists = ['Harvey Danger']

        return playlist_artists

    def get_artist_id(self, artist_name):
        artist_name_url = artist_name.lower().replace(' ','%20')

        results = self.query_spotify("/v1/search?q={}&type=artist".format(artist_name_url))

        if results['artists']['total'] == 0:
            print 'WARNING: zero search results for: {}'.format(artist_name)
            artist_id = 0
        else: 
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

    def setup_db(self):
        db_filename = os.path.abspath('ohw.db')
        if os.path.exists(db_filename):
            os.unlink(db_filename)
        connection_string = 'sqlite:' + db_filename
        connection = connectionForURI(connection_string)
        sqlhub.processConnection = connection

        try:
            ArtistScore.createTable()
        except dberrors.OperationalError:
            print 'ArtistScore table exists.'

    def load_data(self, data_file):
        """
        Load a data file into a dataframe
        """

        if data_file[0] == '/':
            # assume data_file is full path
            data_path = data_file
        else: 
            # assume data file is in the same directory as this script
            project_path = os.path.dirname(os.path.realpath(__file__))
            data_path = project_path + '/' + data_file

        # verify that file exists
        if not os.path.isfile(data_path):
            sys.exit('File does not exist: ' + data_path)

        print '\nLoading file: ' + data_file

        fileName, fileExtension = os.path.splitext(data_path)
        if any(fileExtension == s for s in ['.txt','.tsv']):
            data = pd.read_table(data_path)
        elif fileExtension == '.csv':
            data = pd.read_csv(data_path)
        else: 
            raise RuntimeError('Data file has unknown file extension: {}'.format(fileExtension))

        print 'Rows: {}'.format(len(data))
        print 'Columns: {}'.format(data.columns.values)
        # print data.head()

        return data

    def save_top_ohws(self, prefix='output'):
        output_dir = os.path.dirname(os.path.realpath(__file__)) + '/csv'

        # if output directory doesn't exist, make it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        output_file = '{0}/{1} {2}.csv'.format(output_dir, prefix, datetime.datetime.now().strftime("%Y-%m-%d %H,%M,%S"))
        f = open(output_file, 'w')

        artist_scores = ArtistScore.select('all', orderBy='score desc', limit=10)

        for artist_score in artist_scores:
            output = '{0},{1},{2}'.format(artist_score.artist, artist_score.track, artist_score.score)
            # print output
            f.write('{0}\n'.format(output))

        print 'Top One Hit Wonders saved to: {}'.format(output_file)

        return None

if __name__ == '__main__':
    ohw = OneHitWonders()
    ohw.rank_artists()
    ohw.save_top_ohws()
