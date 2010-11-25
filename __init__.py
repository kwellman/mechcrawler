import mechanize
from test import TestBrowser, URLError, HTTPError, TransferError, BrowserError, CheckError, TransferError
from crawl import CrawlBrowser, CrawlError

def set_default_timeout(timeout=30):
	# provide a timeout in seconds for requests (mechanize default is none)
	mechanize._sockettimeout._GLOBAL_DEFAULT_TIMEOUT = timeout

set_default_timeout()
