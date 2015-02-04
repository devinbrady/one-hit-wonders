from one_hit_wonders import OneHitWonders

if __name__ == '__main__':
    ohw = OneHitWonders()

    for _ in range(333):
        artist = ohw.random_artist()
        if artist:
            print "Storing " + artist["name"]
            ohw.calculate_and_store(artist)

    ohw.get_top_ohws()
