#!/usr/bin/env python3
"""
A tool for extracting useful information from youtube video's, like comments, or subtitles.

Author: Willem Hengeveld <itsme@xs4all.nl>

todo:
extract 4 different dictionaries from the html page.
-- ytInitialPlayerResponse
-- ytcfg.set()
-- ytplayer.web_player_context_config
-- ytInitialData 

"""

import urllib.request
import urllib.parse
import http.cookiejar
import re
import json
import sys
import html
import datetime
from collections import defaultdict

from xml.parsers.expat import ParserCreate

import http.client


def cvdate(txt):
    """
    Convert a string with a date in ymd format to a date object.
    """
    ymd = txt.split("-")
    if len(ymd)!=3:
        print("WARNING: invalid date format: %s" % txt)
        return
    y, m, d = [int(_) for _ in ymd]
    return datetime.date(y, m, d)


def cvseconds(txt):
    """
    Convert string containing a number of seconds to a timedelta object.
    """
    return datetime.timedelta(seconds=int(txt))


def getitembymember(a, member):
    """
    Get the first item from 'a' which has an element named 'member'
    """
    for item in a:
        if member in item:
            return item


def getitem(d, *path):
    """
    Traverse a nested python object, path items select which object is selected:
     * a tuple: selects a dictionary from a list which contains the specified key
     * an integer: select the specified item from a list.
     * a string: select the specified item from a dictionary.
    """
    for k in path:
        if type(k) == tuple:
            d = getitembymember(d, *k)
        elif type(k) == int:
            d = d[k]
        else:
            d = d.get(k)

        if d is None:
            return
    return d


class Youtube:
    """
    Class which knows how to get information from youtune video's

    TODO: get youtube client version by requesting youtube with "User-Agent: Mozilla/5.0 (Mac) Gecko/20100101 Firefox/76.0"
    TODO: extract the inntertubeapikey from the youtube html page.
    """
    def __init__(self, args):
        self.args = args
        cj = http.cookiejar.CookieJar()
        handlers = [urllib.request.HTTPCookieProcessor(cj)]
        if args.debug:
            handlers.append(urllib.request.HTTPSHandler(debuglevel=1))
        self.opener = urllib.request.build_opener(*handlers)
        self.innertubeapikey = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
        self.clientversion =  "2.20210111.08.00"

    def httpreq(self, url, data=None):
        """
        Does GET or POST request to youtube.
        """
        hdrs = {
            "x-youtube-client-name": "1",
            "x-youtube-client-version": self.clientversion,
            "User-Agent": "Mozilla/5.0 (Mac) Gecko/20100101 Firefox/76.0",
        }
        if data and data[:1] in (b'{', b'['):
            hdrs["Content-Type"] = "application/json"

        req = urllib.request.Request(url, headers=hdrs)

        kwargs = dict()
        if data:
            kwargs["data"] = data

        response = self.opener.open(req, **kwargs)
        return response.read()

    def getcomments(self, contclick, xsrf):
        """
        Returns comments for the specified continuation parameter.
        """
        cont, click = contclick
        url = "https://www.youtube.com/comment_service_ajax"
        query = {
            "action_get_comments": 1,  # todo: see what action_get_comment_replies=1 is for.
            "pbj": 1,
            "ctoken": cont,
            #"continuation": cont,   # -- it turns out we don't need this 2nd copy of the token.
            "itct": click,
        }

        postdata = urllib.parse.urlencode({ "session_token":xsrf })
        return self.httpreq(url + "?" + urllib.parse.urlencode(query), postdata.encode('ascii') )

    def getchat(self, cont, live=False):
        """
        Returns chat for the specified continuation parameter.
        """
        if live:
            url = "https://www.youtube.com/live_chat"
        else:
            url = "https://www.youtube.com/live_chat_replay"
        query = {
            "pbj": 1,
            "continuation": cont,
        }

        return self.httpreq(url + "?" + urllib.parse.urlencode(query))

    def getchat2(self, cont, offset, live=False):
        """
        Returns chat for the specified continuation parameter.
        """
        if live:
            url = "https://www.youtube.com/youtubei/v1/live_chat_replay/get_live_chat"
        else:
            url = "https://www.youtube.com/youtubei/v1/live_chat_replay/get_live_chat_replay"
        query = {
            "pbj": 1,
            "continuation": cont,
            "playerOffsetMs": offset,
            "hidden": False,
            "commandMetadata": "[object Object]",
        }

        return self.httpreq(url + "?" + urllib.parse.urlencode(query))

    def getsearch(self, cont):
        """
        Returns next batch of search results
        """
        url = "https://www.youtube.com/youtubei/v1/search"
        query = {
            "key": self.innertubeapikey
        }
        postdata = {
            "context": { "client": {   "clientName": "WEB", "clientVersion": self.clientversion } },
            "continuation": cont,
        }
        postdata = json.dumps(postdata)
        return self.httpreq(url + "?" + urllib.parse.urlencode(query), postdata.encode('ascii'))

    def browse(self, contclick):
        """
        Returns videos for the specified continuation parameter.
        """
        cont, click = contclick
        url = "https://www.youtube.com/browse_ajax"
        query = {
            "ctoken": cont,
            "continuation": cont,
            "itct": click,
        }

        return self.httpreq(url + "?" + urllib.parse.urlencode(query))

    def getpageinfo(self, yturl):
        """
        Returns the youtube configuration object.
        """
        ytcfgtext = self.httpreq(yturl + ("&" if yturl.find('?')>=0 else "?") + "pbj=1")
        if self.args.debug:
            print("============ youtube config")
            print(ytcfgtext.decode('utf-8'))
            print()

        return json.loads(ytcfgtext)

    def getconfigfromhtml(self, ythtml):
        """
        Alternative method of extracting the config object.
        By parsing the html page returned by youtube.
        """
        if self.args.debug:
            print("============ youtube page")
            print(ythtml.decode('utf-8'))
            print()

        m = re.search(br'ytplayer.config = (.*?);ytplayer.load', ythtml)
        if not m:
            print("could not find config")
            return
        cfgtext = m.group(1)
        if self.args.debug:
            print("========== config json")
            print(cfgtext.decode('utf-8'))
            print()

        cfg = json.loads(cfgtext)
        
        playertext = cfg['args']['player_response']
        if self.args.debug:
            print("========== player json")
            print(playertext)
            print()
        return json.loads(playertext)

    def extractsearchconfig(self, html):
        if self.args.debug:
            print("============ youtube page")
            print(html.decode('utf-8'))
            print()
        m = re.search(br'window["ytInitialData"] = (.*);', html)
        if not m:
            print("could not find config")
            return
        cfgtext = m.group(1)
        if self.args.debug:
            print("========== config json")
            print(cfgtext.decode('utf-8'))
            print()

        return json.loads(cfgtext)



class LivechatReader:
    """
    class reads a livechat or livechat replay.
    """
    def __init__(self, args, yt, cfg, live=False):
        self.args = args
        self.yt = yt
        self.live = live
        self.cont = self.getchatinfo(cfg)

    def getcontinuation(self, p):
        p = getitem(p, "continuations", 0, "liveChatReplayContinuationData" if self.live else "reloadContinuationData")
        if not p:
            return
        return p["continuation"]

    def getchatinfo(self, cfg):
        """
        Find the base parameters for querying the video's comments.

        """
        item = getitem(cfg, ("response",), "response", "contents", "twoColumnWatchNextResults", "conversationBar", "liveChatRenderer")
        if not item:
            return
        return self.getcontinuation(item)

    def recursechat(self):
        if not self.cont:
            print("no live chat replay found")
            return
        ms = 0
        while True:
            #cmtjson = self.yt.getchat2(self.cont, ms, self.live)
            cmtjson = self.yt.getchat(self.cont, self.live)
            if self.args.debug:
                print("============ chat req")
                print(cmtjson.decode('utf-8'))
                print()
            if cmtjson.startswith("<!DOCTYPE"):
                print("not json")
                break

            js = json.loads(cmtjson)

            cmtlist, newms = self.extractchat(js) 
            if newms==ms:
                break

            for author, time, runs in cmtlist:
                print("--->", time, author)
                self.printtextrun(runs)

            ms = newms

    def extractchat(self, js):
        actions = getitem(js, ("response",), "response", "continuationContents", "liveChatContinuation", "actions")

        cmtlist = []
        ms = None

        for act in actions:
            replay = getitem(act, "replayChatItemAction", "actions")
            ms = getitem(act, "replayChatItemAction", "videoOffsetTimeMsec")

            item = getitem(replay, ("addChatItemAction",), "addChatItemAction", "item", "liveChatTextMessageRenderer")
            if item:
                msg = getitem(item, "message", "runs")
                author = getitem(item, "authorName", "simpleText")
                time = getitem(item, "timestampText", "simpleText")

                cmtlist.append((author, time, msg))

        return cmtlist, ms

    def printtextrun(self, runs):
        for r in runs:
            print(r.get('text'), end="")
        print()



class CommentReader:
    """
    class which can recursively print comments
    """
    def __init__(self, args, yt, cfg):
        self.args = args
        self.yt = yt
        self.contclick, self.xsrf = self.getcommentinfo(cfg)

    def printtextrun(self, runs):
        for r in runs:
            print(r.get('text'), end="")
        print()

    def extractruns(self, runs):
        text = []
        for r in runs:
            text.append(r.get('text'))
        return "".join(text)

    def recursecomments(self, cc=None, level=0):
        if not cc:
            cc = self.contclick
        while cc:
            cmtjson = self.yt.getcomments(cc, self.xsrf)
            if self.args.debug:
                print("============ comment req")
                print(cmtjson.decode('utf-8'))
                print()

            js = json.loads(cmtjson)

            cmtlist, cc = self.extractcomments(js) 

            for author, when, runs, likes, replies, subcc in cmtlist:
                if self.args.verbose:
                    print("---" * (level+1) + ">", "%s ; %s ; %s likes ; %s replies" % (author, when, likes, replies))
                else:
                    print("---" * (level+1) + ">", author)
                self.printtextrun(runs)
                if subcc:
                    self.recursecomments(subcc, level+1)

    def getcontinuation(self, p):
        p = getitem(p, "continuations", 0, "nextContinuationData")
        if not p:
            return
        return p["continuation"], p["clickTrackingParams"]

    def getcommentinfo(self, cfg):
        """
        Find the base parameters for querying the video's comments.

        """
        item = getitem(cfg, ("response",), "response", "contents", "twoColumnWatchNextResults", "results", "results", "contents")
        cont = self.getcontinuation(getitem(item, ("itemSectionRenderer",), "itemSectionRenderer")) 
        xsrf = getitem(cfg, ("response",), "xsrf_token")

        return cont, xsrf

    def getcomment(self, p):
        """
        Return info for a single comment.
        """
        if "commentThreadRenderer" in p:
            p = p["commentThreadRenderer"]

        c = p
        r = p
        if "comment" in c:
            c = c["comment"]
        if "commentRenderer" in c:
            c = c["commentRenderer"]
        if "replies" in r:
            r = r["replies"]

        author = getitem(c,  "authorText", "simpleText")
        content = getitem(c,  "contentText", "runs")
        likes = getitem(c, "likeCount")
        nrreplies = getitem(c, "replyCount")
        when = self.extractruns(getitem(c,  "publishedTimeText", "runs"))
        replies = getitem(r,  "commentRepliesRenderer")
        if replies:
            cont = self.getcontinuation(replies)
        else:
            cont = None

        return author, when, content, int(likes or 0), int(nrreplies or 0), cont

    def extractcomments(self, js):
        """
        Extract a list of comments from comment dictionary
        """
        p = getitem(js, "response", "continuationContents")
        if not p:
            print("non contents found in continuation")
            return [], None
        if "itemSectionContinuation" in p:
            p = p["itemSectionContinuation"]
        elif "commentRepliesContinuation" in p:
            p = p["commentRepliesContinuation"]

        cmtlist = []
        for c in p["contents"]:
            cmtlist.append(self.getcomment(c))

        # header.commentsHeaderRenderer -> commentsCount  at same level as 'contents'

        return cmtlist, self.getcontinuation(p)


class SearchReader:
    def __init__(self, args, yt, cfg):
        self.args = args
        self.yt = yt
        self.cfg = cfg

    def extractruns(self, runs):
        text = []
        for r in runs:
            text.append(r.get('text'))
        return "".join(text)

    def getresults(self, js):
        ct = getitem(js, "contents", "twoColumnSearchResultsRenderer", "primaryContents", "sectionListRenderer", "contents")
        if not ct:
            ct = getitem(js, "onResponseReceivedCommands", 0, "appendContinuationItemsAction", "continuationItems")

        resultlist = getitem(ct, ("itemSectionRenderer",), "itemSectionRenderer", "contents")
        cont = getitem(ct, ("continuationItemRenderer",), "continuationItemRenderer", "continuationEndpoint", "continuationCommand", "token")

        return resultlist, cont

    def recursesearch(self):
        resultlist, cont = self.getresults(getitem(self.cfg, ("xsrf_token",), "response"))
        while True:
            for item in resultlist:
                if video := item.get("videoRenderer"):
                    vid = getitem(video, "videoId")
                    pub = getitem(video, "publishedTimeText", "simpleText")
                    title = getitem(video, "title", "runs")
                    # title -> runs
                    # descriptionSnippet -> runs
                    # publishedTimeText -> simpleText
                    # lengthText -> simpleText
                    # viewCountText -> simpleText
                    # ownerText -> runs
                    print("%s - %s" % (vid, self.extractruns(title)))
                elif chan := item.get("channelRenderer"):
                    cid = getitem(chan, "channelId")
                    title = getitem(chan, "title", "simpleText")
                    # "videoCountText" -> runs
                    # subscriberCountText -> simpleText
                    # descriptionSnippet -> runs
                    print("%s - %s" % (cid, title))

            jstext = self.yt.getsearch(cont)
            js = json.loads(jstext)
            resultlist, cont = self.getresults(js)


class DetailReader:
    """
    Extract some details for a video from the config.
    """
    def __init__(self, args, yt, cfg):
        self.args = args
        self.yt = yt
        self.cfg = cfg

    def output(self):
        vd = getitem(self.cfg, ("playerResponse",), "playerResponse", "videoDetails")
        mf = getitem(self.cfg, ("playerResponse",), "playerResponse", "microformat", "playerMicroformatRenderer")
        twocol = getitem(self.cfg, ("response",), "response", "contents", "twoColumnWatchNextResults", "results", "results", "contents")
        sentiment = getitem(twocol, ("videoPrimaryInfoRenderer",), "videoPrimaryInfoRenderer", "sentimentBar", "sentimentBarRenderer", "tooltip")

        if not mf:
            print("microformat not found")
            return

        vc = int(mf.get("viewCount"))
        ls = cvseconds(mf.get("lengthSeconds"))
        pd = cvdate(mf.get("publishDate"))
        ud = cvdate(mf.get("uploadDate"))
        desc = getitem(mf, "description", "simpleText")

        vid = vd.get("videoId")

        title = getitem(mf, "title", "simpleText")
        owner = getitem(mf, "ownerChannelName")

        print("%s - %s" % (vid, title))
        print("By: %s" % (owner))
        print()
        print("viewcount: %d, length: %s, sentiment: %s, published: %s%s" % (vc, ls, sentiment, pd, "" if pd==ud else ", uploaded at: %s" % ud))
        print()
        print("%s" % desc)
        print()


class SubtitleReader:
    """
    class which can print a video's subtitles
    """
    def __init__(self, args, yt, cfg):
        self.args = args
        self.yt = yt
        self.cfg = cfg

    def languagematches(self, language, ct):
        """
        Match a captionTrack record to the language filter.
        """
        if language == 'asr' and ct.get('kind') == 'asr':
            return True
        if ct["name"]["simpleText"] == language:
            return True
        if ct["languageCode"] == language:
            return True

    def output(self):
        js = getitem(self.cfg, ("playerResponse",), "playerResponse")
        p = getitem(js, "captions", "playerCaptionsTracklistRenderer", "captionTracks")
            
        if not p:
            print("no subtitles found")
            return

        captiontracks = p

        # filter subtitles based on language
        if self.args.language:
            captiontracks = self.filtertracks(self.args.language, captiontracks)

        for ct in captiontracks:
            if len(captiontracks) > 1:
                print("###  %s ###" % ct["name"]["simpleText"])

            self.outputsubtitles(ct["baseUrl"])

            if len(captiontracks) > 1:
                print()

    def filtertracks(self, language, captiontracks):
        matchedtracks = defaultdict(list)
        for ct in captiontracks:
            if not self.languagematches(language, ct):
                continue

            matchedtracks[ct["languageCode"]].append(ct)

        filteredlist = []
        for lang, tracks in matchedtracks.items():
            if len(tracks) > 1:
                # prefer non automated translation
                tracks = filter(lambda ct:ct.get("kind") != "asr", tracks)
            filteredlist.extend(tracks)

        return filteredlist

    def outputsubtitles(self, cturl):
        ttxml = self.yt.httpreq(cturl)
        if self.args.debug:
            print("========== timedtext xml")
            print(ttxml.decode('utf-8'))
            print()
        tt = self.extracttext(ttxml)

        if self.args.srt:
            self.output_srt(tt)
        elif self.args.verbose:
            for t0, t1, txt in tt:
                print("%s  %s" % (self.formattime(t0), txt))
        else:
            for t0, t1, txt in tt:
                print(txt)

    @staticmethod
    def formattime(t):
        m = int(t/60) ; t -= 60*m
        h = int(m/60) ; m -= 60*h
        return "%d:%02d:%06.3f" % (h, m, t)

    @staticmethod
    def srttime(t):
        return SubtitleReader.formattime(t).replace('.', ',')

    @staticmethod
    def output_srt(tt):
        n = 1
        for t0, t1, txt in tt:
            print(n)
            print("%s --> %s" % (SubtitleReader.srttime(t0), SubtitleReader.srttime(t1)))
            print(txt)
            print()

    @staticmethod
    def unhtml(htmltext):
        """
        Removes html font tags, and decodes html entities
        """
        return html.unescape(re.sub(r'</?font[^>]*>', '', htmltext))

    def extracttext(self, xml):
        """
        Returns a list of tuples: time, endtime, text
        """
        lines = []
        tstart = None
        tend = None
        text = None
        def handle_begin_element(elem, attr):
            nonlocal text, tstart, tend
            if elem == 'text':
                text = ""
                tstart = float(attr.get('start'))
                tend = tstart + float(attr.get('dur'))

        def handle_end_element(elem):
            nonlocal text
            if elem == 'text':
                lines.append((tstart, tend, self.unhtml(text)))
                text = None
        def handle_data(data):
            nonlocal text
            if text is not None:
                text += data

        parser = ParserCreate()
        parser.StartElementHandler = handle_begin_element
        parser.EndElementHandler = handle_end_element
        parser.CharacterDataHandler = handle_data
        parser.Parse(xml, 1)

        return lines


class PlaylistReader:
    """
    class which can print a playlist's contents.
    """
    def __init__(self, args, yt, cfg):
        self.args = args
        self.yt = yt
        self.cfg = cfg

    def output(self):
        # ==== [                  'playlistVideoRenderer', 1, 'contents', 'playlistVideoListRenderer', 0, 'contents', 'itemSectionRenderer', 0, 'contents', 'sectionListRenderer', 'content', 'tabRenderer', 0, 'tabs', 'twoColumnBrowseResultsRenderer', 'contents', 'response', 1]
        # ==== ['gridVideoRenderer', 1, 'items', 'horizontalListRenderer', 'content', 'shelfRenderer', 0, 
        #                     'contents', 'itemSectionRenderer', 1, 'contents', 'sectionListRenderer', 'content', 'tabRenderer', 0, 
        #                     'tabs', 'twoColumnBrowseResultsRenderer', 'contents', 'response', 1]
        playlist = getitem(self.cfg, ("response",), "response", "contents", "twoColumnWatchNextResults", "playlist")
        if playlist:
            print("Title: %s" % getitem(playlist, "playlist", "title"))
            for entry in getitem(playlist, "playlist", "contents"):
                vid = getitem(entry, "playlistPanelVideoRenderer", "videoId")
                title = getitem(entry, "playlistPanelVideoRenderer", "title", "simpleText")
                length = getitem(entry, "playlistPanelVideoRenderer", "lengthText", "simpleText")
                if args.verbose:
                    print("%s - %s  %s" % (vid, length, title))
                else:
                    print("%s - %s" % (vid, title))
            return
        tabs = getitem(self.cfg, ("response",), "response", "contents", "twoColumnBrowseResultsRenderer", "tabs", 0, "tabRenderer", "content")
        ct1 = getitem(tabs, "sectionListRenderer", "contents", 0, "itemSectionRenderer", "contents", 0)
        playlist = getitem(ct1, "playlistVideoListRenderer")
        list_tag = "contents"
        entry_tag = "playlistVideoRenderer"
        if not playlist:
            playlist = getitem(ctl, "shelfRenderer", "content", 'horizontalListRenderer')
            list_tag = "items"
            entry_tag = "gridVideoRenderer"
        if playlist:
            cont = None
            for entry in playlist[list_tag]:
                vid = getitem(entry, entry_tag, "videoId")
                title = getitem(entry, entry_tag, "title")
                if vid and title:
                    print("%s - %s" % (vid, self.extracttext(title)))
                c = getitem(entry, "continuationItemRenderer", "continuationEndpoint", "continuationCommand", "token")
                if c:
                    cl = getitem(entry, "continuationItemRenderer", "continuationEndpoint", "clickTrackingParams")
                    cont = c, cl

            if not cont:
                cont = self.getcontinuation(playlist)
            while cont:
                browsejson = self.yt.browse(cont)
                if self.args.debug:
                    print("============ browse req")
                    print(browsejson.decode('utf-8'))
                    print()

                js = json.loads(browsejson)

                cont = None
                playlist = getitem(js, ("response",), "response", "continuationContents", "gridContinuation")
                if playlist:
                    for entry in getitem(playlist, "items"):
                        vid = getitem(entry, "gridVideoRenderer", "videoId")
                        title = getitem(entry, "gridVideoRenderer", "title")
                        print("%s - %s" % (vid, self.extracttext(title)))
                playlist = getitem(js, ("response",), "response", "continuationContents", "playlistVideoListContinuation")
                item_tag = "contents"
                if not playlist:
                    playlist = getitem(js, ("response",), "response", "onResponseReceivedActions", 0, "appendContinuationItemsAction", )
                    item_tag = "continuationItems"
                if playlist:
                    for entry in getitem(playlist, item_tag):
                        vid = getitem(entry, "playlistVideoRenderer", "videoId")
                        title = getitem(entry, "playlistVideoRenderer", "title")
                        if vid and title:
                            print("%s - %s" % (vid, self.extracttext(title)))
                        c = getitem(entry, "continuationItemRenderer", "continuationEndpoint", "continuationCommand", "token")
                        if c:
                            cl = getitem(entry, "continuationItemRenderer", "continuationEndpoint", "clickTrackingParams")
                            cont = c, cl

                if not playlist:
                    break
                if not cont:
                    cont = self.getcontinuation(playlist)

            return

    def extracttext(self, entry):
        return entry.get("simpleText") or "".join(r.get('text') for r in entry.get("runs"))


    def getcontinuation(self, p):
        p = getitem(p, "continuations", 0, "nextContinuationData")
        if not p:
            return
        return p["continuation"], p["clickTrackingParams"]


def parse_youtube_link(url):
    """
    Recognize different types of youtube urls:

    http://,   https://

    youtu.be/<videoid>[?list=<listid>]

    (?:www.)?youtube.com...

    /channel/<channelid>
    /c/<channelname>
    /playlist?list=<listid>
    /watch?v=<videoid> [&t=pos] [&list=<listid>]
    /watch/<videoid>
    /v/<videoid>
    /embed/<videoid>
    /user/<username>
    /watch_videos?video_ids=<videoid>,<videoid>,...
    /results?search_query=...
    """
    m = re.match(r'^(?:https?://)?(?:www\.)?(?:(?:youtu\.be|youtube\.com)/)?(.*)', url)
    if not m:
        raise Exception("youtube link not matched")

    path = m.group(1)

    if m := re.match(r'^user/([^/?]+)', path):
        yield 'username', m.group(1)
    elif m := re.match(r'^(\w+)/([A-Za-z0-9_-]+)(.*)', path):
        idtype = m.group(1)
        if idtype in ('v', 'embed', 'watch'):
            idtype = 'video'
        elif idtype in ('channel'):
            idtype = 'channel'
        elif idtype in ('c'):
            idtype = 'channelname'
        elif idtype in ('playlist'):
            idtype = 'playlist'
        else:
            raise Exception("unknown id type")

        idvalue = m.group(2)
        yield idtype, idvalue
        if idtype == 'channel':
            yield 'playlist', 'UU' + idvalue[2:]

        idargs = urllib.parse.parse_qs(m.group(3))
        if idvalue := idargs.get('v'):
            if idvalue[0]:
                yield 'video', idvalue[0]
        if idvalue := idargs.get('list'):
            if idvalue[0]:
                yield 'playlist', idvalue[0]

    elif m := re.match(r'^(v|embed|watch|channel|playlist)(?:\?(.*))?$', path):
        idtype = m.group(1)
        if idtype in ('v', 'embed', 'watch'):
            idtype = 'video'
        elif idtype in ('channel'):
            idtype = 'channel'
        elif idtype in ('playlist'):
            idtype = 'playlist'

        idargs = urllib.parse.parse_qs(m.group(2))
        if idvalue := idargs.get('v'):
            if idvalue[0]:
                yield 'video', idvalue[0]
        if idvalue := idargs.get('list'):
            if idvalue[0]:
                yield 'playlist', idvalue[0]

    elif m := re.match(r'^results\?(.*)$', path):
        idargs = urllib.parse.parse_qs(m.group(1))
        if idvalue := idargs.get('search_query'):
            if idvalue[0]:
                yield 'search', idvalue[0]

    elif m := re.match(r'^[A-Za-z0-9_-]+$', path):
        if len(path)==11:
            yield 'video', path
        else:
            yield 'playlist', path
     
    else:
        raise Exception("unknown id")

def channelurl_from_userpage(cfg):
    return getitem(cfg, ("response",), "response", "metadata", "channelMetadataRenderer", "channelUrl")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Extract Youtube comments')
    parser.add_argument('--debug', '-d', action='store_true', help='print all intermediate steps')
    parser.add_argument('--verbose', '-v', action='store_true', help='prefix each line with the timestamp')
    parser.add_argument('--comments', '-c', action='store_true', help='Print video comments')
    parser.add_argument('--subtitles', '-t', action='store_true', help='Print video subtitles')
    parser.add_argument('--language', type=str, help='Output only subtitles in the specified language')
    parser.add_argument('--playlist', '-l', action='store_true', help='Print playlist items')
    parser.add_argument('--info', '-i', action='store_true', help='Print video info')
    parser.add_argument('--srt', action='store_true', help='Output subtitles in .srt format.')
    parser.add_argument('--query', '-q', action='store_true', help='List videos matching the specified query')
    parser.add_argument('--livechat', action='store_true', help='Follow livechat contents')
    parser.add_argument('--replay', action='store_true', help='Print livechat replay')
    parser.add_argument('ytids', nargs='+', type=str, help='One or more Youtube URLs, or IDs, or a query')
    args = parser.parse_args()

    yt = Youtube(args)

    for url in args.ytids:
        if len(args.ytids) > 1:
            print("==>", url, "<==")
        if args.query:
            # note: the 'url' variable holds the query.
            # convert it to a query url so the parse link function can decode it.
            url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": url})

        # analyze url for id's, like videoid, channelid, playlistid or search query.
        for idtype, idvalue in parse_youtube_link(url):
            # reformat the url in a way that i am sure returns the right json data.

            if idtype == 'video':
                url = "https://www.youtube.com/watch?v=%s" % idvalue
            elif idtype == 'playlist':
                url = "https://www.youtube.com/playlist?list=%s" % idvalue
            elif idtype == 'channel':
                url = "https://www.youtube.com/channel/%s" % idvalue
            elif idtype == 'username':
                url = "https://www.youtube.com/user/%s" % idvalue
            elif idtype == 'search':
                url = "https://www.youtube.com/results?" + urllib.parse.urlencode({"search_query": idvalue})

            cfg = yt.getpageinfo(url)

            if idtype=='username':
                url = channelurl_from_userpage(cfg)
                args.ytids.append(url)
                # note: the new url is processed in next loop iteration.

            if args.comments and idtype=='video':
                cmt = CommentReader(args, yt, cfg)
                cmt.recursecomments()
            if args.subtitles and idtype=='video':
                txt = SubtitleReader(args, yt, cfg)
                txt.output()
            if (args.replay or args.livechat) and idtype=='video':
                txt = LivechatReader(args, yt, cfg, live=args.livechat)
                txt.recursechat()
            if args.playlist and idtype=='playlist':
                lst = PlaylistReader(args, yt, cfg)
                lst.output()
            if (args.playlist or args.query) and idtype == 'search':
                q = SearchReader(args, yt, cfg)
                q.recursesearch()
            if args.info and idtype=='video':
                lst = DetailReader(args, yt, cfg)
                lst.output()


if __name__ == '__main__':
    main()


