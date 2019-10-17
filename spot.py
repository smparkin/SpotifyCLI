import argparse
import requests
import json as jsn
import urllib.request
import numpy as np
import imgcat
from PIL import Image
import sys
import time
import traceback

'''
create file called secrets in same folder as spot.py with app token on line 1 and refresh token on line 2
'''

def parse_arguments():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest='mode')

    status = subparsers.add_parser('status', help='Show now playing')
    status.add_argument('--imgcat', action='store_true', help='print album art with imgcat', default=False)
    status.add_argument('--time', action='store_true', help='print position in song', default=False)

    playlist = subparsers.add_parser('playlist', help='Perform playlist-related operations')
    playlist_operation = playlist.add_mutually_exclusive_group(required=True)
    playlist_operation.add_argument('--add', action='store_true', help='add currently playing song to playlist of choice', default=False)
    playlist_operation.add_argument('--remove', action='store_true', help='remove currently playing song from playlist of choice', default=False)
    playlist_operation.add_argument('--play', action='store_true', help='choose a playlist to play from user-saved playlists', default=False)

    search = subparsers.add_parser('search', help='Perform search-related operations')
    search_track_or_album = search.add_mutually_exclusive_group(required=True)
    search_track_or_album.add_argument('--track', action='store_true', help='Search for a specific track on Spotify', default=False)
    search_track_or_album.add_argument('--album', action='store_true', help='Search for a specific album on Spotify', default=False)
    search.add_argument('query', nargs='+', help='Search query')

    playback = subparsers.add_parser('playback', help='Perform playback-related operations')
    playback_operation = playback.add_mutually_exclusive_group(required=True)
    playback_operation.add_argument('--seek', type=float, help='seek <int>/4 into song')
    playback_operation.add_argument('--shuffle', action='store_true', help='toggle shuffle', default=False)
    playback_operation.add_argument('--previous', action='store_true', help='previous song', default=False)
    playback_operation.add_argument('--next', action='store_true', help='next song', default=False)
    playback_operation.add_argument('--play', action='store_true', help='toggle play/pause', default=False)
    playback_operation.add_argument('--like', action='store_true', help='add currently playing song to liked songs', default=False)
    playback_operation.add_argument('--unlike', action='store_true', help='remove currently playing song from liked songs', default=False)
    playback_operation.add_argument('--volume', type=int, help='set volume to int (0-100)')

    device = subparsers.add_parser('device', help='Change Playback device')

    parser.add_argument('-u', '--usage', action='store_true', help='show usage')

    args = parser.parse_args()

    if args.mode is None or args.usage:
        parser.print_usage()

    return args

def main():
    args = parse_arguments()

    if args.mode == 'status':
        spotNP(args.imgcat, args.time)

    elif args.mode == 'playlist':
        if args.add is True:
            spotAP()
        elif args.remove is True:
            spotRP()
        elif args.play is True:
            spotPL()

    elif args.mode == 'search':
        if args.track is True:
            context = 'track'
        if args.album is True:
            context = 'album'
        if args.query is True:
            query = args.query
        else:
            query = None
        spotSE(context, query)

    elif args.mode == 'playback':
        if args.shuffle is True:
            spotSF()
        elif args.previous is True:
            spotPR()
        elif args.next is True:
            spotNE()
        elif args.play is True:
            spotPP()
        elif args.like is True:
            spotLS()
        elif args.unlike is True:
            spotRL()
        elif args.seek or args.seek == 0:
            spotSK(args.seek)
        elif args.volume or args.volume == 0:
            spotVL(args.volume)

    elif args.mode == 'device':
        spotPD()

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


def spotDevice(headers, caller):
    r = requests.get("https://api.spotify.com/v1/me/player/devices", headers=headers)
    if r.status_code != 200:
        print('Invalid permissions!')
        quit()
    json = r.json()
    deviceid = None
    if len(json["devices"]) == 0:
        print("No playback devices")
        quit()
    elif len(json["devices"]) == 1:
        deviceid = json["devices"][0]["id"]
        devicename = json["devices"][0]["name"]
        if caller == "dev":
            print("\033[1m\033[92m"+devicename+"\033[0m is only device.")
            quit()
    elif caller == "vol" or caller == "prev" or caller == "next" or caller == "np":
        for i in json["devices"]:
            if i["is_active"] == True:
                deviceid = i["id"]
                devicename = i["name"]
        if deviceid == None:
            print("No active device")
            quit()
    elif caller == "dev":
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
    elif caller == "play" or caller == "search":
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
    else:
        for i in range(0,len(json["devices"])):
            print("["+str(i)+"] "+json["devices"][i]["name"])
        choice = input("Choose device: ")
        try:
            choice = int(choice)
        except:
            quit()
        deviceid = json["devices"][choice]["id"]
        devicename = json["devices"][choice]["name"]
    
    devicedict = {}
    devicedict.update( {"deviceid": deviceid})
    devicedict.update( {"devicename": devicename})
    return devicedict


def spotSK(seekTime):
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
    durationMS = int(json["item"]["duration_ms"])
    seekMS = durationMS*(seekTime/4)
    seekMS = round(seekMS)

    r = requests.put("https://api.spotify.com/v1/me/player/seek?position_ms="+str(seekMS), headers=headers)
    if r.status_code == 204:
        print("Seeking to "+str((seekMS/1000)/60)+" minutes")
    else:
        print("Error: HTTP"+str(r.status_code))
    return r.status_code


def spotNP(imgcatBool, timeBool):
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}

    dev = spotDevice(headers, "np")
    devicename = dev["devicename"]

    r = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    if r.status_code == 204:
        print("Nothing playing")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    try:
        json = r.json()
        playing = json["is_playing"]
    except:
        playing = False

    if playing == False:
        text = "paused"
    elif playing == True:
        text = "playing" 

    title = json["item"]["name"]
    artist = json["item"]["album"]["artists"][0]["name"]
    imgurl = json["item"]["album"]["images"][1]["url"]
    durationSec = (json["item"]["duration_ms"])/1000
    currentSec = (json["progress_ms"])/1000
    print("\033[95m\033[1m"+title+"\033[0m by ", end='')
    print("\033[94m\033[1m"+artist+"\033[0m is "+text+" on ", end='')
    print("\033[92m\033[1m"+devicename+"\033[0m")
    if (imgcatBool):
        im = np.asarray(Image.open(urllib.request.urlopen(imgurl)))
        time.sleep(1)
        imgcat.imgcat(im)
    if (timeBool):
        print(str(round(currentSec//60))+":"+(str(round(currentSec%60))).zfill(2)+"/"+str(round(durationSec//60))+":"+(str(round(durationSec%60)).zfill(2)))
    return r.status_code


def spotSE(context, query):
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}

    query = ' '.join(query)
    payload = {'type': context, 'q': query}

    r = requests.get("https://api.spotify.com/v1/search", params=payload, headers=headers)
    if r.status_code == 204:
        print("No results")
        quit()
    elif r.status_code != 200:
        print("Error: HTTP"+str(r.status_code))
        quit()
    json = r.json()
    try:
        if context == "album":
            uri = json["albums"]["items"][0]["uri"]
            name = json["albums"]["items"][0]["name"]
        elif context == "track":
            uri = json["tracks"]["items"][0]["uri"]
            name = json["tracks"]["items"][0]["name"]
    except:
        print("Search returned no results")
        quit()

    dev = spotDevice(headers, "search")

    if context == "album":
        payload = {"context_uri": uri}
    else:
        payload = {"uris": [uri]}
    r = requests.put("https://api.spotify.com/v1/me/player/play?device_id="+dev["deviceid"], headers=headers, data=jsn.dumps(payload))
    if r.status_code == 204:
        print("Playing "+context+"\033[1m\033[95m "+name+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
    else:
        print("Unable to play \033[1m\033[95m"+name+"\033[0m.")
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

    dev = spotDevice(headers, "prev")

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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
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

    dev = spotDevice(headers, "next")

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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
    else:
        print("Unable to play \033[1m\033[95m"+trackname+"\033[0m.")
    return r.status_code


def spotPP():
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}

    dev = spotDevice(headers, "play")

    r = requests.get("https://api.spotify.com/v1/me/player", headers=headers)
    try:
        json = r.json()
        playing = json["is_playing"]
    except:
        playing = False

    if playing == False:
        r = requests.put("https://api.spotify.com/v1/me/player/play?device_id="+dev["deviceid"], headers=headers)
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
            print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
        else:
            print("No active devices")
    elif playing == True:
        r = requests.put("https://api.spotify.com/v1/me/player/pause?device_id="+dev["deviceid"], headers=headers)
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
            print("Paused \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
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

def spotRL():
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
    r = requests.delete("https://api.spotify.com/v1/me/tracks?ids="+trackid, headers=headers)
    if r.status_code == 200:
        print("Removed \033[1m\033[95m"+json["item"]["name"]+"\033[0m from Liked Songs")
    else:
        print("An error occured, fun")


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

    dev = spotDevice(headers, "dev")

    payload = {"device_ids":[dev["deviceid"]]}
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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
    elif r.status_code == 202:
        time.sleep(2)
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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
    else:
        print(r.status_code)
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

    dev = spotDevice(headers, "playlist play")

    payload = {"context_uri": "spotify:playlist:"+playlistid}
    r = requests.put("https://api.spotify.com/v1/me/player/play?device_id="+dev["deviceid"], headers=headers, data=jsn.dumps(payload))
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
        print("Playing \033[1m\033[95m"+trackname+"\033[0m on \033[1m\033[92m"+dev["devicename"]+"\033[0m.")
    else:
        print("Unable to play \033[1m\033[95m"+trackname+"\033[0m.")
    return r.status_code


def spotVL(vol):
    accessToken = spotAuth()
    headers = {"Authorization": "Bearer "+accessToken}

    dev = spotDevice(headers, "vol")

    try:
        vol = int(vol)%101
    except:
        print("Only integers please.")
        quit()

    r = requests.put("https://api.spotify.com/v1/me/player/volume?volume_percent="+str(vol), headers=headers)
    if r.status_code == 204:
        print("Volume on \033[1m\033[92m"+dev["devicename"]+"\033[0m set to "+str(vol))
    else:
        json = r.json()
        reason = json["error"]["reason"]
        if reason == "VOLUME_CONTROL_DISALLOW":
            print("Device \033[1m\033[92m"+dev["devicename"]+"\033[0m does not allow volume to be controlled through API")
        else:
            print("No active playback devices")
    return r.status_code

if __name__ == "__main__":
    try:
        main()
        status = 0
    except Exception as msg:
        print('ERROR - {}'.format(msg))
        traceback.print_exc()
        status = -1

    exit(status)
