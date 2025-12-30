import musicbrainzngs
import sqlite3
import country_converter as coco
import math
from countryinfo import CountryInfo

conn = sqlite3.connect('artist.db')

c = conn.cursor()

def diversity_calc(map_data):
    nums = []

    for key, value in map_data.items():
        if key != "Unknown":
            nums.append(value[0]) 

    total = sum(nums)

    probs = [num / total for num in nums]

    H = -sum(p*math.log2(p) for p in probs if p > 0)

    k = len(nums)
    H_norm = H / math.log2(k) if k > 1 else 0

    return round(H_norm, 3)


    


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
    if country not in data:
        data[country] = [0, []]
    
    data[country][0]+= 1
    data[country][1].append(artist)
    return None

def process_artists(initial):
    
    conn = sqlite3.connect('artist.db')
    c = conn.cursor()
    
    data = [] 
    #0 = map data
    #1 = topFiveList
    #2 = lowest popularity
    #3 = lowest population
    #4 = list of countries

    musicbrainzngs.set_useragent('globify', version='v1', contact=None)
    
    artists_data = [{'name': a['name'], 'spotify_id': a['id'], 'popularity': a["popularity"]} for a in initial['items']]


    map_data = {}

    for i, entry in enumerate(artists_data): 
        name = entry['name']
        spotify_id = entry['spotify_id']
        
        
        c.execute("SELECT * FROM artists WHERE id = ?", (spotify_id,))
        lookup = c.fetchone()

        if lookup:
            add_artist(name, lookup[2], map_data)
            artists_data[i].update({"country": lookup[2]})
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

            artists_data[i].update({"country": found_country})
            add_artist(name, found_country, map_data)
            c.execute("INSERT OR IGNORE INTO artists VALUES (?, ?, ?)", (spotify_id, name, found_country))
            conn.commit() 
        

    top_5 = artists_data[0:4]
    lowest_popularity = min(artists_data, key=lambda a: a["popularity"])
    iso2 = list(map_data.keys())
    country_names = coco.convert(names=iso2, to='name_short')
    lowest_population = country_names[0]

    for i in country_names:
        if country_names != 'not found':
            try:
                if CountryInfo(i).population() < CountryInfo(lowest_population).population():
                    lowest_population = i
            except:
                lowest_population = lowest_population

    conn.close()
    return [map_data, top_5, lowest_popularity, lowest_population, country_names, diversity_calc(map_data)] 


    #0 = map data
    #1 = topFiveList
    #2 = lowest popularity
    #3 = lowest population
    #4 = list of countries
    #5 = diversity
