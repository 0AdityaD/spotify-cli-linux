#!/usr/bin/python -u
# -*- coding: utf-8 -*-
"""a command line interface to Spotify on Linux"""

import sys
import os
import argparse
import dbus
import re
from subprocess import Popen, PIPE, STDOUT, check_output

if sys.version_info > (3, 6):
    from .version import __version__
else:
    from version import __version__


def main():
    if len(sys.argv) == 1:
        start_shell()
        return 0

    args = add_arguments()
    if args.version:
        show_version()
    elif args.status:
        show_status()
    elif args.statusshort:
        show_status_short()
    elif args.song:
        show_song()
    elif args.songshort:
        show_song_short()
    elif args.artist:
        show_artist()
    elif args.artistshort:
        show_artist_short()
    elif args.album:
        show_album()
    elif args.playbackstatus:
        show_playback_status()
    elif args.play:
        perform_spotify_action("Play")
    elif args.pause:
        perform_spotify_action("Pause")
    elif args.playpause:
        perform_spotify_action("PlayPause")
    elif args.next:
        perform_spotify_action("Next")
    elif args.prev:
        perform_spotify_action("Previous")
    elif args.volumeup:
        control_volume("+5%")
    elif args.volumedown:
        control_volume("-5%")
    elif args.mute:
        mute()
    elif args.unmute:
        unmute()


def start_shell():
    while(True):
        try:
            if sys.version_info > (3, 6):
                command = input('spotify > ')
            else:
                command = raw_input('spotify > ')
        except EOFError as exception:
            print("Have a nice day!")
            exit(0)

        pid = os.fork()

        if pid == 0:  # if executing context is child process
            os.execlp('spotifycli', 'spotifycli', '--{}'.format(command))
        elif pid > 0:
            os.waitpid(pid, 0)  # wait for child to exit
        else:
            print("Error during call to fork()")
            exit(1)


def add_arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    for argument in get_arguments():
        parser.add_argument(argument[0], help=argument[1], action="store_true")
    return parser.parse_args()


def get_arguments():
    return [
        ("--version", "shows version number"),
        ("--status", "shows song name and artist"),
        ("--statusshort", "shows status in a short way"),
        ("--song", "shows the song name"),
        ("--songshort", "shows the song name in a short way"),
        ("--artist", "shows artist name"),
        ("--artistshort", "shows artist name in a short way"),
        ("--album", "shows album name"),
        ("--playbackstatus", "shows playback status"),
        ("--play", "plays the song"),
        ("--pause", "pauses the song"),
        ("--playpause", "plays or pauses the song (toggles a state)"),
        ("--next", "plays the next song"),
        ("--prev", "plays the previous song"),
        ("--volumeup", "increases the sound volume"),
        ("--volumedown", "decreases the sound volume"),
        ("--mute", "mutes all sound"),
        ("--unmute", "unmutes all sound")
    ]


def show_version():
    print(__version__)


def get_song():
    metadata = get_spotify_property("Metadata")
    artist = metadata['xesam:artist'][0]
    title = metadata['xesam:title']
    return (artist, title)


def show_status():
    artist, title = get_song()
    print("%s - %s" % (artist, title))


def show_status_short():
    artist, title = get_song()
    artist = artist[:15] + (artist[15:] and '...')
    title = title[:10] + (title[10:] and '...')
    print("%s - %s" % (artist, title))


def show_song():
    _, title = get_song()
    print("%s" % title)


def show_song_short():
    _, title = get_song()
    title = title[:10] + (title[10:] and '...')
    print("%s" % title)


def show_artist():
    artist, _ = get_song()
    print("%s" % artist)


def show_artist_short():
    artist, _ = get_song()
    artist = artist[:15] + (artist[15:] and '...')
    print("%s" % artist)


def show_playback_status():
    playback_status = get_spotify_property("PlaybackStatus")
    print({"Playing": 'Playing',
           "Paused": 'Paused',
           "Stopped": 'Stopped'
           }[playback_status])


def show_album():
    metadata = get_spotify_property("Metadata")
    print("%s" % metadata['xesam:album'])


def get_spotify_property(spotify_property):
    try:
        session_bus = dbus.SessionBus()
        spotify_bus = session_bus.get_object(
            "org.mpris.MediaPlayer2.spotify",
            "/org/mpris/MediaPlayer2")
        spotify_properties = dbus.Interface(
            spotify_bus,
            "org.freedesktop.DBus.Properties")
        return spotify_properties.Get(
            "org.mpris.MediaPlayer2.Player",
            spotify_property)
    except BaseException:
        sys.stderr.write("Spotify is off\n")
        sys.exit(1)


def perform_spotify_action(spotify_command):
    Popen('dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify '
          '/org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player."%s"' %
          spotify_command, shell=True, stdout=PIPE)


def getSinks():
    output = check_output('pactl list sinks',
                          shell=True,
                          stderr=STDOUT,
                          universal_newlines=True)
    res = list(filter(lambda x: 'Sink #' in x,
                      re.split('\n', str(output).replace('\\n\\n', '\n'))))
    res = list(map(lambda x: int(x.strip('Sink #')), res))
    return res


def control_volume(volume_percent):
    sinks = getSinks()
    for sink in sinks:
        Popen(
            'pactl set-sink-volume %d "%s"' %
            (sink, volume_percent),
            shell=True,
            stdout=PIPE)


def muter(action):
    sinks = getSinks()
    for sink in sinks:
        Popen('pactl set-sink-mute %d %d' %
              (sink, action), shell=True, stdout=PIPE)


def mute():
    muter(1)


def unmute():
    muter(0)


if __name__ == "__main__":
    main()
