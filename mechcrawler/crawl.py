import re, time
from collections import deque
from urlparse import urlparse
import mechanize
from test import TestBrowser

class CrawlError(Exception): pass

class CrawlBrowser(TestBrowser):
    """Add crawling capabilities to mechanize's Browser. Useful for testing
    all the links of a site.
    """
    def __init__(self, domain=None, includes=[], excludes=[], pause=None, max_links=300):
        if not domain is None:
            d = urlparse(domain)
            if d.netloc:
                self.domain = d.netloc
            else:
                self.domain = d.path.strip('/')
        else:
            self.domain = domain

        self.includes = [re.compile(include) for include in includes]
        self.excludes = [re.compile(exclude) for exclude in excludes]
        self.pause = pause
        self.max_links = max_links

        self.reset()

        TestBrowser.__init__(self)

    def reset(self):
        self.cached_responses = {}
        self.todo_links = deque()
        self.crawl_errors = []
        
    def links(self, **kwds):
        """Add source attribute to link objects to keep track of the link
        origin.
        """
        links = list(TestBrowser.links(self, **kwds))

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

    def handle_url(self, url, delay=None):
        """Visit the url or return cached response if visited previously.
        """
        url = url.split('#')[0]

        if url in self.cached_responses:
            return self.cached_responses[url]

        if not self.filter_url(url):
            return

        print 'fetching: %s' % url

        if not delay is None:
            time.sleep(delay)

        try:
            self.open(url)
        except (KeyboardInterrupt, SystemExit):
            raise
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

        #  only add links if url in domain
        if self.domain is None or urlparse(self.geturl()).netloc == self.domain:
            self.todo_links.extend(self.links())

    def report_error(self, link, result):
        print
        print 'URL\t\t%s' % link.url
        print 'Parent URL\t%s' % link.source
        print 'Result\t\t%s' % result

        self.crawl_errors.append((link.source, link, result))

    def errors(self):
        return self.crawl_errors

    def crawl(self, start_url=None):
        if not start_url:
            if self.domain:
                start_url = 'http://%s' % self.domain
            else:
                start_url = self.geturl()

        self.todo_links.append(mechanize.Link(start_url, '', None, '', {}))

        while self.todo_links:
            link = self.todo_links.popleft()
            result = self.handle_url(link.absolute_url, delay=self.pause)

            if isinstance(result, Exception):
                self.report_error(link, result)

            if len(self.cached_responses) > self.max_links:
                raise CrawlError('max link count (%s) exceeded' % self.max_links)

