import musicbrainzngs
import sqlite3

conn = sqlite3.connect('artist.db')

c = conn.cursor()


def get_country(id): #this gets the country given an area ID
    result = musicbrainzngs.get_area_by_id(id, includes=['area-rels'])['area']

    if 'iso-3166-2-code-list' in result:
        return result['iso-3166-2-code-list'][0][:2]
    elif result['type'] == 'Country':
        return result['name']
    else:
        for area in result['area-relation-list']:
            if area['type'] == 'part of' and area['direction'] == 'backward':
                return get_country(area['area']['id'])

    return 'Unknown'


def add_artist(artist, country, data):
    for value in data:
        if country == value[0]:
            value[1] += 1
            value[2].append(artist)
            return None
    data.append([country, 1, [artist]])
    return None

def process_artists(initial):
    # Connect locally (Thread Safe for Flask)
    conn = sqlite3.connect('artist.db')
    c = conn.cursor()
    
    musicbrainzngs.set_useragent('globify', version='v1', contact=None)
    
    artists_data = [{'name': a['name'], 'spotify_id': a['id']} for a in initial['items']]
    data = []

    for entry in artists_data: 
        name = entry['name']
        spotify_id = entry['spotify_id']
        
        # A. Check Local Database
        c.execute("SELECT * FROM artists WHERE id = ?", (spotify_id,))
        lookup = c.fetchone()

        if lookup:
            # Found in DB! Use the cached country.
            add_artist(name, lookup[2], data)
        else:
            # B. Not in DB - Search MusicBrainz
            found_country = 'Unknown' # Default value
            
            try:
                mb_result = musicbrainzngs.search_artists(query=name, artist=name, limit=1, strict=False)
                mb_artist = mb_result['artist-list'][0]
                
                # Determine Country
                if 'country' in mb_artist:
                    found_country = mb_artist['country']
                elif 'area' in mb_artist:
                    found_country = get_country(mb_artist['area']['id'])
                elif 'begin-area' in mb_artist:
                    found_country = get_country(mb_artist['begin-area']['id'])
                elif 'end-area' in mb_artist:
                    found_country = get_country(mb_artist['end-area']['id'])
                    
            except (IndexError, KeyError, musicbrainzngs.WebServiceError):
                # If search fails or no artist found, stays 'Unknown'
                pass

            # C. Add to Data and Save to DB (Done ONCE)
            add_artist(name, found_country, data)
            c.execute("INSERT OR IGNORE INTO artists VALUES (?, ?, ?)", (spotify_id, name, found_country))
            conn.commit() # Save the new artist

    conn.close()
    return data