from html.parser import HTMLParser
from urllib import parse


class LinkFinder(HTMLParser):
    def __init__(self, base_url, page_url):
        HTMLParser.__init__(self)
        self.base_url = base_url
        self.page_url = page_url
        self.links = set()

    def error(self, message):
        pass

    # THIS GETS THE STARTING TAG AND IS CALLED AT EVERY STARTING TAG
    
    def handle_starttag(self, tag, attrs):
        for (attribute, value) in attrs:
            if attribute == 'href':
                url = parse.urljoin(self.base_url, value)
                self.links.add(url)

    def page_links(self):
        return self.links

