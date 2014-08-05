# Standard library imports
import logging
import os
import random
import threading
import time
import queue
from subprocess import Popen
from threading import Lock
from urllib.error import URLError
from urllib.request import urlopen
import xml.etree.ElementTree as ET

# Third party imports
import zmq

# Local (Yarely) imports
from yarely.frontend.core import platform
from yarely.frontend.core.helpers.base_classes.constraint import \
    PriorityConstraint, PriorityConstraintCondition, \
    PlaybackConstraint, PreferredDurationConstraint
from yarely.frontend.core.subscriptions.subscription_parser import \
    XMLSubscriptionParser, XMLSubscriptionParserError, ContentItem, ContentDescriptorSet
from yarely.frontend.core.helpers.base_classes import ApplicationWithConfig
from yarely.frontend.core.helpers.base_classes.zmq_rpc import ZMQRPC
from yarely.frontend.core.helpers.execution import application_loop
from yarely.frontend.core.helpers.zmq import ZMQ_ADDRESS_INPROC, \
    ZMQ_DISPLAYCONTROLLER_REP_PORT, ZMQ_ADDRESS_LOCALHOST, \
    ZMQ_SOCKET_LINGER_MSEC, ZMQ_RENDERER_REQ_PORT, \
    ZMQ_SENSORMANAGER_REQ_PORT, ZMQ_SUBSMANAGER_REQ_PORT

# Platform specific render monkeys
from yarely.frontend.linux.content.rendering.viewer import Renderers
from yarely.frontend.linux.helpers.assetwrappers import \
    ImageAsset, BrowserAsset, PlayerAsset
from yarely.frontend.linux.helpers.cachemanager import \
    cache_manager

from yarely.frontend.linux.content.rendering.handlers.browser import Browser
from yarely.frontend.linux.content.rendering.handlers.player import Player
from yarely.frontend.linux.content.rendering.handlers.image import Image

# For working out what we're running on
from sys import exit, platform, stdout

log = logging.getLogger(__name__)

DEFAULT_TIME_TO_SHOW = 5     # minimum default time renderer can show content.
TIME_TO_SLEEP = 2            # default value to sleep if constraints not met
WARN_NO_REPLY = "No reply generated in ZMQ request handler, reply with error."
SENSOR_LIFETIME = 30         # seconds
DEFAULT_SCREEN_WIDTH = 1024
DEFAULT_SCREEN_HEIGHT = 768
STREAM_DURATION = 7200
STREAM_ON_LEEWAY = 5         # (seconds) Keep display on while stream runs

ZMQ_SENSORMANAGER_ADDR = ZMQ_ADDRESS_LOCALHOST.format(
    port=ZMQ_SENSORMANAGER_REQ_PORT
)
ZMQ_SUBSMANAGER_ADDR = ZMQ_ADDRESS_LOCALHOST.format(
    port=ZMQ_SUBSMANAGER_REQ_PORT
)
ZMQ_RENDERER_ADDR = ZMQ_ADDRESS_LOCALHOST.format(port=ZMQ_RENDERER_REQ_PORT)

YARELY_MODULE_STARTER = os.path.join(
    os.path.abspath(__file__)[:-len('frontend/core/scheduler/scheduler.py')],
    'frontend/linux/content/rendering/viewer.py'
)

RENDERER_COMMAND_LINE_ARGS = {
    'application/pdf': {'module': '.image', 'param_type': 'path',
                        'precache': True, 'stream': False},
    'image': {'module': '.image', 'param_type': 'path', 'precache': True,
              'stream': False},
    'text': {'module': '.web', 'param_type': 'uri', 'precache': False,
             'stream': False},
    'video': {'module': '.qtmovie', 'param_type': 'uri', 'precache': True,
              'stream': False},
    'video/vnd.vlc': {'module': '.vlc', 'param_type': 'uri',
                      'precache': False, 'stream': True},
}

DISPLAY_ON_XML = (
    "<request token='UNUSED'><display-on until='{timestamp}'/></request>"
)

DISPLAY_RECEIVER_ENDPOINT = ZMQ_ADDRESS_LOCALHOST.format(
    port=ZMQ_DISPLAYCONTROLLER_REP_PORT
)
REQUEST_TIMEOUT = 2500
REQUEST_RETRIES = 1
QUEUE_TIMEOUT = 1
_TERMINATION_MARKER = object()

# Handy utility function to flatten recursive lists
# Taken from:
# http://stackoverflow.com/questions/5409224/python-recursively-flatten-a-list
def flatten(x):
    """Recursively flatten a list and any sublists.
       Usage: list(flatten(a)).

    """
    try:
        it = iter(x)
    except TypeError:
        yield x
    else:
        for i in it:
            for j in flatten(i):
                yield j


class DisplayClient():
    def __init__(self):
        self.context = zmq.Context(1)
        self.poll = zmq.Poller()
        self._make_client()
        self.msg_queue = queue.Queue()   # Q of infinite size
        self.queue_processor = threading.Thread(target=self._handle_queue)
        self.queue_processor.daemon = True
        self.queue_processor.start()

    def _make_client(self):
        self.client = self.context.socket(zmq.REQ)
        self.client.connect(DISPLAY_RECEIVER_ENDPOINT)
        self.poll.register(self.client, zmq.POLLIN)

    def send_request(self, request):
        self.client.send_unicode(request)
        expect_reply = True
        while expect_reply:
            socks = dict(self.poll.poll(REQUEST_TIMEOUT))
            if socks.get(self.client) == zmq.POLLIN:
                reply = self.client.recv()
                if not reply:
                    break
                else:
                    expect_reply = False
                    self.client.setsockopt(zmq.LINGER, 0)
                    self.client.close()
                    self.poll.unregister(self.client)
                    self._make_client()
            else:
                expect_reply = False
                self.client.setsockopt(zmq.LINGER, 0)
                self.client.close()
                self.poll.unregister(self.client)
                self._make_client()

    def _handle_queue(self):
        while True:
            # Send a message from the message queue
            try:
                qitem = self.msg_queue.get(
                    timeout=QUEUE_TIMEOUT
                )

                # First check for termnation
                if qitem is _TERMINATION_MARKER:
                    break

                # We've not been asked to terminate, so send
                # the message.
                self.send_request(qitem)
            except queue.Empty:
                pass


class Scheduler(threading.Thread, ZMQRPC):
    """ Creates a schedule list based on content_items and after
        validating the time_constraint, the content_item is passed
        to the renderer.

    """
    def __init__(self, etree=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self.render_process=None
        self.scheduler_event_thread = threading.Event()
        self.refresh_schedules_softinterrupt = threading.Event()
        self.ignore_scheduler = 0
        self.etree = etree
        self.web_requests = dict()
        self._current_priority_level = None
        self._previous_priority_level = None
        self._current_content_items = []
        self._incoming_set_of_items = []
        self._playlist_update_mutex = Lock()
        self.now_playing = None
        self.new_etree = None
        self.zmq_scheduler_req_addr = ZMQ_SUBSMANAGER_ADDR
        self.zmq_context_req = zmq.Context()
        self.zmq_reply_socket = None
        self.web_requests_updated = False
        self.executing_renderers = list()
        self.renderers_waiting_for_termination = list()
        self.screen_width = (
            int(os.environ['SCREEN_WIDTH'])
            if 'SCREEN_WIDTH' in os.environ else DEFAULT_SCREEN_WIDTH
        )
        self.screen_height = (
            int(os.environ['SCREEN_HEIGHT'])
            if 'SCREEN_HEIGHT' in os.environ else DEFAULT_SCREEN_HEIGHT
        )
        log.info('SCREEN WIDTH: ' + str(self.screen_width))
        log.info('SCREEN HEIGHT: ' + str(self.screen_height))
        self.display_client = DisplayClient()

    def _generate_params(self, params):
        params_root = ET.Element(tag='params')
        param = ET.Element(
            tag='param', attrib={'name': 'token', 'value': 'UNUSED'}
        )
        params_root.append(param)
        for key, value in params.items():
            param = ET.Element(
                tag='param', attrib={'name': key, 'value': value}
            )
            params_root.append(param)
        return params_root

    def parse_content_descriptor_set(self, root_cds, flatten=True):
        """ Create a list of content items """
        priority_levels = reversed(
            range(len(PriorityConstraint.ALL_PRIORITIES))
        )
        for priority_level in priority_levels:
            condition = PriorityConstraintCondition(priority_level)
            log.debug(
                'priority {pri} root_cds {rcds} and len is {len}'.format(
                    pri=priority_level, rcds=str(root_cds), len=len(root_cds)
                )
            )

            playlists = []
            for root_element in root_cds:
                if hasattr(root_element, 'get_content_items'):
                    playlists += root_element.get_content_items(
                        condition=condition, flatten=flatten
                    )
                else:
                    playlists.append(root_element)
            log.debug(
                'Playlists at priority level {level} is len {len}'.format(
                    len=len(playlists), level=priority_level
                )
            )
            if len(playlists):
                log.info(
                    'Found {len} playlists at priority level {level}'.format(
                        len=len(playlists), level=priority_level
                    )
                )

                self._previous_priority_level = self._current_priority_level
                self._current_priority_level = priority_level
                break

        return playlists

    def process_subscription(self):
        """
           Extracts xml to get content_item schedule and send schedule
           list to renderer.
        """
        if self.etree is None or len(self.web_requests):

            log.debug('No etree or web requests')
            ignore_until = self.ignore_scheduler + SENSOR_LIFETIME
            if ignore_until > time.time() and len(self.web_requests):
                self.renderer_override()
        else:
            log.debug('Got etree')
            self.process_to_renderer()

    def renderer_override(self):
        if not self.web_requests_updated:
            return
        self.web_requests_updated = False

        _web_items=list(self.web_requests[key][0] for key in self.web_requests)

        for content in _web_items:
            asset=self.determine_asset(content)
            self.now_playing=asset
            content_src_uri = self.cache_manager.prefetch_content_item(asset)
            if content_src_uri is None:
                # Can't fetch this now, move it to the end and try
                # the next content item
                _web_items.append(_web_items.pop(0))

                continue

            while len(self.executing_renderers):
                    renderer = self.executing_renderers.pop()
                    log.debug('terminating ' + repr(renderer.pid))
                    renderer.terminate()

            asset.set_uri(content_src_uri)
            # Start buffering content
            asset.prepare()

            first_item_duration = self.get_duration_for(content)


            # Sleep for the content duration
            if first_item_duration is not None:
                # Normal content with a duration
                now = time.time()
                end_time = now + first_item_duration

                # Allow display to stay for 2x duration of content
                self.display_client.msg_queue.put_nowait(
                    DISPLAY_ON_XML.format(
                        timestamp=end_time
                    )
                )

                asset.play()

                while (
                    now < end_time and (
                        self.ignore_scheduler + SENSOR_LIFETIME
                    ) <= now and
                    not self.scheduler_event_thread.is_set()
                ):
                    # Sleep for up to 1 sec
                    try:
                        time.sleep(min(1, end_time - time.time()))
                    except IOError:
                        pass
                    now = time.time()

                    log.debug(
                        "Time remaining {}".format(end_time - now)
                    )


    def get_ratio_for(self, playlist):
        """Lookup the playback constraint (ratio) for this content item"""

        # Get the head of the playlist, find their playback constraints
        ratio_constraints = [
            cstrnt.get_unscaled_ratio()
            for cstrnt in playlist[0].get_constraints()
            if isinstance(cstrnt, PlaybackConstraint)
        ]
        log.debug('ratio_constraints = {rc}'.format(rc=ratio_constraints))
        ratio_constraints = [ratio for ratio in ratio_constraints if ratio]
        log.debug('ratio_constraints = {rc}'.format(rc=ratio_constraints))

        return (max(ratio_constraints)
                if len(ratio_constraints)
                else None)

    def order_by_constraint(self, playlist):
        """Lookup the playback constraint (ratio) for this content item"""

        # Get the head of the playlist, find their playback constraints
        # Recurse down to try to avoid playlists getting ordered more than once
        if isinstance(playlist, ContentItem):
            return [
                cstrnt.get_order()
                for cstrnt in playlist.get_parent().get_constraints(False)
                if isinstance(cstrnt, PlaybackConstraint)
            ]

        # Not an item, so feed items into recursive function
        order_constraints = []
        for item in playlist:
            order_constraints = self.order_by_constraint(item)
            if isinstance(item, ContentItem):
                break

        # Back from getting order of parent, so now work out what to do with
        # the playlist
        log.debug(
            'order_constraints = {oc}'.format(oc=repr(order_constraints))
        )
        if order_constraints:
            if 'random' in order_constraints:
                random.shuffle(playlist)
            elif 'reverse' in order_constraints:
                playlist.reverse()

    def get_duration_for(self, item):
        """Lookup the duration constraint (ratio) for this content item"""

        if item is None:
            return 0

        duration_constraints = [
            float(cstrnt) for cstrnt in item.get_constraints()
            if isinstance(cstrnt, PreferredDurationConstraint)
        ]
        return (
            max(duration_constraints)
            if len(duration_constraints) else self.content_duration
        )

    def determine_asset(self, content_item):
        """Work out which asset type (renderer wrapper)
           this content type requires
        """
        simple_content_type = content_item.get_content_type().split('/')[0]
        return {
            'image': ImageAsset(content_item, self.renderers),
            'text': BrowserAsset(content_item, self.renderers),
            'video': PlayerAsset(content_item, self.renderers)
        }.get(simple_content_type, None)


    def process_to_renderer(self):
        """ Content_item passed to renderer if time contraint is valid. """
        sleep_counter = 0

        self._playlist_update_mutex.acquire()
        self._current_content_items = self._incoming_set_of_items[:]
        self._playlist_update_mutex.release()

        msg = 'process_to_renderer - schedule list has {len} playlists'
        log.info(msg.format(len=len(self._current_content_items)))

        # Think we can get to the parent to classify each item using
        #     get_parent() - should be able to work from this
        # Set up the following:
        # list of lists for each content set, c.f. q = [[10, 10, 30],
        #     [10, 10, 5], [10, 100]]
        # ratios of airtime for each content set, c.f. p = [1,.5,.1]
        # leaky buckets for each content set, c.f. b = [0, 0, 0]
        # playcounts for monitoring purposes, c.f. pl = [0, 0, 0]

        # Split the schedule back into the contentsets - yes, I know
        # this is crazy, but I am avoiding trying to rewrite this
        # properly changing contentset functionality
        ratio_for = [
            self.get_ratio_for(playlist)
            for playlist in self._current_content_items
        ]
        buckets = [0] * len(self._current_content_items)
        log.debug('ratio_for {rf}'.format(rf=str(ratio_for)))

        num_playlists = len(self._current_content_items)

        # Balance the presentation ratios across channels that don't specify it
        airtime_specified = [ratio for ratio in ratio_for if ratio]

        num_with_specified_ratios = len(airtime_specified)

        # What if the sum adds up to more than one?
        max_specified_ratio = sum(airtime_specified)
        airtime_remaining = 1 - max_specified_ratio

        # They've specified too much airtime (>100%) or all the airtime
        # and there are playlists without airtime allocated
        if max_specified_ratio > 1 or \
           max_specified_ratio == 1 and \
           num_playlists > num_with_specified_ratios:
            # Rescale to 80% if there are other channels to consider,
            # else rescale to 100%
            specified_proportion = .8 if (
                num_playlists > num_with_specified_ratios) else 1
            scale_by = specified_proportion / max_specified_ratio
            ratio_for = (
                [new_r * scale_by if new_r else None for new_r in ratio_for])

            log.debug(
                'specified ratios > 1, '
                'rescaling by {r} to ratio_for {rf}'.format(
                    r=scale_by, rf=str(ratio_for)
                )
            )
            airtime_remaining = 1 - specified_proportion

        try:
            airtime_proportion = airtime_remaining / (
                num_playlists - num_with_specified_ratios
            )
        except ZeroDivisionError:
            # All channels have specified proportions,
            # or there are no content sets
            airtime_proportion = 0

        ratio_for = [
            ratio if ratio else airtime_proportion for ratio in ratio_for
        ]
        log.debug(
            'airtime ratios {ratio_list}'.format(ratio_list=str(ratio_for))
        )

        # Iterate round the playlists
        while (not self.scheduler_event_thread.is_set() and
               not self.refresh_schedules_softinterrupt.is_set()
               and len(self._current_content_items)):
            # need to credit buckets to make sure something can progress every
            # iteration,
            # i.e. to avoid gaps - this is where we diverge from traditional
            # rate pacing
            # FIXME: This assumes the item is an item not a sub-list...
            # Added test to ensure that a list does have a subitem - it may
            # not if it's been removed because it has an unsupported MIME type
            # or is unavailable! AJF 17.7.2012

            credit_list = [
                (max(0, self.get_duration_for(
                    self._current_content_items[cds_index][0]
                    if len(self._current_content_items[cds_index]) > 0
                    else None
                )) - buckets[cds_index]) * 1 / ratio_for[cds_index]
                for cds_index in range(0, len(self._current_content_items))
            ]

            log.debug(
                'Diffs: {credit_list}'.format(credit_list=str(credit_list))
            )

            try:
                credit_needed = min(
                    [credit for credit in credit_list if credit > 0]
                )
            except ValueError:
                # Added 0, in case there's no credit needed for any of the
                # buckets, else can get 0 length list

                credit_needed = 0

            log.debug(
                'Content inc needed is {credit_needed}'.format(
                    credit_needed=credit_needed
                )
            )

            buckets = [
                buckets[schedule] + ratio_for[schedule] * credit_needed
                for schedule in range(0, len(self._current_content_items))
            ]
            log.debug(
                'Crediting buckets to {buckets}'.format(buckets=str(buckets))
            )

            # Now choose which item to go with - these should 'round robin',
            # so when an item has been chosen it needs to rotate to the end of
            # the list
            for cds_index in range(0, len(self._current_content_items)):
                # Test first (current head) item from each source

                # if we have no items left in this playlist, e.g. due to errors
                # or lack of renderers, skip it

                if not len(self._current_content_items[cds_index]):
                    continue

                # Get the next content item and its duration (if it has one)

                content_item = self._current_content_items[cds_index][0]

                # Work out how to play this content item
                #print('CONTENT ITEM: '+content_item.get_content_type())
                asset = self.determine_asset(content_item)

                first_item_duration = self.get_duration_for(content_item)

                # If we have enough credit in our bucket for this item
                if (buckets[cds_index] >= first_item_duration):
                    log.debug(
                        'Content from queue {index} for {dur}'.format(
                            index=cds_index, dur=first_item_duration
                        )
                    )

                    # Play the item
                    log.debug(
                        'playing content item {item!s}'.format(
                            item=content_item
                        )
                    )
                    if (
                        content_item.constraints_are_met() and
                        content_item.count_files()
                    ):
                        # sleep counter check if value is greater than 10 sleep
                        # 10s when constraints are not met, reset to 0
                        # otherwise
                        sleep_counter = 0
                        log.debug('content_item.constraints_are_met!')

                        # If MIME type is not okay
                        if asset is None:
                            msg = 'unrecognised content type: {type}'
                            log.warning(msg.format(type=content_item.get_content_type()))
                            msg = ('removing content item {item!s} with '
                                   'unknown mime type, xml is {xml}')

                            # Log and remove this bogus content item
                            log.debug(msg.format(
                                item=content_item, xml=content_item.get_xml()
                            ))

                            self._current_content_items[cds_index].pop(0)
                            continue     # Skip this item, try the next one

                        # Record the item we're trying to play so that we
                        # can know when we need to interrupt it (if it gets
                        # removed).
                        self.now_playing = content_item

                        # Lookup content URI / file path
                        # (do any precaching we can)
                        content_src_uri = self.cache_manager.prefetch_content_item(asset)
                        if content_src_uri is None:
                            # Can't fetch this now, move it to the end and try
                            # the next content item
                            self._current_content_items[
                                cds_index
                            ].append(
                                self._current_content_items[cds_index].pop(0)
                            )
                            continue        # Skip this item, try the next one

                        asset.set_uri(content_src_uri)
                        log.debug('URI is ' + content_src_uri)

                        log.info(
                            "Next item's duration is {duration!r}".format(
                                duration=first_item_duration
                            )
                        )

                        # Start buffering content
                        asset.prepare()

                        # Sleep for the content duration
                        if first_item_duration is not None:
                            # Normal content with a duration
                            now = time.time()
                            end_time = now + first_item_duration

                            # Allow display to stay for 2x duration of content
                            self.display_client.msg_queue.put_nowait(
                                DISPLAY_ON_XML.format(
                                    timestamp=end_time + self.content_duration
                                )
                            )

                            asset.play()
                            
                            while (
                                now < end_time and (
                                    self.ignore_scheduler + SENSOR_LIFETIME
                                ) <= now and
                                not self.scheduler_event_thread.is_set()
                            ):
                                # Sleep for up to 1 sec
                                try:
                                    time.sleep(min(1, end_time - time.time()))
                                except IOError:
                                    pass
                                now = time.time()

                                log.debug(
                                    "Time remaining {}".format(end_time - now)
                                )

                        else:
                            # Stream content (NOT HANDLED ON rpi YET)
                            msg = 'Stream content (no duration) now {now}'
                            log.debug(msg.format(now=time.time()))

                            asset.play()
                            
                            while (
                                (
                                    self.ignore_scheduler + SENSOR_LIFETIME
                                ) <= time.time() and
                                not self.scheduler_event_thread.is_set()
                            ):
                                # Ensure display stays on for 2x duration
                                # of content
                                xml = DISPLAY_ON_XML.format(
                                    timestamp=time.time() + STREAM_ON_LEEWAY
                                )
                                self.display_client.msg_queue.put_nowait(xml)

                                # Sleep 1 sec
                                time.sleep(1)

                        log.debug('Content duration done, now_playing = None')

                        self.now_playing = None

                        # Update playtime counters and buckets for content
                        # descriptor sets

                        if first_item_duration is not None:
                            buckets[cds_index] -= first_item_duration

                        # Terminate old renderers
                        # Should really pass the colour of the next asset
                        asset.stop()

                        if self.scheduler_event_thread.is_set():
                            self.scheduler_event_thread.clear()
                            log.debug('Schedule change preemption')
                            break

                    elif not content_item.constraints_are_met():
                        log.info('Skipping item, constraints not met')
                        # if constraints not met within 10 time, sleep 2
                        # seconds before reevaluating constraints
                        sleep_counter += 1
                        if sleep_counter > 9:
                            time.sleep(TIME_TO_SLEEP)

                    # Move played item back to the end of its playlist
                    self._current_content_items[cds_index].append(
                        self._current_content_items[cds_index].pop(0)
                    )

        # Reset the soft interrupt flag as we're leaving this playback loop now
        self.refresh_schedules_softinterrupt.clear()

    def run(self):
        self.renderers = Renderers()

        while True:
            self.process_subscription()
            time.sleep(1)

    def set_content_duration(self, time_to_show):
        self.content_duration = time_to_show

    def set_cache_path(self, cache_path):
        self.cache_path = cache_path
        self.cache_manager=cache_manager(self.cache_path)

    def update_list(self, etree_new):
        """ A simple comparator based on MD5."""

        # Get the 1st tier content descriptor sets (corresponding to each
        # subscription)
        # FIXME: Still think this is returning a CDS for the root XML
        # twice somehow, then the subscriptions are nested in that
        try:
            subs_parser = XMLSubscriptionParser(etree_new)
        except XMLSubscriptionParserError:
            log.exception('Failed to parse subscription update.')
            return
        root_cds = subs_parser.get_descriptor_set().get_children()
        if not len(root_cds):
            return

        # Parse the XML subscriptions - we should get a list of lists,
        # each list corresponding to a playlist]
        # A higher priority trumps any lower ones, so pull out content
        # of a certain priority
        incoming_content_items = self.parse_content_descriptor_set(
            root_cds, flatten=False
        )

        # Let's compare the current set of items with the previous set
        # we're working on
        # Are there any changes between this and the last one?
        should_interrupt = (
            self._previous_priority_level and
            self._current_priority_level > self._previous_priority_level or
            self.web_requests_updated
        )
        log.debug(
            '# incoming items = {list}, interrupt = {si}'.format(
                list=len(incoming_content_items), si=should_interrupt
            )
        )

        if not should_interrupt:
            # New or expired content items?
            add_list = []
            remove_list = []

            flat_copy_of_incoming_items = list(flatten(incoming_content_items))
            flat_copy_of_current_items = list(
                flatten(self._current_content_items)
            )
            log.debug(
                'incoming items = {list}'.format(
                    list=str([str(item)
                              for item in flat_copy_of_incoming_items])
                )
            )
            log.debug(
                'current items = {list}'.format(
                    list=str([str(item)
                              for item in flat_copy_of_current_items])
                )
            )

            log.debug("About to compare content lists")
            try:
                while True:
                    new_item = flat_copy_of_incoming_items.pop(0)

                    if len([
                        existing
                            for existing in flat_copy_of_current_items
                            if existing == new_item
                    ]) == 0:
                        add_list.append(new_item)
                        log.debug("added item = %s" % str(new_item))
            except IndexError:
                pass

            flat_copy_of_incoming_items = list(flatten(incoming_content_items))
            try:
                while True:
                    existing_item = flat_copy_of_current_items.pop(0)

                    if len([
                        new_item
                            for new_item in flat_copy_of_incoming_items
                            if new_item == existing_item
                    ]) == 0:
                        remove_list.append(existing_item)
                        log.debug("removed item = %s" % str(existing_item))

                        if existing_item == self.now_playing:
                            # Removed currently playing item, make sure it gets
                            # interrupted
                            msg = ('hard interrupt, '
                                   'current playing item removed')
                            log.debug(msg)
                            self.scheduler_event_thread.set()
            except IndexError:
                pass

            # No interesting changes
            log.debug(
                '# add list = {add}, remove list = {remove}'.format(
                    add=len(add_list), remove=len(remove_list)
                )
            )
            if len(add_list) == 0 and len(remove_list) == 0:
                log.debug('Nothing to change, not updating playlists')
                return
        else:
            # Should (hard) interrupt current content that's playing
            log.debug('hard interrupt, stopping current content')
            self.scheduler_event_thread.set()

        self.etree = etree_new

        # Update the list of items
        self._playlist_update_mutex.acquire()
        self._incoming_set_of_items = incoming_content_items[:]
        self._playlist_update_mutex.release()

        # Reorder playlists based on their playback constraints
        self.order_by_constraint(self._incoming_set_of_items)

        # Just gentle interrupt - i.e. reset buckets and lists etc.
        # for the new content but don't interrupt what's playing
        log.debug(
            'soft interrupt, refreshing content, ' +
            'self._incoming_set_of_items = {current}'.format(
                current=repr(self._incoming_set_of_items)
            )
        )
        self.refresh_schedules_softinterrupt.set()

    def set_web_requests(self, web_requests):
        if sorted(self.web_requests) != sorted(web_requests):
            print('web_requests has changed')
            self.web_requests_updated = True
        self.web_requests = web_requests.copy()
        self.renderer_override()



class SchedulerReceiver(ApplicationWithConfig, ZMQRPC):
    """
        Creates a socket to receive content_descriptor set
        from subscription manager
    """
    def __init__(self):
        super().__init__('Scheduler')
        self.web_requests = dict()
        self.zmq_scheduler_term_identifier = "scheduler_term_{id}".format(
            id=id(self)
        )

    def _handle_arguments(self, args):
        """Handle arguments received from the argument parser."""
        super()._handle_arguments(args)

        # duration content to show
        log.debug(
            "_handle_arguments: Config duration {dur}, "
            "default is {def_time}".format(
                dur=int(
                    self.config.get('Scheduling', 'DefaultContentDuration')
                ),
                def_time=DEFAULT_TIME_TO_SHOW)
        )

        self.content_duration = max(
            int(self.config.get('Scheduling', 'DefaultContentDuration')),
            DEFAULT_TIME_TO_SHOW
        )

        # cache path
        self.cache_path = self.config.get(
            'CacheFileStorage', 'CacheLocation'
        )

    def _handle_incoming_zmq(self):
        """Executes in separate thread: _zmq_req_to_scheduler_thread."""
        self.zmq_context_req = zmq.Context()

        # Initialise ZMQ reply socket to subscription manager
        zmq_subsmanager_reply_socket = self.zmq_context_req.socket(zmq.REP)
        zmq_subsmanager_reply_socket.setsockopt(zmq.LINGER,
                                                ZMQ_SOCKET_LINGER_MSEC)
        zmq_subsmanager_reply_socket.bind(ZMQ_SUBSMANAGER_ADDR)

        # Initialise ZMQ reply socket to sensor manager
        zmq_sensormanager_reply_socket = self.zmq_context_req.socket(zmq.REP)
        zmq_sensormanager_reply_socket.setsockopt(zmq.LINGER,
                                                  ZMQ_SOCKET_LINGER_MSEC)
        zmq_sensormanager_reply_socket.bind(ZMQ_SENSORMANAGER_ADDR)

        # Initialise ZMQ reply socket to watch for termination
        zmq_termination_reply_socket = self.zmq_context_req.socket(zmq.REP)
        zmq_termination_reply_socket.bind(
            ZMQ_ADDRESS_INPROC.format(
                identifier=self.zmq_scheduler_term_identifier
            )
        )

        # Initialise ZMQ poller to watch REP sockets
        zmq_poller = zmq.Poller()
        zmq_poller.register(zmq_subsmanager_reply_socket, zmq.POLLIN)
        zmq_poller.register(zmq_sensormanager_reply_socket, zmq.POLLIN)
        zmq_poller.register(zmq_termination_reply_socket, zmq.POLLIN)

        # Provide a method to loop over sockets that have data
        def _loop_over_sockets():
            term = False
            for sock in socks_with_data:
                if sock is zmq_termination_reply_socket:
                    term = True

                # B. FIXME THIS SHOULD USE THE _handle_zmq_msg METHOD
                elif sock is zmq_subsmanager_reply_socket:
                    req_str = sock.recv_unicode()
                    req_elem = ET.XML(req_str)
                    subs_update = req_elem.find('subscription-update')
                    if subs_update is not None:
                        new_content_set = ET.tostring(
                            subs_update
                        )
                    sock.send_unicode(
                        ET.tostring(
                            self._encapsulate_reply(self._generate_pong()),
                            encoding="unicode"
                        )
                    )
                    if subs_update is not None:
                        self.update_scheduler(new_content_set)

                else:
                    msg = sock.recv().decode()
                    reply = self._handle_zmq_msg(msg)
                    if reply is None:
                        log.warning(WARN_NO_REPLY)
                        reply = self._encapsulate_reply(self._generate_error())
                    sock.send(ET.tostring(reply))
            return term

        while True:
            socks_with_data = dict(zmq_poller.poll())
            if socks_with_data:
                term = _loop_over_sockets()
                if term:
                    break

        # Cleanup ZMQ
        zmq_poller.unregister(zmq_subsmanager_reply_socket)
        zmq_poller.unregister(zmq_sensormanager_reply_socket)
        zmq_poller.unregister(zmq_termination_reply_socket)
        zmq_subsmanager_reply_socket.close()
        zmq_sensormanager_reply_socket.close()
        zmq_termination_reply_socket.close()

    def _handle_request_sensor_update(self, msg_root=None, msg_elem=None):
        request_time = time.time()

        # Pull out the server, port, password from the received request
        if None not in (msg_root, msg_elem):
            parser=ContentItem(msg_elem.find('content-item'))
            #don't override renderer until content is ready...
            while(self.scheduler.cache_manager.prefetch_content_item(self.scheduler.determine_asset(parser)) is None):
                time.sleep(2)
            request_time = time.time()
            self.web_requests[parser.get_files()[0]] = (parser,request_time)
        copy=self.web_requests.copy()
        # Remove expired requests
        for key in copy:
            if copy[key][1] + SENSOR_LIFETIME < request_time:
                log.debug(str(key) + ' has expired')
                self.web_requests.pop(key)

        if len(self.web_requests) > 0:
            request_times = [self.web_requests[key][1] for key in self.web_requests]
            self.scheduler.ignore_scheduler = max(request_times)

            # Generate another sensor check to ensure old sensor updates are
            # removed even when new ones aren't coming in - in this case
            # we don't pass in the msg parameters so they default to None.
            t = threading.Timer(1, self._handle_request_sensor_update)
            t.start()

        # Make the set of connection requests available in the other
        # object/thread
        self.scheduler.set_web_requests(self.web_requests)

        return self._encapsulate_reply(self._generate_pong())




    def control_scheduler(self):
        self.scheduler = Scheduler()
        self.scheduler.set_content_duration(self.content_duration)
        self.scheduler.set_cache_path(self.cache_path)
        log.info('Starting content scheduling')
        self.scheduler.start()

    def start(self):
        """The main execution method for this application."""
        self.zmq_scheduler_req_addr = ZMQ_SUBSMANAGER_ADDR

        # Start a new thread to create ZMQ sockets to receive
        # requests from the sensor and subscription managers.
        self._zmq_scheduler_reply_thread = threading.Thread(
            target=self._handle_incoming_zmq
        )
        t_name = 'ZMQ reply socket monitor'
        self._zmq_scheduler_reply_thread.name = t_name
        self._zmq_scheduler_reply_thread.daemon = True
        self._zmq_scheduler_reply_thread.start()
        self.control_scheduler()
        
    def stop(self):
        """Application termination cleanup.

        """
        # Turn off display as we're exiting
        self.scheduler.display_client.send_request(
            DISPLAY_ON_XML.format(timestamp=time.time() - 1)
        )
        self.scheduler.display_client.msg_queue.put_nowait(
            _TERMINATION_MARKER
        )

        # Terminate ZMQ-related threads
        zmq_termination_request_socket = self.zmq_context_req.socket(zmq.REQ)
        zmq_termination_request_socket.setsockopt(
            zmq.LINGER, ZMQ_SOCKET_LINGER_MSEC
        )
        zmq_termination_request_socket.connect(
            ZMQ_ADDRESS_INPROC.format(
                identifier=self.zmq_scheduler_term_identifier
            )
        )
        zmq_termination_request_socket.send_unicode('TERMINATE')
        zmq_termination_request_socket.close()
        self._zmq_scheduler_reply_thread.join()

        super().stop()
        self.zmq_context_req.term()

    def update_scheduler(self, new_content_set):
        log.debug('Update scheduler')
        etree = ET.fromstring(new_content_set)
        self.scheduler.update_list(etree)

if __name__ == "__main__":
    application_loop(SchedulerReceiver)
