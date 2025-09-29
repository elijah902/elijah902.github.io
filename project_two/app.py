import spotipy
import os
from flask import Flask, redirect, request, session, url_for, jsonify
from spotipy.oauth2 import SpotifyOAuth


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key-for-development')
app.config['SESSION_COOKIE_NAME'] = 'spotify-login'

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPE = "user-library-read user-read-private user-read-email user-top-read"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID, 
    client_secret=CLIENT_SECRET, 
    redirect_uri=REDIRECT_URI, 
    scope=SCOPE
)

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info  
    return token_info['access_token']

@app.route('/')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return f'<a href="{auth_url}">Login with Spotify</a>'

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    print(token_info['scope'])
    session['token_info'] = token_info
    return redirect(url_for('me'))

@app.route('/me')
def me():
    token = get_token()
    if not token:
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token)

    user = sp.current_user()
    
    playlist_ids = ['37i9dQZF1DX0XUsuxWHRQd']
    
    data = []
    for playlist_id in playlist_ids:
        try: 
            tracks = sp.playlist_tracks(playlist_id)
            for item in tracks.get('items', []):
                track = item.get('track')
                if not track or not track.get('id'):
                    continue

                try:
                    features = sp.audio_features([track['id']])[0]
                    if features is not None:
                        data.append({
                            "track": track['name'],
                            "artist": track['artists'][0]['name'],
                            "danceability": features['danceability']
                        })
                except Exception as e:
                    artist_name = track['artists'][0]['name'] if track.get('artists') and track['artists'] else 'Unknown Artist'
                    print(f"Skipping track {track['name']} by {artist_name}: {e}")
                    continue
        except Exception as e:
            print(f"Skipping playlist {playlist_id}: {e}")
            continue
    return jsonify(user=user['display_name'], tracks=data)
