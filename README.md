# S2YM
Spotify 2 Youtube Music Converter Tool

Welcome to my Spotify to Youtube Music converter! As someone who was paying for both Spotify and Youtube Premium, I finally decided to take the leap to the included Youtube Music platform. There are some tools that you can use online to accomplish what I'm doing here, but I thought it'd be fun to treat this as a mini-project for myself. Make sure to follow the below steps carefully.

**Prerequisites**
1. Python (3.4 or later)
2. spotipy library
3. ytmusicapi library
* Run **pip install {library_name}** to install any required Python libraries

**Procedure**

A. Access the Spotify API
1. Create a Spotify for Developers account at https://developer.spotify.com/
2. Once logged in, go to your Dashboard
3. Click on the Create an app button and fill in the following fields:
   a. App Name (anything)
   b. App Description (anything)
   c. Redirect URI: enter http://127.0.0.1:8888/callback
4. Check the Developer Terms of Service checkbox and tap on the Create button
5. Go to the Dashboard
6. Click on the name of the app you have just created
7. Click on the Settings button
8. Obtain your client_id and client_secret, we will need them soon

B. Access the Youtube Music API
1. Go to music.youtube.com in your browser (Firefox highly recommended)
2. If not already, log in to your account
3. Press Ctrl+Shift+I to open Developer Tools window
4. Click on the Network Tab
5. Refresh your webpage
6. Look for any POST request
7. Verify that the request looks like such:
  a. Status 200
  b. Method POST
  c. Domain music.youtube.com
  d. File browse?... (get_search_suggestions?prettyPrint=false always works for me)
8. Copy the request headers (right click > copy > copy request headers)
9. Open a console window (Git Bash recommended)
10. Enter **ytmusicapi browser**
11. Paste in the copied request headers
12. Press Enter, Ctrl+Z, Enter
13. Verify that a "browser.json" file was created in your current directory.
14. Copy that created file to the same folder as the spotify2ym.py script

C. Run the Script
1. From a console window, navigate to the spotify2ym directory
2. Enter **python spotify2ym.py**
3. When prompted, paste in your Spotify Client ID and press Enter
4. Paste in your Spotify Client Secret
5. Press Enter to use default redirect URI
6. If ytmusicapi verification fails, delete browser.json and re-run procedure B.
7. Press 1 and Enter to export liked Spotify songs to JSON file
8. Press 2 and Enter to sync liked songs from Spotify to Youtube Music
9. Press 6 to stop the program. 


