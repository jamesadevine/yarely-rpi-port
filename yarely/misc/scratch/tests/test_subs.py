from yarely.frontend.core.subscriptions.subscription_manager import SubscriptionManager
s = SubscriptionManager()


from yarely.frontend.core.subscriptions.subscription_parser import XMLSubscriptionParser
xml1 = '''<?xml version="1.0"?>
<content-set name="Legacy e-Campus Display: ecampus-50" type="inline">
  <auth handler="none"/>
  <feedback/>
  <constraints>
    <scheduling-constraints>
      <time>
        <not-before>08:30:00</not-before>
        <not-after>18:00:00</not-after>
        <play-on>daily</play-on>
      </time>
    </scheduling-constraints>
  </constraints>
  <content-set name="ecampus-50: e-Campus Team - e-Campus Sticky" type="remote">
    <requires-file>
      <sources>
        <http-source uri="http://e-content.lancs.ac.uk/yarely/per_channel.php?channel_id=66" refresh="1 hour"/>
      </sources>
    </requires-file> 
 </content-set>
  <content-set name="ecampus-50: Press Office - press office news" type="remote">
    <requires-file>
      <sources>
        <http-source uri="http://e-content.lancs.ac.uk/yarely/per_channel.php?channel_id=124" refresh="1 hour"/>
      </sources>
    </requires-file> 
  </content-set>
</content-set>'''
xml2 = '''<?xml version="1.0"?>
<content-set name="Press Office - press office news" type="inline">
  <auth handler="none"/>
  <feedback/>
  <constraints>
    <scheduling-constraints>
      <playback order="random" avoid-context-switch="false"/>
      <time>
        <play-on>daily</play-on>
      </time>
    </scheduling-constraints>
  </constraints>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">4e39c989f71404c12651882f37d2b1bb</hash>
        <hash type="sha1">b42f0d8bd689e9f30472e32fd54fbee5ce59f278</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Briefings%20Poster%202011%2020x14.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">1793d88ca04afe78079bb78a159947e6</hash>
        <hash type="sha1">ae33e952d1befceb9638c064e05b5052129fd8e1</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Enforcement-alone-wont-solve-underage-drinking-problem.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">5cfe67c015144d17a87f153ae78aa46b</hash>
        <hash type="sha1">1e8ea596c4b6cc47ab5d48bfbf0a65db6c2814ba</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/English%20student%20wins%20short%20story%20competition.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">53d45edf30a245b872610e42ea39b69e</hash>
        <hash type="sha1">658e30068f9302e6426159b3ca04f74909e80173</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Esmee-Fairbairn-Lecture.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">8bbcf4c151dca5972784ddafe03dde62</hash>
        <hash type="sha1">752a20d1444140ff22f654685fc008f6b83433fe</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/GDUF.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">2a7ea0374a6cb07ad2b9768bbc9d8948</hash>
        <hash type="sha1">c606fea56a8bfc79cc55ce0cab9507acd7ab0d16</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Green%20Gown.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">a1e1105ddafda002fa7ab2ee05d9e6b3</hash>
        <hash type="sha1">f5273c37468bc673779ab4a8f449456546a33d39</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Ian%20Hartley%202.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">7cccbaff4b7dd2deb24f6184a40a7652</hash>
        <hash type="sha1">0b143901f0c0b418dde626346196eab00029b92f</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Marion%20McClintock.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">a4d64b66fd3981d00d33a9a7f58dd8d6</hash>
        <hash type="sha1">60c005c557960a9d8b5acad4264652262429117d</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Question%20time.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">1dd95deaadb756d7fc4198b7f98eeb94</hash>
        <hash type="sha1">523e99f3e9c496fa904b125d54994885ff243f38</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Rich%20underground%20life%20discovered%20at%20the%20poles.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">3f2c5044a9d743a8c08457ca3af5055b</hash>
        <hash type="sha1">0d7c8ca7cd618f34d92abdb640c4efb8f9a52d2d</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/Students%20gain%20insight%20into%20City%20careers.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">36ec1229967c24461c4ebd66fd139d8d</hash>
        <hash type="sha1">804a0c8cef27839856838dc63857b6d148c73e02</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/University%20expertise%20helps%20technology%20firm.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">4dd56adb12fc9020c85673505169f17f</hash>
        <hash type="sha1">3fffef72e680ad39efd3b557349e20098bb12d88</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/bubble.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
  <content-item content-type="image/jpeg; charset=binary">
    <requires-file>
      <hashes>
        <hash type="md5">14d8f4eb9480356d12fbd5d6b9cc3339</hash>
        <hash type="sha1">1a149c9e4413d590ca09a759f1e219f006e49fc4</hash>
      </hashes>
      <sources>
        <uri>http://e-content.lancs.ac.uk/ChannelContent/PressOffice/press_office_news/donation%20for%20bipolar%20research.jpg</uri>
      </sources>
    </requires-file>
  </content-item>
</content-set>'''
#p1 = XMLSubscriptionParser(xml1)
p2 = XMLSubscriptionParser(xml2)
