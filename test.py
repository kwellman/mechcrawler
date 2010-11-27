import re, random, time, urllib2, httplib
from fnmatch import fnmatch
import mechanize

# TODO: add cookie methods: set_cookie, set_cookiejar, get_cookie, get_cookiejar

# set up aliases for exceptions
URLError = urllib2.URLError
HTTPError = mechanize.HTTPError
TransferError = httplib.HTTPException

class BrowserError(Exception): pass
class CheckError(Exception): pass
class RegexError(CheckError): pass

USERAGENTS = (
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6',
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.0.6) Gecko/2009011912 Firefox/3.0.6',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6 (.NET CLR 3.5.30729)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.10 (intrepid) Firefox/3.0.6',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6',
    'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.6) Gecko/2009011913 Firefox/3.0.6 (.NET CLR 3.5.30729)',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/1.0.154.48 Safari/525.19',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648)',
    'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.0.6) Gecko/2009020911 Ubuntu/8.10 (intrepid) Firefox/3.0.6',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.5) Gecko/2008121621 Ubuntu/8.04 (hardy) Firefox/3.0.5',
    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-us) AppleWebKit/525.27.1 (KHTML, like Gecko) Version/3.2.1 Safari/525.27.1',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)',
    'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1)'
)

class TestBrowser(mechanize.Browser):
    """Subclass of mechanize's Browser with added methods useful for testing.
    """
    def __init__(self, *args, **kwargs):
        super(TestBrowser, self).__init__(self, *args, **kwargs)

        self.set_useragent(pattern='firefox')

        extra_headers = [
            ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            ('Accept-Language', 'en-us,en;q=0.5'),
            #('Accept-Encoding', 'gzip,deflate'),
            ('Accept-Charset', 'ISO-8859-1,utf-8;q=0.7,*;q=0.7'),
            ('Keep-Alive', '115'),
            ('Connection', 'keep-alive'),
            ('Cache-Control', 'max-age=0')]
        self.append_headers(extra_headers)

        # Print HTTP headers.
        #self.set_debug_http(True)

        # do handle HTTP-EQUIV properly.
        #self.set_handle_equiv(True)

        # don't handle robots.txt
        self.set_handle_robots(False)

    def set_useragent(self, useragent=None, pattern='', randomize=False):
        """Sets the user-agent http header. Can specify exact header value by
        passing useragent argument, or glob pattern to select from USERAGENTS
        presets.
        """
        self.remove_headers(keys=['User-Agent'])

        if useragent:
            self.append_headers([('User-Agent', useragent)])
            return

        if randomize:
            useragents = list(USERAGENTS)
            random.shuffle(useragents)
        else:
            useragents = USERAGENTS

        # matching is case insensitive and can be anywhere in string
        pattern = '*' + pattern.lower() + '*'

        for useragent in useragents:
            if fnmatch(useragent.lower(), pattern):
                self.append_headers([('User-Agent', useragent)])
                return
        else:
            raise BrowserError('no user agent matching "%s"' % pattern)

    def remove_headers(self, headers=[], keys=[]):
        assert isinstance(headers, (list, tuple)), 'headers argument must be list or tuple'
        headers = list(headers)

        for key in keys:
            for header in self.addheaders:
                if header[0].lower() == key.lower():
                    headers.append(header)

        for header in headers:
            try:
                self.addheaders.remove(header)
            except ValueError:
                pass

    def append_headers(self, headers):
        self.addheaders.extend(headers)

    def set_headers(self, headers):
        self.addheaders = headers

    def select_form(self, name=None, predicate=None, nr=None, id=None, action=None, method=None):
        """Allow selection based on "action" and/or "method" attributes.
        """
        try:
            return super(TestBrowser, self).select_form(self, name=name, predicate=predicate, nr=nr)
        except (ValueError, mechanize.FormNotFoundError), e:
            for form in self.forms():
                if id and not form.attrs.get('id') == id:
                    continue
                if action and not form.attrs.get('action') == action:
                    continue
                if method and not form.attrs.get('method') == method:
                    continue
                if name and not form.attrs.get('name') == name:
                    continue
                self.form = form
                break
            else:
                kwargs = zip(['name', 'predicate', 'nr', 'id', 'action', 'method'], [name, predicate, nr, id, action, method])
                description = ["%s '%s'" % (key, value) for key, value in kwargs if value]
                if not description:
                    raise ValueError('at least one argument must be supplied to specify form')
                description = ', '.join(description)
                raise mechanize.FormNotFoundError('no form matching '+description)

    def wait(self, min=1, max=5):
        """Mimic user behavior by pausing for random interval.
        """
        time.sleep(random.uniform(min, max))

    def check_title(self, regex=None, match=None, html=None):
        title = self.get_title(html)

        if title is None:
            raise CheckError('no title found')

        if not match is None and not title == match:
            raise CheckError('expected "%s" got "%s"' % (match, title))
        
        if not regex is None:
            self.re_search(regex, string=title)

    def check_html(self, regex=None, token=None, html=None):
        if html is None:
            html = self.response().get_data()

        if not token is None and not token in html:
            raise CheckError('did not find token "%s"' % token)

        if not regex is None:
            self.re_search(regex, string=html)

    def check_url(self, regex=None, match=None, url=None):
        if url is None:
            url = self.get_url()

        if not match is None and not url == match:
            raise CheckError('expected "%s" got "%s"' % (match, url))

        if not regex is None:
            self.re_search(regex, string=url)

    def check(self, url=None, url_regex=None, token=None, html_regex=None, title=None, title_regex=None):

        errors = []
        html = self.response().get_data()

        try:
            self.check_title(match=title, regex=title_regex, html=html)
        except CheckError, e:
            errors.append('title fail: ' + str(e))

        try:
            self.check_html(token=token, regex=html_regex, html=html)
        except CheckError, e:
            errors.append('html fail: ' + str(e))

        try:
            self.check_url(match=url, regex=url_regex)
        except CheckError, e:
            errors.append('url fail: ' + str(e))

        if errors:
            raise CheckError('\n'.join(errors))
    
    def get_title(self, html=None):
        if html is None:
            html = self.response().get_data()
    
        match = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1)
            
    def re_search(self, pattern, *groups, **kwargs):
        """Regex search in html of response or value of 'string'
        argument. Accepts 'string' and 'flags' in kwargs.
        """
        if not 'string' in kwargs:
            kwargs['string'] = self.response().get_data()

        if hasattr(pattern, 'search'):
            match = pattern.search(**kwargs)
        else:
            match = re.search(pattern, **kwargs)

        try:
            return match.group(*groups)
        except AttributeError, e:
            raise RegexError('regex not found "%s"' % pattern)
        except IndexError, e:
            raise RegexError('groups %s not found in regex "%s"' % (groups, pattern))

    def re_search_url(self, pattern, *groups, **kwargs):
        kwargs['string'] = self.response().geturl()
        return self.re_search(pattern, *groups, **kwargs)

    def print_request(self):
        print self.request.header_items()
        print self.request.get_data()
