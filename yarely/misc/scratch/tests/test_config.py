from yarely.frontend.core.config import YarelyConfig
conf = YarelyConfig('/Users/sarah/Documents/yarely/\
frontend/core/config/samples/yarely.cfg')
try:
    colour = conf.getcolour('Facade', 'BackgroundColour')
except:
    print('Failed to get colour, trying tuple...')
    try:
        colour = conf.gettuple('Facade', 'BackgroundColour')
    except:
        print('ERROR - Failed to get tuple!!')
print(repr(colour))
print(conf.getfloat('Facade', 'ImageScale', raw=True))
print(conf.getint('CacheConfig', 'MaxCacheSize'))
