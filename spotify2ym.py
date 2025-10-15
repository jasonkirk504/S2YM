#!/usr/bin/env python3
import os
import sys
import json
import logging

from dotenv import load_dotenv
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from pathlib import Path 

#Enable logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def export_liked_songs_to_json(sp_client, platform="spotify", filename="liked_songs.json", limit=50):
    if platform != "spotify":
        logging.info("Chose a platform other than Spotify...must handle later")
        return 
    liked_songs = []
    offset = 0

    while True:
        results = sp_client.current_user_saved_tracks(limit=limit, offset=offset)
        items = results.get('items', [])
        if not items:
            break

        for item in items:
            track = item['track']
            liked_songs.append({
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'album': track['album']['name'],
                'release_date': track['album']['release_date'],
                'spotify_url': track['external_urls']['spotify']
            })
        
        offset += limit
        logging.info(f"Fetched {len(liked_songs)} liked songs so far...")

    #Save to JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(liked_songs, f, indent=2, ensure_ascii=False)

    logging.info(f"Exported {len(liked_songs)} liked songs to {filename}")
        
def get_liked_song_count(filepath="liked_songs.json"):
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            return len(data) if isinstance(data, list) else 0
    except Exception as e:
        print(f"Error reading liked songs: {e}")
        return 0

def sync_liked_songs(yt_client, json_path="liked_songs.json"):
    logging.info("Starting sync from Spotify to Youtube Music...") 

    if not os.path.exists(json_path):
        logging.error(f"JSON file '{json_path}' not found. Please export liked songs first.")
        return
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            liked_songs = json.load(f)
    except Exception as e:
        logging.error(f"Failed to read JSON file: {e}")
        return 

    matched_songs = []

    for i, song in enumerate(liked_songs, start=1):
        query = f"{song['name']} {' '.join(song['artists'])}"
        logging.info(f"[{i}/{len(liked_songs)}] Searching YouTube Music for: {query}")
        search_results = yt_client.search(query, filter="songs")

        if search_results:
            top_result = search_results[0]
            matched_songs.append({
                'spotify_name': song['name'],
                'spotify_artists': ', '.join(song['artists']),
                'ytmusic_title': top_result.get('title'),
                'ytmusic_artists': ', '.join([a['name'] for a in top_result.get('artists', [])]),
                'ytmusic_videoId': top_result.get('videoId')
            })
        else:
            matched_songs.append({
                'spotify_name': song['name'],
                'spotify_artists': ', '.join(song['artists']),
                'ytmusic_title': None,
                'ytmusic_artists': None,
                'ytmusic_videoId': None
            })

    logging.info(f"Matched {len([m for m in matched_songs if m['ytmusic_videoId']])} out of {len(liked_songs)} songs.")

    logging.info("Getting Liked songs from Youtube Music to avoid unnecessary API calls...")
    liked_yt_songs = yt_client.get_liked_songs(limit=1600)  # You can increase limit if needed
    already_liked_ids = {song['videoId'] for song in liked_yt_songs['tracks'] if 'videoId' in song}
    
    #Print or log the matched song
    for match in matched_songs:
        video_id = match.get('ytmusic_videoId')
        if not video_id:
            spotify_artists = match.get('spotify_artists', 'Unknown Artist')
            logging.warning(f"Could not find a match for: {match['spotify_name']} by {spotify_artists}")
            continue
        if video_id in already_liked_ids:
            logging.info(f"Already liked {match['ytmusic_title']} by {match['ytmusic_artists']}")
            continue 

        yt_client.rate_song(video_id, 'LIKE')
        logging.info(f"Liked on Youtube Music: {match['ytmusic_title']} by {match['ytmusic_artists']}")

    logging.info("Sync complete...")

def create_playlist(name):
    logging.info(f"Creating new Youtube Music playlist: {name}...")
    # TODO: Create playlist via Youtube API
    logging.info("Playlist created...")

def get_spotify_client(auth_manager):
    return Spotify(auth_manager=auth_manager)

def test_ytmusicapi():
    ytmusic = YTMusic("browser.json")
    try:
        liked_songs = ytmusic.get_liked_songs(limit=1)
        print("\nSESSION IS VALID")
    except Exception as e:
        print("\nSESSION MIGHT BE EXPIRED :(")
        print(e)

def test_spotifyapi(client_id, client_secret, redirect_uri, scope="user-read-private", suppress=False):
    """
    Tests whether the provided Spotify credentials are valid by attempting to authenticate
    and fetch the current user's profile.

    Returns:
        bool: True if credentials are valid, False otherwise.
    """
    try:
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=scope,
            open_browser=True
        )
        sp = Spotify(auth_manager=auth_manager)
        user = sp.current_user()
        if not suppress:
            print(f"\n✅ Authenticated as: {user['display_name']} ({user['id']})")
        return auth_manager
    except Exception as e:
        if not suppress:
            print("❌ Failed to initiate OAuth flow. Likely due to invalid credentials.")
            print(f"Error: {e}")
        return None 

def main_menu():
    song_count = get_liked_song_count()
    print("\n🎵 Spotify to Youtube Music Sync Tool")
    print("\n**First export liked Spotify songs to JSON then sync.**")
    print(f"** {song_count} liked songs found in JSON file **")       
    print("\n\t1. Export Spotify Liked Songs to JSON")
    print("\t2. Sync liked songs from Spotify to Youtube Music")
    print("\t3. Create a new YouTube Music playlist")
    print("\t4. Test YTMusic API")
    print("\t5. Test Spotify API")
    print("\t6. Exit")

def setup_wizard():
    print("Welcome to the Spotify to Youtube Music Setup Wizard")

    client_id = input("Enter your Spotify Client ID: ").strip()
    client_secret = input("Enter your Spotify Client Secret: ").strip()
    redirect_uri = input("Enter your Redirect URI (default: http://127.0.0.1:8888/callback): ").strip()
    if not redirect_uri:
        redirect_uri = "http://127.0.0.1:8888/callback"

    print("\n🔍 Testing credentials...")
    auth_manager = test_spotifyapi(client_id, client_secret, redirect_uri)
    if not auth_manager:
        print("⚠️ Setup aborted. Please check your credentials and try again.")
        return None, None, None, None, None

    with open(".env", "w") as f:
        f.write(f"SPOTIPY_CLIENT_ID={client_id}\n")
        f.write(f"SPOTIPY_CLIENT_SECRET={client_secret}\n")
        f.write(f"SPOTIPY_REDIRECT_URI={redirect_uri}\n")

    from dotenv import load_dotenv
    load_dotenv()

    sp_client = Spotify(auth_manager=auth_manager)
    return client_id, client_secret, redirect_uri, auth_manager, sp_client
    

def spotify_sanity_check():
    # Load environment variables once at the start
    load_dotenv() 

    client_id = os.getenv("SPOTIPY_CLIENT_ID")
    client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI")
    
    auth_manager = None
    sp_client = None

    if not client_id or not client_secret or not redirect_uri:
        logging.warning("Spotify credentials missing in .env file. Starting setup wizard...")
        client_id, client_secret, redirect_uri, auth_manager, sp_client = setup_wizard()
        # If the wizard failed, auth_manager will be None, and the program should exit or warn.
    
    # If credentials were loaded from .env, or the wizard just ran successfully
    while not auth_manager: # Only run the loop if we still need to authenticate
        
        # 1. Attempt to validate credentials
        auth_manager = test_spotifyapi(client_id, client_secret, redirect_uri, suppress=True)

        if auth_manager:
            sp_client = Spotify(auth_manager=auth_manager)
            print(f"\n✅ Authenticated as: {sp_client.current_user()['display_name']}")
            break
        else:
            # If loaded credentials are BAD (expired token, etc.), THEN run the wizard
            logging.warning("Spotify credentials expired or invalid. Starting setup wizard...")
            clear_spotify_cache()

            # Run setup_wizard to get new credentials and update the environment
            client_id, client_secret, redirect_uri, auth_manager, sp_client = setup_wizard()

    # Return the final, successfully authenticated data
    return client_id, client_secret, redirect_uri, auth_manager, sp_client

def ytmusic_sanity_check(filepath="browser.json"):
    """
    Checks if the YT Music authentication file exists. 
    If not, it prompts the user to create it.
    """
    if Path(filepath).exists():
        logging.info("✅ Found existing YT Music authentication file.")
        try:
            #Attempt to initialize and test
            yt_client = YTMusic(filepath)
            #Test if session is still valid
            yt_client.get_liked_songs(limit=1)
            logging.info("✅ Session is valid")
            return yt_client
        except Exception as e:
            logging.error(f"❌ YT Music session expired or invalid: {e}")
            #Fall through to the setup prompt
            pass
    
    # --- Setup Instructions ---
    logging.warning("⚠️ YT Music authentication file not found or invalid.")
    print("\n--- YOUTUBE MUSIC SETUP ---")
    print(f"The required authentication file ({filepath}) is missing or invalid.")
    print("Please follow the official setup process to create the file.")
    print("1. Install ytmusicapi if you haven't: pip install ytmusicapi")
    print("2. Run the command to start the interactive setup:")
    print("   ytmusicapi browser")
    print("3. Copy the resulting JSON file into your script's directory.")
        
    sys.exit(1)

    
    

def clear_spotify_cache(username=None):
    cache_path = f".cache-{username}" if username else ".cache"
    if os.path.exists(cache_path):
        os.remove(cache_path)
        logging.info(f"🧹 Cleared Spotify cache: {cache_path}")

def main():
    #Load env variables
    load_dotenv()

    # 1. Handle Spotify authentication
    client_id, client_secret, redirect_uri, auth_manager, sp_client = spotify_sanity_check()
    # 2. Handle YTMusic authentication
    yt_client =  ytmusic_sanity_check()
    
    # 3. Continue to menu
    while True:
        main_menu()
        selection = input("\nSelect an option (1-6): ").strip()

        if selection == "1":
            export_liked_songs_to_json(sp_client)
        elif selection == "2":
            sync_liked_songs(yt_client)
        elif selection == "3":
            clear_spotify_cache()
            logging.info("Selection 3 not yet implemented...")
        elif selection == "4":
            test_ytmusicapi()
        elif selection == "5":
            test_spotifyapi(client_id, client_secret, redirect_uri)
        elif selection == "6":
            print("See You Space Cowboy...")
            break
        else:
            print("\nInvalid selection. Please select a valid option (1-5)")

if __name__ == "__main__":
    main()