from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, redirect, session, url_for, render_template
import processing
import os

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)


scope = "user-top-read user-read-recently-played"

cache_handler = FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth(
    client_id= os.environ["CLIENT_ID"],
    client_secret=os.environ["CLIENT_SECRET"],
    redirect_uri=os.environ["REDIRECT_URI"],
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)


def get_spotify_client():
    # Return a Spotify client for the current user session, refreshing token if needed.
    token_info = cache_handler.get_cached_token()
    if not token_info:
        return None
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        cache_handler.save_token_to_cache(token_info)
    return Spotify(auth=token_info['access_token'])

@app.route('/')
def home():
    return render_template("login.html")

@app.route("/", methods=['POST'])
def process_button():
    if request.method == 'POST':
        if request.form.get('login_button') == 'login':
            token_info = cache_handler.get_cached_token()
            if not sp_oauth.validate_token(token_info):
                auth_url = sp_oauth.get_authorize_url()
                return redirect(auth_url)
            return redirect(url_for('get_artists', time_range=request.form.get('time_dropdown')))


@app.route('/callback')
def callback():
     sp_oauth.get_access_token(request.args['code'])
     return redirect(url_for('get_artists'))

@app.route('/get_artists')
def get_artists():
    time_range = request.args.get('time_range', 'medium_term')
    sp = get_spotify_client()
    if not sp:
        return redirect(sp_oauth.get_authorize_url())

    artists = sp.current_user_top_artists(time_range=time_range, limit=30)
    data = processing.process_artists(artists)
    map_data = data[0]
    top_five = data[1]
    lowest_popularity = data[2]
    lowest_population = data[3]
    countries = data[4]
    diversity = data[5]

    print(data)

    return render_template("globe.html", map_data=map_data, top_five=top_five, lowest_popularity=lowest_popularity, countries=countries, diversity=diversity, lowest_population=lowest_population)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True, port=8000)