# yttool

A tool for extracting info from youtube:
 * print all comments for a video
 * print a video's description + info
 * print all subtitles for a video
 * print out an entire livechat replay.
 * list all items in a playlist
 * list all videos for a channel or user
 * list all video's matching a query

# install

You can install this from the official python repository using `pip`:

    pip3 install youtube-tool

Note: depending on your local python installation(s), you may have to type
one of `pip`, `pip3`, or maybe even: `pip3.8`.


You can also 'install' this by executing the `yttool.py` file directly from
the source directory:

    python3 yttool.py  ....arguments...


# requirements

This script needs python 3.8 or later to run.

# usage

## list all subtitles attached to a video.

This will output the subtitles in all available languages.

    yttool --subtitles https://www.youtube.com/watch?v=bJOuzqu3MUQ

Or list the subtitles prefixed with timestamps

    yttool -v --subtitles https://www.youtube.com/watch?v=bJOuzqu3MUQ


You can also extract the subtitles in a format suitable for
creating `.srt` subtitle files:

    yttool --srt --subtitles https://www.youtube.com/watch?v=bJOuzqu3MUQ


Or you can filter by language, for example only output the english subtitles:

    yttool --language en --subtitles https://www.youtube.com/watch?v=0xY06PT5JDE

Or only output the automatically generated subtitles:

    yttool --language asr --subtitles https://www.youtube.com/watch?v=0xY06PT5JDE


## comments

List all the comments for this Numberphile video:

    yttool --comments https://www.youtube.com/watch?v=bJOuzqu3MUQ


## livechat replay

Print out an entire livechat replay:

    yttool --livechat https://www.youtube.com/watch?v=lE0u_jIDh0E


## list a playlist contents.

List all the video's contained in this System of a Down playlist:

    yttool --playlist https://www.youtube.com/playlist?list=PLSKnqXUHTaSdXuK8Z2d-hXLFtJbRZwPtJ

The output will look like this:

    CSvFpBOe8eY - System Of A Down - Chop Suey! (Official Video)
    zUzd9KyIDrM - System Of A Down - B.Y.O.B. (Official Video)
    L-iepu3EtyE - System Of A Down - Aerials (Official Video)
    iywaBOMvYLI - System Of A Down - Toxicity (Official Video)
    DnGdoEa1tPg - System Of A Down - Lonely Day (Official Video)
    LoheCz4t2xc - System Of A Down - Hypnotize (Official Video)
    5vBGOrI6yBk - System Of A Down - Sugar (Official Video)
    SqZNMvIEHhs - System Of A Down - Spiders (Official Video)
    ENBv2i88g6Y - System Of A Down - Question! (Official Video)
    bE2r7r7VVic - System Of A Down - Boom! (Official Video)
    F46r-_jPPHY - System Of A Down - War? (Official Video)

The first 11 characters are the video id, you can load the corresponding video
by typing: `https://www.youtube.com/watch?v=5vBGOrI6yBk` in your browser's URL bar.


Or list all video's from a channel:

    yttool -l https://www.youtube.com/channel/UCoxcjq-8xIDTYp3uz647V5A

Or when you don't know the channelid, you can get the same with the username:

    yttool -l https://www.youtube.com/user/numberphile


## list query results

This:

    yttool -q somequery

Will list first couple of the video's matching that query.

## Just the id's

You can also call yttool with only the video id as an argument:

    yttool --info CSvFpBOe8eY


# Side note about youtube video id's

Youtube's id's are structured in several ways:

A videoid is 11 characters long, when decoded using base64, this results in exactly 8 bytes.
The last character of a videoid can only be: `048AEIMQUYcgkosw`  --> 10x6+4 = 64 bits

A playlist id is either 24 or 34 characters long, and has the following format:

### id's containing a 'playlist' id.

 * "PL<playlistid>" or "EC<playlistid>" -- custom playlist, or educational playlist.
 * "BP<playlistid>" and "SP<playlistid>"  also seem to have some kind of function.
 * playlistid can be:
   * either 32 base64 characters --> either a 6x32 = 192 bits
   * or or 16 hex characters --> either a 16x4 = 64 bits
 * www.youtube.com/playlist?list=PL<playlistid>
 * www.youtube.com/course?list=EC<playlistid>
   * no longer works very well, the layout of the `course` page is broken,
     with lots of overlapping text.

### id's containing a channel id

A channel-id is 22 base64 characters, with the last character one of: `AQgw`, so this decodes to 21x6+2 = 128 bits

 * "UC<channelid>"  -- user channel
   * www.youtube.com/channel/UC<channelid>
 * "PU<channelid>"  -- popular uploads playlist
   * quick way to load: www.youtube.com/watch?v=xxxxxxxxxxx&list=PU<channelid>
 * "UU<channelid>"  -- user uploads playlist
   * quick way to load: www.youtube.com/watch?v=xxxxxxxxxxx&list=UU<channelid>
 * "LL<channelid>"  -- liked video's for user
   * quick way to load: www.youtube.com/watch?v=xxxxxxxxxxx&list=LL<channelid>
   * or www.youtube.com/playlist?list=LL<channelid>
 * "FL<channelid>"     -- favorites
   * www.youtube.com/watch?v=xxxxxxxxxxx&list=FL<channelid>
 * "RDCMUC<channelid>" -- mix for channel
   * www.youtube.com/watch?v=xxxxxxxxxxx&list=RDCMUC<channelid>

 * prefixes CL, EL, MQ, TT, WL also seem to have a special meaning

### Other playlist types

These take 
 * "TLGG<22chars>"  -- temporary list - redir from `watch_videos`
    * When decoded, the last 8 bytes are digits for the "ddmmyyyy" date.
 * "RDEM<22chars>" -- radio channel
   * 22chars is NOT a channel-id
   * www.youtube.com/watch?v=xxxxxxxxxxx&list=RDEM<22chars>
 * "RD<videoid>"  -- mix for a specific video.
 * "OLAK5uy_<33chars>"   -- album playlist.
   * id's start with: `klmn`  : 0b1001xx
   * id's ends with: `AEIMQUYcgkosw048`  --> 2 + 31x6 + 4 = 192 bits
   * www.youtube.com/playlist?list=OLAK5uy_<33chars>
 * "WL"           -- 'watch later'
   * www.youtube.com/playlist?list=WL
   * www.youtube.com/watch?v=xxxxxxxxxxx&list=WL
 * "UL"        -- channel video mix
   * www.youtube.com/watch?v=<11charsvidid>&list=ULxxxxxxxxxxx
   * This works only when there are exactly 11 characters after 'UL'
 * "LM"        -- music.youtube likes
 * "RDMM"      -- music.youtube your mix
 * "RDAMVM<videoid>"      -- music.youtube band mix
 * "RDAO<22chars>"
 * "RDAMPL" + prefix+playlistid
 * "RDCLAK5uy_" + 33chars
 * "RDTMAK5uy_" + 33chars

 * prefixes EL, CL also seem to have a special meaning.


# Youtube url's


Domains:

    youtu.be
    youtube.com

UrlPath:

    /watch?v=<videoid>&t=123s&list=<listid>
    /v/<videoid>
    /embed/<videoid>
    /embed/videoseries?list=<playlistid>
    /watch/<videoid>
    /playlist?list=<playlistid>
    /channel/<channelid>
    /user/<username>
    /watch_videos?video_ids=<videoid>,<videoid>,...

# TODO

 * DONE extract 'listid' from video links for playlist view.
 * DONE list a channel's video's
 * DONE list a user's video's
 * handle radio links
 * DONE extract live-chat comments
 * Filter out duplicates from the livechat replay dump.
 * check how my tool works with an actual live chat.
 * DONE youtube search results.
 * generalize the way continuations are used.
 * add upload date and duration in the video lists.

# AUTHOR

Willem Hengeveld <itsme@xs4all.nl>

