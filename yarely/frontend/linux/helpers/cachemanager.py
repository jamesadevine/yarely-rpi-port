__author__ = 'James'
from subprocess import Popen
from multiprocessing import Process,Manager
from yarely.frontend.linux.helpers.assetwrappers import \
    ImageAsset, BrowserAsset, PlayerAsset
from urllib.error import URLError
from threading import Lock
from urllib.request import urlopen
import re
import os
from subprocess import check_output


class cache_manager(object):
    def __init__(self,cache_path):
        print('Initialising Cache Manager')
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
        self.width_height=resolution.strip('+0+0')

    def prefetch_content_item(self, asset):
        content_file = asset.asset.get_files()[0]
        sources = content_file.get_sources()
        if not len(sources):
            print(
                'Could not get source URI at index 0'
            )
            return None

        for src in sources:
            content_src_uri = src.get_uri()

            # Look to see if this file should be precached
            if not asset.should_precache():
                # Don't precache, use the URI as it is
                return content_src_uri
            file_uri=content_src_uri.split('.')
            file_uri=str(file_uri[-2]+'.'+file_uri[-1])
            file_uri=file_uri.replace('/', '')
            # Precache content
            # Work out path to the content in the cache
            cache_path = os.path.join(
                self.cache_path,
                file_uri
            )
            #print ('FILE URI:'+file_uri)
            #print ('CACHE PATH:'+cache_path)
            if os.path.exists(cache_path):
                # Content already cached
                return cache_path
            else:
                #download file in background without blocking main thread
                if isinstance(asset,BrowserAsset) and not self.is_in_active_downloads(content_src_uri) and self.running_process.value<5:
                    self.increment_running_process()
                    print('downloading browser asset')
                    self.add_to_active_downloads(content_src_uri)
                    #if it's a page we use popen to save a screencap of that image
                    process=Process(target=self.download_page,args=(content_src_uri,cache_path,self.active_downloads_lock,))
                    process.daemon=True
                    process.start()
                elif not self.is_in_active_downloads(content_src_uri) and self.running_process.value<5:
                    self.increment_running_process()
                    print('downloading image or video asset')
                    self.add_to_active_downloads(content_src_uri)

                    #else use a traditional write buffer to download the resource.
                    process=Process(target=self.download_resource,args=(content_src_uri,cache_path,self.active_downloads_lock,))
                    process.daemon=True
                    process.start()
                elif self.is_in_active_downloads(content_src_uri):
                    self.cache_path
                    #print('IN ACTIVE DOWNLOADS ASDJAKDHKSAHDFJLKASHDFJALSHDFJHASDLFJKHALSDKJ')
                #else:
                    #print('Too many processes are running')
                return None
        return None

    def decrement_running_process(self):
        print('DECREMENTING RUNNING')
        self.running_process_lock.acquire()
        print(str(self.running_process.value))
        self.running_process.value-=1
        print(str(self.running_process.value))
        self.running_process_lock.release()

    def increment_running_process(self):
        print('Incrementing RUNNING')
        self.running_process_lock.acquire()
        print(str(self.running_process.value))
        self.running_process.value+=1
        print(str(self.running_process.value))
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

    def download_resource(self, uri,download_path,active_downloads_lock):
        #store resource in separate directory so that the scheduler doesn't try and read a bad resource...
        temp_path='/tmp/downloading'+download_path
        print('downloading to '+temp_path)
        print('downloading from: '+uri)
        try:
            filehandle = urlopen(uri)
            open(temp_path, 'wb').write(filehandle.read())
            print('Download complete - moving to actual cache: '+download_path)
            os.rename(temp_path,download_path)
            active_downloads_lock.acquire()
            del self.active_downloads[uri]
            active_downloads_lock.release()
            print('decrementing from process')
            self.decrement_running_process()
        except (URLError, IOError) as e:
            print('Failed to fetch resource from url: '+str(e))
            print('decrementing from process')
            self.decrement_running_process()

    def download_page(self, uri,download_path,active_downloads_lock):
        #store image of page in separate directory so that the scheduler doesn't try and read a bad resource...
        temp_path='/tmp/downloading'+download_path
        print('downloading to '+temp_path)
        process=Popen(['xvfb-run', '--server-args', '"-screen 0, '+str(self.width_height)+'x24"', 'cutycapt', '--url='+uri,'--out='+temp_path])
        process.wait()
        print('Download complete - moving to actual cache: '+download_path)
        os.rename(temp_path,download_path)
        active_downloads_lock.acquire()
        del self.active_downloads[uri]
        active_downloads_lock.release()
        print('decrementing from process')
        self.decrement_running_process()

