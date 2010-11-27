import re
from collections import deque
import mechanize
from test import TestBrowser

class CrawlError(Exception): pass

class CrawlBrowser(TestBrowser):
    """Add crawling capabilities to mechanize's Browser. Useful for testing
    all the links of a site.
    """
    def __init__(self):#, includes=[], excludes=[]):
        self.cached_responses = {}
        self.todo_links = deque()
        #self.includes = [re.compile(include) for include in includes]
        #self.excludes = [re.compile(exclude) for exclude in excludes]
        self.crawl_errors = []

        super(CrawlBrowser, self).__init__(self)

    def links(self, **kwds):
        """Add source attribute to link objects to keep track of the link
        origin.
        """
        links = list(super(CrawlBrowser, self).links(self, **kwds))

        for link in links:
            link.source = self.geturl()

        return links

    def filter_url(self, url):
        """Check if url meets user specified criteria for inclusion or exclusion
        in the crawl.
        """
        for exclude in self.excludes:
            if exclude.match(url):
                return False

        for include in self.includes:
            if include.match(url):
                return True

        if self.includes:
            return False
    
        return True

    def handle_url(self, url):
        """
        """
        url = url.split('#')[0]

        if url in self.cached_responses:
            return self.cached_responses[url]

        if not self.filter_url(url):
            return

        print 'fetching: %s' % url

        try:
            self.open(url)
        except Exception, e:
            result = e
        else:
            result = None

        # in case of a redirect to an already visited page
        if self.geturl() in self.cached_responses:
            self.cached_responses[url] = result
            return result

        self.cached_responses[url] = result
        self.cached_responses[self.geturl()] = result

        if result:
            # an error has occured
            return result

        # TODO: only add links if url in domain (use urlparse for this)
        pass

        self.todo_links.extend(self.links())

    def report_error(self, link, result):
        print
        print 'URL\t\t%s' % link.url
        print 'Parent URL\t%s' % link.source
        print 'Result\t\t%s' % result

        self.crawl_errors.append((link.source, link, result))

    def crawl(self, start_url=None, includes=[], excludes=[], domain=None, max_links=300):
        # TODO: add domain filter for link crawling 
        pass

        self.includes = [re.compile(include) for include in includes]
        self.excludes = [re.compile(exclude) for exclude in excludes]

        if not start_url:
            start_url = self.geturl()

        self.todo_links.append(mechanize.Link(start_url, '', None, '', {}))

        while self.todo_links:
            link = self.todo_links.popleft()
            result = self.handle_url(link.absolute_url)

            if isinstance(result, Exception):
                self.report_error(link, result)

            if len(self.cached_responses) > max_links:
                raise CrawlError('max link count (%s) exceeded' % max_links)

