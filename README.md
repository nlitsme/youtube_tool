# yttool

A tool for extracting info from youtube, like video comments, subtitles, or playlist items.

## song, which has no subtitles

    yttool --subtitles https://www.youtube.com/watch?v=EPOAHKTLsUo

## electroboom vid, with 4 different subtitles

    yttool --subtitles https://www.youtube.com/watch?v=0xY06PT5JDE


## comments

    yttool --comments https://www.youtube.com/watch?v=0xY06PT5JDE

# TODO

Add option to list playlist video's

    "contents": {
        "twoColumnWatchNextResults": {
            "playlist": {
                    "title": "music",
                    "contents": [
                        { "playlistPanelVideoRenderer":... }
                     ] } } }

   * playlistPanelVideoRenderer

