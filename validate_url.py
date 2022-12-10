'''make a  function that takes a url and returns a url containing http and wwww if missing'''

def validate_url(url):
    if url == None:
        return None
    elif 'http' in url:
        return url
    elif 'www' in url:
        return 'http://' + url
    else:
        return 'http://www.' + url