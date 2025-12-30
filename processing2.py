import musicbrainzngs

musicbrainzngs.set_useragent('globify', version='v1', contact=None)

def getCountry(id):
    result = musicbrainzngs.get_area_by_id(id, includes=['area-rels'])['area']

    if result['type'] == 'Country':
        return result['name']
    elif 'iso-3166-2-code-list' in result:
        return result['iso-3166-2-code-list'][0][:2]
    else:
        for area in result['area-relation-list']:
            if area['type'] == 'part of' and area['direction'] == 'backward':
                return getCountry(area['area']['id'])
    
    return 'Unknown'
            
print(getCountry("29a709d8-0320-493e-8d0c-f2c386662b7f"))

def process_artists(initial):
    musicbrainzngs.set_useragent('globify', version='v1', contact=None)
    artists = []
    for artist in initial['items']: 
        name = artist['name']
        artists.append(name)
    
    data = []

    for name in artists: 
        try:
            artist = musicbrainzngs.search_artists(query= name, artist = name, limit = 1, strict=False)['artist-list'][0]
         
        except:
            add_artist(name, 'Unknown', data)
        else:
            if 'country' in artist:
                add_artist(artist['name'], artist['country'], data)
            else:
                if 'area' in artist:
                    add_artist(artist['name'], getCountry(artist['area']['id']), data)
                elif 'begin-area' in artist:
                    add_artist(artist['name'], getCountry(artist['begin-area']['id']), data)
                elif 'end-area' in artist:
                    add_artist(artist['name'], getCountry(artist['end-area']['id']), data)
                else: 
                    add_artist(artist['name'], 'Unknown', data)

    return data 

def add_artist(artist, country, data):
    for value in data:
        if country == value[0]:
            value[1] += 1
            value[2].append(artist)
            return None
    data.append([country, 1, [artist]])
    return None

test_input = {
    'items': [
        {'name': 'Queen'},
    ]
}

# Call the function
result = process_artists(test_input)
print(result)