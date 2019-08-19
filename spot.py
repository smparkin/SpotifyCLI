import requests
import json as jsn
import urllib.request
import numpy as np
import imgcat
from PIL import Image
import sys
import time

'''
NP: now playing
SE: search
SF: shuffle
PR: previous
NE: next
PP: play/pause
LS: add to liked songs
AP: add to playlist
RP: remove from playlist
PD: change playback device
LP: play playlist from saved playlists
VL: volume

create file called secrets in same folder as spot.py with app token on line 1 and refresh token on line 2
'''

def main():
    try:
        arg = sys.argv[1]
    except:
        arg = input("NP: now playing\nSE: search\nSF: shuffle\nPR: previous\nNE: next\nPP: play/pause\nLS: add to liked songs\nAP: add to playlist\nRP: remove from playlist\nPD: change playback device\nLP: play playlist from saved playlists\nVL: volume\nChoose one: ")
    arg.upper()
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
    elif arg == "AP":
        spotAP()
    elif arg == "RP":
        spotRP()
    elif arg == "PD":
        spotPD()
    elif arg == "PL":
        spotPL()
    elif arg == "VL":
        spotVL()
    else:
        print("Only use: NP, SE, SF, PR, NE, PP, LS, AP, RP, PD, PL")
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

    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    for i in json["devices"]:
        if i["is_active"] == True:
            devicename = i["name"]

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
    print("Playing", end=' ')
    print("\033[95m\033[1m"+title+"\033[0m by ", end='')
    print("\033[94m\033[1m"+artist+"\033[0m on ", end='')
    print("\033[92m\033[1m"+devicename+"\033[0m")
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
    deviceid = None
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    if len(json["devices"]) == 1:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
    for i in json["devices"]:
        if i["is_active"] == True:
            deviceid = i["id"]
            devicename = i["name"]
    if deviceid == None:
        for i in range(0,len(json["devices"])):
            print("["+str(i)+"] "+json["devices"][i]["name"])
        choice = input("Choose device: ")
        try:
            choice = int(choice)
        except:
            quit()
        deviceid = json["devices"][choice]["id"]
        devicename = json["devices"][choice]["name"]

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

    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    deviceid = None
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    if len(json["devices"]) == 1:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
    for i in json["devices"]:
        if i["is_active"] == True:
            deviceid = i["id"]
            devicename = i["name"]
    if deviceid == None:
        for i in range(0,len(json["devices"])):
            print("["+str(i)+"] "+json["devices"][i]["name"])
        choice = input("Choose device: ")
        try:
            choice = int(choice)
        except:
            quit()
        deviceid = json["devices"][choice]["id"]
        devicename = json["devices"][choice]["name"]

    r = requests.post("https://api.spotify.com/v1/me/player/previous", headers=headers)
    if r.status_code == 204:
        time.sleep(0.5)
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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+devicename+"\033[0m.")
    else:
        print("Unable to play \033[1m\033[95m"+trackname+"\033[0m.")
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

    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    deviceid = None
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    if len(json["devices"]) == 1:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
    for i in json["devices"]:
        if i["is_active"] == True:
            deviceid = i["id"]
            devicename = i["name"]
    if deviceid == None:
        for i in range(0,len(json["devices"])):
            print("["+str(i)+"] "+json["devices"][i]["name"])
        choice = input("Choose device: ")
        try:
            choice = int(choice)
        except:
            quit()
        deviceid = json["devices"][choice]["id"]
        devicename = json["devices"][choice]["name"]

    r = requests.post("https://api.spotify.com/v1/me/player/next", headers=headers)
    if r.status_code == 204:
        time.sleep(0.5)
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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+devicename+"\033[0m.")
    else:
        print("Unable to play \033[1m\033[95m"+trackname+"\033[0m.")
    return r.status_code

def spotPP():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}

    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    deviceid = None
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    if len(json["devices"]) == 1:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
    for i in json["devices"]:
        if i["is_active"] == True:
            deviceid = i["id"]
            devicename = i["name"]
    if deviceid == None:
        for i in range(0,len(json["devices"])):
            print("["+str(i)+"] "+json["devices"][i]["name"])
        choice = input("Choose device: ")
        try:
            choice = int(choice)
        except:
            quit()
        deviceid = json["devices"][choice]["id"]
        devicename = json["devices"][choice]["name"]

    r = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    try:
        json = r.json()
        playing = json["is_playing"]
    except:
        playing = False

    if playing == False:
        r = requests.put("https://api.spotify.com/v1/me/player/play?device_id="+deviceid, headers=headers)
        if r.status_code == 204:
            time.sleep(0.5)
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
            print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+devicename+"\033[0m.")
        else:
            print("No active devices")
    elif playing == True:
        r = requests.put("https://api.spotify.com/v1/me/player/pause?device_id="+deviceid, headers=headers)
        if r.status_code == 204:
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
            print("Paused \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+devicename+"\033[0m.")
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

def spotAP():
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

    r = requests.get("https://api.spotify.com/v1/me/playlists?limit=50", headers=headers)
    json = r.json()
    j = 0
    playdict = {}
    for i in json["items"]:
        if userid == i["owner"]["display_name"]:
            print("["+str(j)+"] "+i["name"])
            playdict.update( {j: [i["name"], i["id"]]})
            j += 1
        elif i["collaborative"] == True:
            print("["+str(j)+"] "+i["name"])
            playdict.update( {j: [i["name"], i["id"]]})
            j += 1
    choice = input("Select Playlist: ")
    try:
        choice = int(choice)
    except:
        quit()
    playlistid = playdict[choice][1]
    playlistname = playdict[choice][0]

    headers = {"Authorization": "Bearer "+accessToken, "Accept": "application/json", "Content-Type": "application/json"}
    r = requests.post("https://api.spotify.com/v1/playlists/"+playlistid+"/tracks?uris="+trackuri, headers=headers)
    if r.status_code == 201:
        print("Successfully added \033[1m\033[95m"+trackname+"\033[0m to \033[1m\033[96m"+playlistname+"\033[0m")
    else:
        print("Unable to add song to specified playlist. Do you have access to do so?")
    return r.status_code

def spotPD():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}

    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    if len(json["devices"]) == 1:
        devicename = json["devices"][0]["name"]
        print("\033[1m\033[92m"+devicename+"\033[0m is only device.")
        quit()
    j = 0
    devicedict = {}
    for i in json["devices"]:
        if i["is_active"] == False:
            print("["+str(j)+"] "+i["name"])
            devicedict.update( {j: [i["name"], i["id"]]})
            j += 1
    choice = input("Choose device: ")
    try:
        choice = int(choice)
    except:
        quit()
    deviceid = devicedict[choice][1]
    devicename = devicedict[choice][0]

    payload = {"device_ids":[deviceid]}
    r = requests.put("https://api.spotify.com/v1/me/player", headers=headers, data=jsn.dumps(payload))
    if r.status_code == 204:
        time.sleep(0.5)
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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+devicename+"\033[0m.")
    else:
        print("Unable to transfer playback.")
    
def spotRP():
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
    print("Remove \033[1m\033[95m"+json["item"]["name"]+"\033[0m from:")
    trackname = json["item"]["name"]
    trackuri = json["item"]["uri"]

    r = requests.get("https://api.spotify.com/v1/me", headers=headers)
    json = r.json()
    userid = json["id"]

    r = requests.get("https://api.spotify.com/v1/me/playlists?limit=50", headers=headers)
    json = r.json()
    j = 0
    playdict = {}
    for i in json["items"]:
        if userid == i["owner"]["display_name"]:
            print("["+str(j)+"] "+i["name"])
            playdict.update( {j: [i["name"], i["id"]]})
            j += 1
        elif i["collaborative"] == True:
            print("["+str(j)+"] "+i["name"])
            playdict.update( {j: [i["name"], i["id"]]})
            j += 1
    choice = input("Select Playlist: ")
    try:
        choice = int(choice)
    except:
        quit()
    playlistid = playdict[choice][1]
    playlistname = playdict[choice][0]

    headers = {"Authorization": "Bearer "+accessToken, "Accept": "application/json", "Content-Type": "application/json"}
    payload = { "tracks": [{ "uri": trackuri }] }
    r = requests.delete("https://api.spotify.com/v1/playlists/"+playlistid+"/tracks", headers=headers, data=jsn.dumps(payload))
    if r.status_code == 200:
        print("If \033[1m\033[95m"+trackname+"\033[0m was in \033[1m\033[96m"+playlistname+"\033[0m it has been removed.")
    else:
        print("Unable to remove song from specified playlist. Do you have access to do so?")
    return r.status_code

def spotPL():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
    print("Play:")

    r = requests.get("https://api.spotify.com/v1/me/playlists?limit=50", headers=headers)
    json = r.json()
    j = 0
    playdict = {}
    for i in json["items"]:
        print("["+str(j)+"] "+i["name"])
        playdict.update( {j: [i["name"], i["id"]]})
        j += 1
    choice = input("Select Playlist: ")
    try:
        choice = int(choice)
    except:
        quit()
    playlistid = playdict[choice][1]
    playlistname = playdict[choice][0]

    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    deviceid = None
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    if len(json["devices"]) == 1:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
    for i in json["devices"]:
        if i["is_active"] == True:
            deviceid = i["id"]
            devicename = i["name"]
    if deviceid == None:
        for i in range(0,len(json["devices"])):
            print("["+str(i)+"] "+json["devices"][i]["name"])
        choice = input("Choose device: ")
        try:
            choice = int(choice)
        except:
            quit()
        deviceid = json["devices"][choice]["id"]
        devicename = json["devices"][choice]["name"]

    payload = {"context_uri": "spotify:playlist:"+playlistid}
    r = requests.put("https://api.spotify.com/v1/me/player/play?device_id="+deviceid, headers=headers, data=jsn.dumps(payload))
    if r.status_code == 204:
        time.sleep(0.5)
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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+devicename+"\033[0m.")
    else:
        print("Unable to play \033[1m\033[95m"+trackname+"\033[0m.")
    return r.status_code

def spotVL():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}
 
    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    json = r.json()
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    if len(json["devices"]) == 1:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
    for i in json["devices"]:
        if i["is_active"] == True:
            deviceid = i["id"]
            devicename = i["name"]

    choice = input("Change volume on \033[1m\033[92m"+devicename+"\033[0m [0-100]: ")
    try:
        choice = int(choice)%101
    except:
        print("Only integers please.")
        quit()

    r = requests.put("https://api.spotify.com/v1/me/player/volume?volume_percent="+str(choice), headers=headers)
    if r.status_code == 204:
        print("Volume on \033[1m\033[92m"+devicename+"\033[0m now "+str(choice))
    else:
        print("No active playback devices")
    return r.status_code

if __name__ == "__main__":
    main()
