""" JMX Connections. 

    @author: jhe
"""
import json
import urllib2

from jmx4py.util import network


class JmxConnection(object):
    """ JMX Proxy Connection base class.
    """

    # Registry of URL schemes for different connection types
    registry = {}


    @classmethod
    def register(cls, url_scheme, factory):
        """ Register a connection factory for the given URL scheme.
        """
        cls.registry[url_scheme.lower()] = factory


    @classmethod
    def from_url(cls, url):
        """ Create a connection from the given URL using the scheme registry.
        """
        try:
            # Support the common socket pair for HTTP connections to the default context
            host, port = url
            
            try:
                port = int(port)
            except (TypeError, ValueError), exc:
                raise urllib2.URLError("Bad port in (host, port) pair %r (%s)" % (url, exc)) 
            
            return JmxHttpConnection("http://%s:%d/jolokia/" % (host, port)) 
        except (TypeError, ValueError): 
            url_scheme = url.split(':', 1)[0].lower()
            if url_scheme not in cls.registry:
                raise urllib2.URLError("Unsupported URl scheme '%s' in '%s'" % (url_scheme, url)) 
                
            return cls.registry[url_scheme](url)


    def __init__(self, url):
        """ Create a proxy connection.
        """
        self.url = url


    def open(self):
        """ Open the connection.
        """
        raise NotImplementedError()


    def close(self):
        """ Close the connection and release associated resources.
        """
        raise NotImplementedError()


    def send(self, data):
        """ Perform a single request and return the deserialized response.
        """ 
        raise NotImplementedError()


class JmxHttpConnection(JmxConnection):
    """ JMX Proxy Connection via HTTP.
    """

    def __init__(self, url):
        """ Create a proxy connection.
        """
        super(JmxHttpConnection, self).__init__(url)
        self.url = self.url.rstrip('/') + '/'
        self._open = False


    def open(self):
        """ Open the connection.
        """
        # Currently, we have no connection pooling, so this is basically a NOP
        self._open = True
        return self


    def close(self):
        """ Close the connection and release associated resources.
        """
        self._open = False


    def send(self, data):
        """ Perform a single request and return the deserialized response.
        """ 
        headers = {
            "User-Agent": "jmx4py 0.1", # TODO: add automatic version detection
        }
        req_body = json.dumps(data) # TODO: using data automatically select POST as method 
        req = urllib2.Request(self.url, data=req_body, headers=headers, unverifiable=True)  

        handle = network.urlopen(req) # TODO: , username, password)
        try:
# TODO: wire debugging
#            if debug:
#                log.trace("Reponse headers for %r:\n    %s" % (
#                    url, "\n    ".join(i.strip() for i in handle.info().headers)
#                ))
            result = json.loads(handle.read())
            return result
        finally:
            handle.close()        
