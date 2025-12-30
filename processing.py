import musicbrainzngs
import sqlite3

conn = sqlite3.connect('artist.db')

c = conn.cursor()


def get_country(id): 
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
    try:
        data.update({{country}: data[country]+1})
    except:
        data.update({country: 1})
    return None

def process_artists(initial):
    
    conn = sqlite3.connect('artist.db')
    c = conn.cursor()
    
    musicbrainzngs.set_useragent('globify', version='v1', contact=None)
    
    artists_data = [{'name': a['name'], 'spotify_id': a['id'], 'popularity': a["popularity"]} for a in initial['items']]
    
    lowest_popularity = min(artists_data, key=lambda a: a["popularity"])

    map_data = {}

    for entry in artists_data: 
        name = entry['name']
        spotify_id = entry['spotify_id']
        
        
        c.execute("SELECT * FROM artists WHERE id = ?", (spotify_id,))
        lookup = c.fetchone()

        if lookup:
            add_artist(name, lookup[2], map_data)
        else:
            
            found_country = 'Unknown' 
            
            try:
                mb_result = musicbrainzngs.search_artists(query=name, artist=name, limit=1, strict=False)
                mb_artist = mb_result['artist-list'][0]
                
                if 'country' in mb_artist:
                    found_country = mb_artist['country']
                elif 'area' in mb_artist:
                    found_country = get_country(mb_artist['area']['id'])
                elif 'begin-area' in mb_artist:
                    found_country = get_country(mb_artist['begin-area']['id'])
                elif 'end-area' in mb_artist:
                    found_country = get_country(mb_artist['end-area']['id'])
                    
            except (IndexError, KeyError, musicbrainzngs.WebServiceError):
                pass

            
            add_artist(name, found_country, map_data)
            c.execute("INSERT OR IGNORE INTO artists VALUES (?, ?, ?)", (spotify_id, name, found_country))
            conn.commit() 

    conn.close()
    return map_data