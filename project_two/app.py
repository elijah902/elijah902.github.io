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
SCOPE = "user-library-read user-read-private user-read-email"

sp_oauth = SpotifyOAuth(
    client_id=CLIENT_ID, 
    client_secret=CLIENT_SECRET, 
    redirect_uri=REDIRECT_URI, 
    scope=SCOPE
)

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
    token_info = session.get('token_info')
    if not token_info:
        return redirect("/")
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    user = sp.current_user()
    playlists = sp.current_user_playlists(limit=10)

    data = []
    for playlist in playlists.get('items', []):
        try:
            if not playlist or not playlist.get('id'):
                continue 
            
            tracks = sp.playlist_tracks(playlist['id'])
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
                            "danceability": features['danceability'],
                            "energy": features['energy'],
                            "tempo": features['tempo'],
                            "valence": features['valence']
                        })
                except Exception as e:
                    artist_name = track['artists'][0]['name'] if track.get('artists') and track['artists'] else 'Unknown Artist'
                    print(f"Skipping track {track['name']} by {artist_name}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Skipping playlist {playlist.get('name') if playlist else 'Unknown'}: {e}")
            continue
        
    
    return jsonify(user=user['display_name'], tracks=data)
