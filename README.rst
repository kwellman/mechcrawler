Mechcrawler
~~~~~~~~~~~

Usage
-----

To crawl all the links of a domain::

    from mechcrawler import CrawlBrowser

    br = CrawlBrowser(domain='domain.com')

    br.crawl(start_url='http://domain.com')

    print br.errors()

Thanks to Mechanize, mechcrawler can handle cookies and forms. It may be useful to have some processing before starting a crawl. For example, you can login to a site using the mechanize api, so that the crawl can access pages that require a user to be logged in.

Example::

    br.select_form(name='loginform')
    br['username'] = 'username'
    br['password'] = 'password'
    br.submit()

Requirements
------------

Mechanize::
    
   easy_install mechanize

