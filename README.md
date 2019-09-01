# SpotifyCLI

## Installation
Clone or download zip<br/>
Create secrets file in same directory as script<br/>
&nbsp;&nbsp;&nbsp;line 1 app token<br/>
&nbsp;&nbsp;&nbsp;line 2 refresh token

## Usage
`python3 spot.py <option>`

### Options
- `status`: show now playing
- `search <track/album> <query>`: search (defaults to track), if no query will ask for input
- `shuffle`: toggle shuffle
- `previous`: previous song
- `next`: next song
- `play`: toggle play/pause
- `like`: add currently playing to liked songs
- `playlist add`: add currently playing to playlist of choice
- `playlist remove`: remove currently playing from choice of playlist
- `device`: change playback device
- `playlist play`: choose playlist to play from saved playlists
- `volume <int>`: set volume to int (0-100)
