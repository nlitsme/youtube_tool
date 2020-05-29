# yttool

A tool for extracting info from youtube, like video comments, subtitles, or playlist items.


## list all subtitles attached to a video.

List the subtitles, this will output all available languages.

    yttool --subtitles https://www.youtube.com/watch?v=bJOuzqu3MUQ

Or list the subtitles prefixed with timestamps

    yttool -v --subtitles https://www.youtube.com/watch?v=bJOuzqu3MUQ


You can also extract the subtitles in a format suitable for
creating `.srt` subtitle files:

    yttool --srt --subtitles https://www.youtube.com/watch?v=bJOuzqu3MUQ


## comments

List all the comments for this Numberphile video:

    yttool --comments https://www.youtube.com/watch?v=bJOuzqu3MUQ


## list a playlist contents.

List all the video's contained in this System of a Down playlist:

    yttool --playlist https://www.youtube.com/playlist?list=PLSKnqXUHTaSdXuK8Z2d-hXLFtJbRZwPtJ


# Youtube video id's

Youtube's id's are structure in several ways:

 * a videoid is 11 characters long.
 * a playlist id is either 24 or 34 characters long, and has the following format:
   * "PL<32chars>"  -- custom playlist
   * "UC<22chars>"  -- user channel
   * "PU<22chars>"  -- popular uploads playlist
   * "UU<22chars>"  -- user playlist
   * "VLPL<32chars>"
   * "RDEM<22chars>" -- radio channel


# TODO

 * extract 'listid' from video links for playlist view.
 * handle radio links
 * extract live-chat comments

# AUTHOR

Willem Hengeveld <itsme@xs4all.nl>

