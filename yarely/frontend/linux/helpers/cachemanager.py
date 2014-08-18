__author__ = 'James'
from subprocess import Popen
import logging
from multiprocessing import Process,Manager
from yarely.frontend.linux.helpers.assetwrappers import \
    ImageAsset, BrowserAsset, PlayerAsset
from urllib.error import URLError
from threading import Lock
from urllib.request import urlopen
import re
import pexpect
import heapq
from datetime import datetime
import os
import time
from subprocess import check_output
from PIL import Image

log = logging.getLogger(__name__)

xvfb_run_bin='/usr/bin/xvfb-run'
URL_REFRESH_TIME=1800 #30 minutes
FILE_DELETION_TIME=1800 #30 minutes


class cache_manager(object):
    def __init__(self,cache_path):
        log.info('Initialising Cache Manager')
        self.cache_path=cache_path
        self.manager=Manager()
        if not os.path.exists('/tmp/downloading/'+self.cache_path):
          os.makedirs('/tmp/downloading/'+self.cache_path)
        #setup locks for shared state vars
        self.active_downloads_lock=Lock()
        self.running_process_lock=Lock()

        #set up shared state vars
        self.running_process=self.manager.Value('running_process_count',0)
        self.active_downloads=self.manager.dict()

        #get the current resolution geometry string
        resolution = re.search(
            '(\d{3,4}x\d{3,4}) @',
            str(check_output(['tvservice', '-s']).strip())
        ).group(1)

        #get just the resolution string (width/height in pixels)
        self.width=resolution.split('x')[0]
        self.height=resolution.split('x')[1]

        log.info('Initialising url removal')
        #start url removal and file deletion processes.
        url_removal_process=Process(target=self.remove_old_items)
        url_removal_process.daemon=True
        url_removal_process.start()

        log.info('Initialising old file deletion')
        file_deletion_process=Process(target=self.remove_old_items)
        file_deletion_process.daemon=True
        file_deletion_process.start()

    def prefetch_content_item(self, asset):
        content_file = asset.asset.get_files()[0]
        sources = content_file.get_sources()
        if not len(sources):
            log.debug(
                'Could not get source URI at index 0'
            )
            return None

        for src in sources:
            content_src_uri = src.get_uri()
            log.info('prefetching content item: '+content_src_uri)
            # Look to see if this file should be precached
            if not asset.should_precache():
                # Don't precache, use the URI as it is
                return content_src_uri
            if isinstance(asset,BrowserAsset):
                file_uri=content_src_uri.split('.')
                file_uri=str(file_uri[-3]+file_uri[-2]+file_uri[-1]+'.url.png')
                file_uri=file_uri.replace('/', '')
            else:
                file_uri=content_src_uri.split('.')
                file_uri=str(file_uri[-3]+file_uri[-2]+'.'+file_uri[-1])
                file_uri=file_uri.replace('/', '')
            # Precache content
            # Work out path to the content in the cache
            cache_path = os.path.join(
                self.cache_path,
                file_uri
            )
            #
            log.info ('ASSET: '+str(asset))
            log.info ('FILE URI:'+file_uri)
            log.info ('CACHE PATH:'+cache_path)
            if os.path.exists(cache_path):
                # Content already cached
                return cache_path
            else:
                #download file in background without blocking main thread
                if isinstance(asset,BrowserAsset) and not self.is_in_active_downloads(content_src_uri) and self.running_process.value<5:
                    self.increment_running_process()
                    log.info('downloading browser asset')
                    self.add_to_active_downloads(content_src_uri)
                    #if it's a page we use popen to save a screencap of that image
                    self.download_page(content_src_uri,cache_path,self.active_downloads_lock,)
                elif isinstance(asset,ImageAsset) and not self.is_in_active_downloads(content_src_uri) and self.running_process.value<5:
                    self.increment_running_process()
                    log.info('downloading image')
                    self.add_to_active_downloads(content_src_uri)

                    #else use a traditional write buffer to download the resource.
                    process=Process(target=self.download_image,args=(content_src_uri,cache_path,self.active_downloads_lock,))
                    process.daemon=True
                    process.start()
                elif isinstance(asset,PlayerAsset) and not self.is_in_active_downloads(content_src_uri) and self.running_process.value<5:
                    self.increment_running_process()
                    log.info('downloading video')
                    self.add_to_active_downloads(content_src_uri)

                    #else use a traditional write buffer to download the resource.
                    process=Process(target=self.download_video,args=(content_src_uri,cache_path,self.active_downloads_lock,))
                    process.daemon=True
                    process.start()
        return None

    def decrement_running_process(self):
        self.running_process_lock.acquire()
        log.info(str(self.running_process.value))
        self.running_process.value-=1
        log.info(str(self.running_process.value))
        self.running_process_lock.release()

    def increment_running_process(self):
        self.running_process_lock.acquire()
        log.info(str(self.running_process.value))
        self.running_process.value+=1
        log.info(str(self.running_process.value))
        self.running_process_lock.release()

    def add_to_active_downloads(self,uri):
        self.active_downloads_lock.acquire()
        self.active_downloads[uri]=0
        self.active_downloads_lock.release()

    def is_in_active_downloads(self,uri):
        self.active_downloads_lock.acquire()
        if uri in self.active_downloads.keys():
            self.active_downloads_lock.release()
            return True
        self.active_downloads_lock.release()
        return False

    def download_video(self, uri,download_path,active_downloads_lock):
        #store resource in separate directory so that the scheduler doesn't try and read a bad resource...
        temp_path='/tmp/downloading'+download_path
        log.info('downloading to '+temp_path)
        log.info('downloading from: '+uri)
        try:
            filehandle = urlopen(uri)
            open(temp_path, 'wb').write(filehandle.read())
            log.info('Download complete - moving to actual cache: '+download_path)
            try:
                os.rename(temp_path,download_path)
            except:
                log.info('rename failed - try again later')
            active_downloads_lock.acquire()
            del self.active_downloads[uri]
            active_downloads_lock.release()
            log.info('decrementing from process')
            self.decrement_running_process()
        except (URLError, IOError) as e:
            log.info('Failed to fetch resource from url: '+str(e))
            log.info('decrementing from process')
            self.decrement_running_process()


    def download_image(self, uri,download_path,active_downloads_lock):
        #store resource in separate directory so that the scheduler doesn't try and read a bad resource...
        temp_path='/tmp/downloading'+download_path
        log.info('downloading to '+temp_path)
        log.info('downloading from: '+uri)
        try:
            filehandle = urlopen(uri)
            open(temp_path, 'wb').write(filehandle.read())
            log.info('Download complete')
            try:
                img = Image.open(temp_path).convert('RGB')
                if img.size[0]!= int(self.width) and img.size[1]!= int(self.height):
                    log.info('Image opened... resizing to: '+str(int(self.width))+str(int(self.height)))
                    img = img.resize((int(self.width),int(self.height)), Image.ANTIALIAS)
                    log.info('Image resized... saving to: '+temp_path.split('.')[-1])
                    img.save(temp_path)
                del img
                log.info('moving to: '+download_path)
                os.rename(temp_path,download_path)
            except:
                log.info('unable to save - moving on.')
            active_downloads_lock.acquire()
            del self.active_downloads[uri]
            active_downloads_lock.release()
            log.info('decrementing from process')
            self.decrement_running_process()
        except (URLError, IOError) as e:
            log.info('Failed to fetch resource from url: '+str(e))
            log.info('decrementing from process')
            self.decrement_running_process()

    def download_page(self, uri,download_path,active_downloads_lock):
        #store image of page in separate directory so that the scheduler doesn't try and read a bad resource...
        temp_path='/tmp/downloading'+download_path
        log.info('downloading to '+temp_path)
        process=Popen(['xvfb-run','-s -screen 0, '+str(self.width)+'x'+str(self.height)+'x24', 'cutycapt', '--url='+uri,'--delay=10000','--min-width='+str(self.width), '--min-height='+str(self.height),'--out='+temp_path])
        process.wait()
        log.info('Download complete - moving to actual cache: '+download_path)
        try:
            os.rename(temp_path,download_path)
        except:
            log.info('rename failed - try again later')

        active_downloads_lock.acquire()
        del self.active_downloads[uri]
        active_downloads_lock.release()
        log.info('decrementing from process')
        self.decrement_running_process()

    #this function runs in the background and removes 20 items whenever it sees that the diskspace usage >80%
    def remove_old_items(self):
        while True:
            statvfs = os.statvfs(self.cache_path)
            disk_size=statvfs.f_frsize * statvfs.f_blocks
            free_space=statvfs.f_frsize * statvfs.f_bavail
            percentage_used=free_space/disk_size*100

            if percentage_used>80:
                old_files=self.oldest_files_in_tree(count=20)
                while old_files:
                    os.remove(old_files.pop())
            time.sleep(FILE_DELETION_TIME)

    def oldest_files_in_tree(self, count=1, extension=('.jpg','.png','.jpeg','.url.png')):
        return heapq.nsmallest(count,
            (os.path.join(dirname, filename)
            for dirname, dirnames, filenames in os.walk(self.cache_path)
            for filename in filenames
            if filename.endswith(extension)),
            key=lambda fn: os.stat(fn).st_mtime)

    def check_time(self,filename,time):
        last_modified=datetime.fromtimestamp(os.stat(filename).st_mtime)
        current_time=datetime.now()
        if (current_time-last_modified).seconds>time:
            return True
        return False

    def files_with_last_modified(self,time=URL_REFRESH_TIME, count=1, extension=('.jpg','.JPG','.png','.jpeg','.url.png')):
        return heapq.nsmallest(count,
            (os.path.join(dirname, filename)
            for dirname, dirnames, filenames in os.walk(self.cache_path)
            for filename in filenames
            if filename.endswith(extension) and self.check_time(os.path.join(dirname, filename),URL_REFRESH_TIME)),
            key=lambda fn: os.stat(fn).st_mtime)

    def remove_urls(self):
        while True:
            old_files=self.files_with_last_modified(count=100)
            while old_files:
                os.remove(old_files.pop())
            time.sleep(URL_REFRESH_TIME)