from yarely.frontend.core.scheduler.schedule import ScheduleFactory
content_xml = \
"""<content-collection name="e-Campus Team - e-Campus Sticky" type="inline">
  <auth handler="none"/>
  <feedback/>
  <constraints>
    <scheduling-constraints>
      <playback order="random" avoid-context-switch="false"/>
      <time>
        <not-before>00:30:00</not-before>
        <not-after>23:55:00</not-after>
        <play-on>weekdays</play-on>
      </time>
    </scheduling-constraints>
  </constraints>
  <content-item content-type="image/png; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">a</hash>
        <hash type="sha1">ccce1d4566906e820f7ec6ceea9824a2677fffe0</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/logo1.png</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/png; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">b</hash>
        <hash type="sha1">ccce1d4566906e820f7ec6ceea9824a2677fffe0</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/logo2.png</uri>
      </sources>
    </requires-file>
  </content-item>
<content-item content-type="image/png; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">c</hash>
        <hash type="sha1">ccce1d4566906e820f7ec6ceea9824a2677fffe0</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/logo3.png</uri>
      </sources>
    </requires-file>
    <constraints>
            <scheduling-constraints>
               <playback order="random" avoid-context-switch="false"/>
               <time>
                    <not-before>00:30:00</not-before>
                    <not-after>22:55:00</not-after>
                    <play-on>weekdays</play-on>
              </time>
           </scheduling-constraints>
    </constraints>
  </content-item>
</content-collection>
"""

content_xml1 = \
"""<content-collection name="e-Campus Team - e-Campus Sticky" type="inline">
  <auth handler="none"/>
  <feedback/>
  <constraints>
    <scheduling-constraints>
      <playback order="random" avoid-context-switch="false"/>
      <time>
        <not-before>00:30:00</not-before>
        <not-after>23:55:00</not-after>
        <play-on>weekdays</play-on>
      </time>
    </scheduling-constraints>
  </constraints>
  <content-item content-type="image/png; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">a</hash>
        <hash type="sha1">ccce1d4566906e820f7ec6ceea9824a2677fffe0</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/logo1.png</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/png; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">b</hash>
        <hash type="sha1">ccce1d4566906e820f7ec6ceea9824a2677fffe0</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/logo2.png</uri>
      </sources>
    </requires-file>
  </content-item>
<content-item content-type="image/png; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">d</hash>
        <hash type="sha1">ccce1d4566906e820f7ec6ceea9824a2677fffe0</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/logo4.png</uri>
      </sources>
    </requires-file>
    <constraints>
            <scheduling-constraints>
               <playback order="random" avoid-context-switch="false"/>
               <time>
                    <not-before>00:30:00</not-before>
                    <not-after>22:55:00</not-after>
                    <play-on>weekdays</play-on>
              </time>
           </scheduling-constraints>
    </constraints>
  </content-item>
</content-collection>
"""

if __name__ == '__main__':
    schedule_task = ScheduleFactory()
    schedule_task.start()
