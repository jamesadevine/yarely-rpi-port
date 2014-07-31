from yarely.frontend.core.content.caching.cache_handler_http import HandleHTTP

#url = "http://www.lyre-of-ur.com/images/NewLyre/Lyre_10Mb.jpg"
url = "http://www.comp.lancs.ac.uk/~surajbal/images/2.JPG"

# Simple check if functions of class handle_http working
if __name__ == "__main__":
    handler = HandleHTTP()
    print(handler.fetch_http(url))
