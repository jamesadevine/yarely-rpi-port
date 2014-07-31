import zmq


content_xml = \
"""
<subscription-update uri="foo">
<content-set name="Legacy e-Campus Display: ecampus-50" type="inline">
  <auth handler="none"/>
  <feedback/>
  <constraints>
    <scheduling-constraints>
      <time>
        <between start="08:30:00" end="18:00:00"/>
      </time>
      <day-of-week>
        <between start="monday" end="sunday"/>
      </day-of-week>
    </scheduling-constraints>
  </constraints>
<content-set name="Press Office - press office news" type="inline">
<auth handler="none"/>
<feedback/>
<constraints>
<scheduling-constraints>
<playback order="random" avoid-context-switch="false"/>
<day-of-week><between start="monday" end="sunday"/></day-of-week>
</scheduling-constraints>
</constraints>

<content-item content-type="image/jpeg; charset=binary">
<requires-file>
<hashes>
<hash type="md5">8839c989f71404c12651882f37d2b1bb</hash>
<hash type="sha1">b42f0d8bd689e9f30472e32fd54fbee5ce59f278</hash>
</hashes><sources>
<uri>http://e-content.lancs.ac.uk/1.jpg</uri>
</sources></requires-file></content-item>

<content-item content-type="image/jpeg; charset=binary"><requires-file>
<hashes><hash type="md5">1793d88ca04afe78079bb78a159947e6</hash>
<hash type="sha1">ae33e952d1befceb9638c064e05b5052129fd8e1</hash>
</hashes>
<sources><uri>http://e-content.lancs.ac.uk/2.jpg</uri>
</sources>
</requires-file>
</content-item><content-item content-type="image/jpeg; charset=binary">
<requires-file><hashes>
<hash type="md5">5cfe67c015144d17a87f153ae78aa46b</hash>
<hash type="sha1">1e8ea596c4b6cc47ab5d48bfbf0a65db6c2814ba</hash></hashes>
<sources>
<uri>http://e-content.lancs.ac.uk/3.jpg</uri>
</sources>
</requires-file>
</content-item>
</content-set>
</content-set>
</subscription-update>
"""

content_xml1 = \
"""
<subscription-update uri="foo">
<content-set name="Legacy e-Campus Display: ecampus-50" type="inline">
  <auth handler="none"/>
  <feedback/>
  <constraints>
    <scheduling-constraints>
      <time>
        <between start="08:30:00" end="14:00:00"/>
      </time>
      <day-of-week>
        <between start="monday" end="sunday"/>
      </day-of-week>
    </scheduling-constraints>
  </constraints>
<content-set name="Press Office - press office news" type="inline">
<auth handler="none"/>
<feedback/>
<constraints>
<scheduling-constraints>
<playback order="random" avoid-context-switch="false"/>
<day-of-week><between start="monday" end="sunday"/></day-of-week>
</scheduling-constraints>
</constraints>
<content-item content-type="image/jpeg; charset=binary">
<requires-file>
<hashes>
<hash type="md5">8839c989f71404c12651882f37d2b1bb</hash>
<hash type="sha1">b42f0d8bd689e9f30472e32fd54fbee5ce59f278</hash>
</hashes><sources>
<uri>http://e-content.lancs.ac.uk/1.jpg</uri>
</sources></requires-file>
</content-item><content-item content-type="image/jpeg; charset=binary">
<requires-file>
<hashes><hash type="md5">1793d88ca04afe78079bb78a159947e6</hash>
<hash type="sha1">ae33e952d1befceb9638c064e05b5052129fd8e1</hash>
</hashes>
<sources><uri>http://e-content.lancs.ac.uk/2.jpg</uri>
</sources>
</requires-file>
</content-item><content-item content-type="image/jpeg; charset=binary">
<requires-file><hashes>
<hash type="md5">4cfe67c015144d17a87f153ae78aa46b</hash>
<hash type="sha1">1e8ea596c4b6cc47ab5d48bfbf0a65db6c2814ba</hash></hashes>
<sources>
<uri>http://e-content.lancs.ac.uk/4.jpg</uri>
</sources>
</requires-file>
</content-item>
</content-set>
</content-set>
</subscription-update>
"""

context = zmq.Context()
socket = context.socket(zmq.PUSH)
socket.connect("tcp://127.0.0.1:5000")

# print the message size in bytes
#print(len(content_xml1))
socket.setsockopt(zmq.HWM, 8)
socket.send_unicode(content_xml1)
