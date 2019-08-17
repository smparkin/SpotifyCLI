import requests
import json as jsn
import urllib.request
import numpy as np
import imgcat
from PIL import Image
import sys

'''
NP: now playing
SE: search
SF: shuffle
PR: previous
NE: next
PP: play/pause
LS: add to liked songs
PA: playlist add

create file called secrets in same folder as spot.py with app token on line 1 and refresh token on line 2
'''

def main():
    try:
        arg = sys.argv[1]
    except:
        arg = input("NP: now playing\nSE: search\nSF: shuffle\nPR: previous\nNE: next\nPP: play/pause\nLS: add to liked songs\nPA: playlist add\nChoose one: ")
    if arg == "NP":
        spotNP()
    elif arg == "SE":
        spotSE()
    elif arg == "SF":
        spotSF()
    elif arg == "PR":
        spotPR()
    elif arg == "NE":
        spotNE()
    elif arg == "PP":
        spotPP()
    elif arg == "LS":
        spotLS()
    elif arg == "PA":
        spotPA()
    else:
        print("Only use: NP, SE, SF, PR, NE, PP, LS, PA")
        quit()

def spotAuth():
    f = open(sys.path[0]+"/secrets", "r")
    appToken = f.readline()[:-1]
    refreshToken = f.readline()[:-1]
    tokenURL = "https://accounts.spotify.com/api/token"

    headers = {"Authorization": "Basic "+appToken}
    payload = {"grant_type": "refresh_token", "refresh_token": refreshToken}
    r = requests.post(tokenURL, headers=headers, data=payload)

    json = r.json()
    accessToken = json["access_token"]
    return accessToken

def spotNP():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("Nothing playing")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()

    title = json["item"]["name"]
    artist = json["item"]["album"]["artists"][0]["name"]
    imgurl = json["item"]["album"]["images"][1]["url"]
    durationSec = (json["item"]["duration_ms"])/1000
    currentSec = (json["progress_ms"])/1000
    print("Now Playing:")
    print("\033[95m\033[1m"+title+"\033[0m")
    print("\033[94m\033[1m"+artist+"\033[0m")
    im = np.asarray(Image.open(urllib.request.urlopen(imgurl)))
    imgcat.imgcat(im)
    print(str(round(currentSec//60))+":"+(str(round(currentSec%60))).zfill(2)+"/"+str(round(durationSec//60))+":"+(str(round(durationSec%60)).zfill(2)))
    return r.status_code

def spotSE():
    accessToken = spotAuth()
    query = ""
    if len(sys.argv) > 2:
        for i in range(2, len(sys.argv)):
            query = query+" "+sys.argv[i]
    else:
        query = input("Search for: ")
    query.replace(" ", "%20")
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/search?q="+query+"&type=track", headers=headers)
    if r.status_code == 204:
        print("No results")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()
    try:
        trackuri = json["tracks"]["items"][0]["uri"]
        trackname = json["tracks"]["items"][0]["name"]
    except:
        print("Search returned no results")
        quit()

    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    try:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
    except:
        print("No playback device found")
        quit()

    payload = {"uris": [trackuri]}
    r = requests.put("https://api.spotify.com/v1/me/player/play?device_id="+deviceid, headers=headers, data=jsn.dumps(payload))
    if r.status_code == 204:
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+devicename+"\033[0m.")
    else:
        print("Unable to play \033[1m\033[95m"+trackname+"\033[0m.")
    return r.status_code

def spotSF():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("No active playback session")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()

    r = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    json = r.json()
    shuf = json["shuffle_state"]
    if shuf == True:
        shuf = "false"
    elif shuf == False:
        shuf = "true"

    r = requests.put("https://api.spotify.com/v1/me/player/shuffle?state="+shuf, headers=headers)
    if r.status_code == 204:
        r = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
        json = r.json()
        curshuf = json["shuffle_state"]
        if curshuf == True:
            print("Enabled shuffle.")
        else:
            print("Disabled shuffle.")
    else:
        print("Unable to toggle shuffle.")
    return r.status_code

def spotPR():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("No active playback session")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()
    trackname = json["item"]["name"]
    trackid = json["item"]["id"]

    r = requests.post("https://api.spotify.com/v1/me/player/previous", headers=headers)
    if r.status_code == 204:
        r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
        json = r.json()
        trackname = json["item"]["name"]
        print("Playing \033[1m\033[95m"+trackname+"\033[0m.")
    else:
        print("Unable to go to previous track.")
    return r.status_code

def spotNE():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("No active playback session")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()
    trackname = json["item"]["name"]
    trackid = json["item"]["id"]

    r = requests.post("https://api.spotify.com/v1/me/player/next", headers=headers)
    if r.status_code == 204:
        r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
        json = r.json()
        trackname = json["item"]["name"]
        print("Playing \033[1m\033[95m"+trackname+"\033[0m.")
    else:
        print("Unable to skip track.")
    return r.status_code

def spotPP():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("No active playback session")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()
    trackname = json["item"]["name"]
    trackid = json["item"]["id"]

    r = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    json = r.json()
    playing = json["is_playing"]

    if playing == False:
        r = requests.put("https://api.spotify.com/v1/me/player/play", headers=headers)
        if r.status_code == 204:
            print("Playing \033[1m\033[95m"+trackname+"\033[0m.")
        else:
            print("No active devices")
    elif playing == True:
        r = requests.put("https://api.spotify.com/v1/me/player/pause", headers=headers)
        if r.status_code == 204:
            print("Paused \033[1m\033[95m"+trackname+"\033[0m.")
        else:
            print("No active devices")
    return r.status_code

def spotLS():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("Nothing playing")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()
    trackname = json["item"]["name"]
    trackid = json["item"]["id"]

    headers = {"Authorization": "Bearer "+accessToken, "Accept": "application/json", "Content-Type": "application/json"}
    r = requests.put("https://api.spotify.com/v1/me/tracks?ids="+trackid, headers=headers)
    if r.status_code == 200:
        print("Added \033[1m\033[95m"+json["item"]["name"]+"\033[0m to Liked Songs")
    else:
        print("An error occured, fun")
    return r.status_code

def spotPA():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("Nothing playing")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()
    print("Add \033[1m\033[95m"+json["item"]["name"]+"\033[0m to:")
    trackname = json["item"]["name"]
    trackuri = json["item"]["uri"]
    trackuri.replace(":", "%3A")

    r = requests.get("https://api.spotify.com/v1/me", headers=headers)
    json = r.json()
    userid = json["id"]

    r = requests.get(playlistURL+"?limit=50", headers=headers)
    json = r.json()
    j = 0
    for i in json["items"]:
        if userid == i["owner"]["display_name"]:
            print("["+str(j)+"] "+i["name"])
            j += 1
        elif i["collaborative"] == True:
            print("["+str(j)+"] "+i["name"])
            j += 1
    choice = input("Select Playlist: ")
    try:
        choice = int(choice)
    except:
        quit()
    playlistid = json["items"][choice]["id"]
    playlistname = json["items"][choice]["name"]

    headers = {"Authorization": "Bearer "+accessToken, "Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post("https://api.spotify.com/v1/playlists/"+playlistid+"/tracks?uris="+trackuri, headers=headers)
    if r.status_code == 201:
        print("Successfully added \033[1m\033[95m"+trackname+"\033[0m to \033[1m\033[96m"+playlistname+"\033[0m")
    else:
        print("Unable to add song to specified playlist. Do you have access to do so?")
    return r.status_code

if __name__ == "__main__":
    main()
