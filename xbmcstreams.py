#!/usr/bin/env python
"""
xbmcstreams - wrapper and CLI for XBMC FTP and HTTP control interfaces

- can save <3'ed stream and track titles to a 'sweet_file'

"""

import csv
import datetime
import os
import sys
import mechanize
import cmdloop
import logging
from BeautifulSoup import BeautifulSoup as BS
from urllib2 import HTTPError
from ftplib import FTP
from time import sleep

HOST='192.168.0.0'
FTP_USER='xbmc'
FTP_PASSWD='xbmc'
HTTP_USER=FTP_USER
HTTP_PASSWD=FTP_PASSWD

DI_USER=''
DI_PASSWD=''

SWEET_FILE='sweet.csv'


class XBMC(object):
    """
    See: http://www.xbmc.org/trac/browser/branches/xbox-test/guilib/Key.h
    """

    def __init__(self,
            host=HOST,
            ftp_user=FTP_USER,
            ftp_passwd=FTP_PASSWD,
            http_user=HTTP_USER,
            http_passwd=HTTP_PASSWD):
        self.host = host
        self.ftp_user = ftp_user
        self.ftp_passwd = ftp_passwd
        self.http_user = http_user
        self.http_passwd = http_passwd
        self.url = lambda x: os.path.join("http://%s" % self.host, x or '')
        self.cmd_url = lambda x: 'http://%s/xbmcCmds/xbmcHttp?command=%s' % (self.host,x)
        self.b = mechanize.Browser()
        self.b.set_handle_robots(False)
        self.b.add_password("http://%s/" % host,http_user,http_passwd)

    def cmd(self,cmd):
        self.b.open(self.cmd_url(cmd))

    def play(self, url):
        print "Loading %s in XBMC..." % url
        ftp = FTP(self.host, self.ftp_user, self.ftp_passwd)
        ftp.login(self.ftp_user, self.ftp_passwd)
        ftp.sendcmd('site PlayMedia %s' % url)
        ftp.quit()
        #self.b.open(self.cmd_url("PlayFile(%s)" % url))  # (Doesn't block)
        #print "Done."

    def lastfm_love(self):
        ftp = FTP(self.host, self.ftp_user, self.ftp_passwd)
        ftp.login(self.ftp_user, self.ftp_passwd)
        ftp.sendcmd('site LastFM.Love')
        ftp.quit()

    def get_now_playing(self):
        b = self.b
        b.open(self.cmd_url("GetCurrentlyPlaying"))
        page = ''.join(b.response().readlines())
        return dict(map(lambda x: x.strip().split(':',1), page.split('<li>')[1:-1]))

    def mute(self):
        self.cmd("Mute()")

    def volume(self,level):
        self.cmd("SetVolume(%d)" % level)

    def stop(self):
        self.cmd("Stop()")

    def next(self):
        self.cmd("PlayNext()")

    def prev(self):
        self.cmd("PlayPrev()")

    def up(self):
        self.cmd("SendKey(270)")

    def down(self):
        self.cmd("SendKey(271)")

    def left(self):
        self.cmd("SendKey(272)")

    def right(self):
        self.cmd("SendKey(273)")

    def toggle_fullscreen(self):
        self.cmd("Action(18)") #258

    def toggle_info(self):
        self.cmd("Action(11)")

    def shutdown(self):
        self.cmd("Shutdown()")

class DiFm(object):
    def __init__(self, user=DI_USER, passwd=DI_PASSWD):
        self.user = user
        self.passwd = passwd
        self.b = mechanize.Browser()
        self.streams = {}
        self.logged_in = False

    def login(self):
        b = self.b
        b.open("http://di.fm")
        b.select_form(nr=0)
        b['amember_login'] =  self.user
        b['amember_pass'] = self.passwd

        try:
            # Return response obj
            b.submit()
            self.logged_in = True
            return b.response()
        except HTTPError, e:
            sys.exit("post failed: %d: %s" % (e.code, e.msg))

    def get_streams(self,response=None):
        """
        @return: streams as [
            {'title':None,
            'nowplaying':None,
            'link':None
            }, ...]
        """
        if not self.logged_in:
            response = self.login()

        if not response:
            self.b.open("http://di.fm")
            response = self.b.response()

        html = ''.join(response.readlines())

        # Confirm "Welcome to DI Premium" in page test
        if "Welcome to DI Premium" not in html:
            raise Exception("Not getting the premium page")

        page = BS(html)

        streams = []

        for r in page.findAll('tr'):
            stream_links = r.findAll('img',attrs={'src':'/pro/images/blue_256k.gif'})
            if stream_links:
                stream = {'link_mp3_256':stream_links[0].parent['href']}
                stream['title'] = stream['link_mp3_256'].split('/')[2]

                try:
                    cell_contents = r.find('span',attrs={'class':'text_trackname'}).contents
                    print "#"*20, "\n", len(cell_contents), "\n", cell_contents
                    stream['now_playing'] = cell_contents[-1].strip()
                    streams.append(stream)
                except AttributeError:
                    logging.debug("Couldn't get now playing info for %s" % stream['title'])
                    pass
                except IndexError:
                    logging.debug("Couldn't get now playing info for %s" % stream['title'])
                    pass
                except TypeError:
                    logging.debug("Couldn't get now playing info for %s" % stream['title'])
                    pass


        self.streams = streams = dict(enumerate(streams))
        return streams

    def stream_by_name(self,name):
        if not self.streams:
            logging.debug("No streams loaded yet")
            raise KeyError

        for i,stream in self.streams.items():
            if stream['title'].startswith(name):
                return stream

        raise KeyError

class ConsoleGui(cmdloop.CommandLoop):
    PS1=">>"
    def __init__(self,sweet_file=SWEET_FILE):
        self.xbmc = XBMC()
        self.difm = DiFm()
        self.sweet = file(sweet_file,'w+')
        self.sweet_csv = csv.writer(self.sweet)

    def _onLoopStart(self):
        """
        Login and retrieve streams list on startup
        """
        pass
        #self.print_streams(streams=self.difm.get_streams(self.difm.login()))

    def play_stream(self,stream):
        url = ''.join(['shout://di.fm',stream['link_mp3_256']])
        self.xbmc.play(url)
        sleep(2)
        self.xbmc.toggle_fullscreen()
        self.nowplayingCmd()

    @cmdloop.aliases('p','play')
    @cmdloop.shorthelp('play a stream')
    @cmdloop.usage('play [STREAM]')
    def playCmd(self,flags,args):
        if len(args) != 1:
            raise cmdloop.InvalidArguments

        cmdname = args[0]

        if not self.difm.streams:
            self.difm.get_streams()

        try:
            self.play_stream(self.difm.streams[int(cmdname)])
            return None
        except ValueError:
            pass
        except KeyError:
            print "Couldn't find a '%s' in the streams list" % cmdname
            return None

        try:
            self.play_stream(self.difm.stream_by_name(cmdname))
            return None
        except KeyError:
            print "Could't find a '%s' in the streams list" % cmdname
            pass

    @cmdloop.aliases('r','reload')
    @cmdloop.shorthelp('reload stream list')
    def printStreamsCmd(self,flags=None,args=None,streams=None):
        if not streams:
            streams = self.difm.get_streams()
        for i,stream in sorted(streams.items()):
            print '[%.2d] %-20s :: %s' % (i, stream['title'], stream['now_playing'])

    @cmdloop.aliases('l','list')
    @cmdloop.shorthelp('reprint cached streams list')
    def printStreamsCachedCmd(self,flags,args):
        self.printStreamsCmd(streams=self.difm.streams)

    @cmdloop.aliases('i','info')
    @cmdloop.shorthelp('get now playing info')
    def nowplayingCmd(self,flags=None,args=None):
        np = self.xbmc.get_now_playing()
        print "Now Playing: %s - %s [%s]" % (np.get('Artist'), np.get('Title'), np.get('Album'))

    @cmdloop.aliases('m','mute')
    @cmdloop.shorthelp('mute')
    def muteCmd(self,flags,args):
        self.xbmc.mute()

    @cmdloop.aliases('n','next')
    @cmdloop.shorthelp('next')
    def nextCmd(self,flags,args):
        self.xbmc.next()

    @cmdloop.aliases('prev','last','back')
    @cmdloop.shorthelp('prev')
    def prevCmd(self,flags,args):
        self.xbmc.prev()

    @cmdloop.aliases('s','stop')
    @cmdloop.shorthelp('stop')
    def stopCmd(self,flags,args):
        self.xbmc.stop()

    @cmdloop.aliases('v','vol','volume')
    @cmdloop.shorthelp('set volume')
    @cmdloop.usage('volume [VOLUME]')
    def volumeCmd(self,flags,args):
        if len(args) > 1:
            raise cmdloop.InvalidArguments
        try:
            vol = int(args[0])
        except:
            raise cmdloop.InvalidArguments

        self.xbmc.volume(vol)

    @cmdloop.aliases('sweet','dig','love','<3')
    @cmdloop.shorthelp('Log the currently playing track')
    def sweetCmd(self,flags,args):
        np = self.xbmc.get_now_playing()
        self.sweet_csv.writerow([
            datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'),
            np.get('Artist'),
            np.get('Title'),
            np.get('Album')
        ])
        self.sweet.flush()

    def _unknownCommand(self, cmdname, flags, args):
        try:
            self.play_stream(self.difm.streams[int(cmdname)])
            return None
        except ValueError:
            pass
        except KeyError:
            print "Couldn't find a '%s' in the streams list" % cmdname
            return None

        try:
            self.play_stream(self.difm.stream_by_name(cmdname))
            return None
        except KeyError:
            print "Could't find a '%s' in the streams list" % cmdname
            pass

        print >> self.OUT, "Error: %s: command not found (and not in the streams list)" % cmdname

    @cmdloop.aliases('x','quit','q')
    def quitCmd(self, flags, args):
        '''
        Quit the environment.
        '''
        raise cmdloop.HaltLoop


if __name__=="__main__":
    from optparse import OptionParser

    op = OptionParser()
    op.add_option("-s","--stream",dest="stream",help="Play Stream (URL)",action="store")
    op.add_option("-i","--interactive",dest="interactive",help="Launch the interactive console",action="store_true",default=False)
    op.add_option("-t","--test",dest="test",help="Play a constant stream link",action="store")

    (opts,args) = op.parse_args()

    console = ConsoleGui()

    if opts.stream:
        x = XBMC()
        x.play(opts.stream)

    elif opts.interactive:
        console.runLoop()

    else:
        cmd = ' '.join(args)
        console.pushCommandLine('quit')
        console.pushCommandLine(cmd)
        console.runLoop(preamble=False,help=False)
