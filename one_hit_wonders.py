#!/usr/bin/env python


import httplib
import sys
from BeautifulSoup import BeautifulSoup
import os
import datetime
import re
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

def main():

    country_code = 'US'

    # if True, will print the top tracks for each artist
    print_all_tracks = False
    
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
        
        artist_id = get_artist_id(band)

        top_tracks = get_top_tracks(artist_id, country_code)
        
        score, top_track_name = calculate_score(top_tracks, print_all_tracks)
        
        print 'One Hit Wonder Score: {0:.0f}'.format(score)

        data_row = pd.DataFrame({
            "Artist": band,
            "Top Track": top_track_name,
            "OHW Score": score
        }, index=[i])

        # print data_row

        df = df.append(data_row)

    
    df = df.sort(columns='OHW Score', ascending=False)
    
    save_dataframe(df, 'ohw score')

    return None

    


def get_artist_id(artist_name):

    artist_name_url = artist_name.lower().replace(' ','%20')
    
    results = query_spotify("/v1/search?q={}&type=artist".format(artist_name_url))

    # at some point, confirm that we got exactly 1 result

    artist_id = results['artists']['items'][0]['id']

    return artist_id


def get_top_tracks(artist_id, country_code):

    results = query_spotify("/v1/artists/{0}/top-tracks?country={1}".format(artist_id, country_code))

    return results['tracks']


def query_spotify(url):

    conn = httplib.HTTPSConnection('api.spotify.com')
    
    conn.request('GET', url)

    r1 = conn.getresponse()

    # if HTML status isn't 200, throw error
    if r1.status != 200:
        error_str = 'Bad HTML status from Spotify: {0} {1}'.format(r1.status, r1.reason)
        raise RuntimeError(error_str)

    body = r1.read()
    
    if body[0:6] == '<html>':

        parsed_html = BeautifulSoup(body)
        html_error = parsed_html.body.find('h1').text

        error_str = 'Bad API response from Spotify ({}), probably an error in the API query.'.format(html_error)
        raise RuntimeError(error_str)

    results = json.loads(body)

    return results


def calculate_score(top_tracks, print_all_tracks=False):

    sorted_tracks = sorted(top_tracks, key=lambda x: x['popularity'], reverse=True)

    top_track_name = sorted_tracks[0]['name']

    top_tracks_popularity = [sorted_tracks[0]['popularity']]

    for i, track in enumerate(sorted_tracks): 
        if print_all_tracks: 
            print '{0}. ({1}) {2}'.format(i+1, track['popularity'], track['name'])

        if i != 0: 
            if top_track_name not in track['name']: 
                top_tracks_popularity.append(track['popularity'])
            elif print_all_tracks: 
                print '^^^^^^^ duplicate of top hit, will exclude'
    
        
    if not print_all_tracks:     
        print 'Top Hit: {}'.format(sorted_tracks[0]['name'])

    score = top_tracks_popularity[0] - np.mean(top_tracks_popularity[1:len(top_tracks_popularity)])

    return score, top_track_name


def save_dataframe(df, prefix='output'):

    output_dir = os.path.dirname(os.path.realpath(__file__)) + '/csv'

    # if output directory doesn't exist, make it
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    output_file = '{0}/{1} {2}.csv'.format(output_dir, prefix, datetime.datetime.now().strftime("%Y-%m-%d %H,%M,%S"))
    
    df.to_csv(output_file)

    print 'DataFrame saved to: {}'.format(output_file)

    return None


if __name__ == '__main__':
    main()