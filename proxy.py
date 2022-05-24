import socketserver
import http.server
import re
from os.path import exists
import mimetypes
import httplib2
import lxml.html


#httplib2.debuglevel = 0
h = httplib2.Http('.cache')
PORT = 8232
ADDRESS = "https://news.ycombinator.com/"


class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        if self.path.endswith("gif") or self.path.endswith("ico"):
            imgname = self.path[1:]
            if not exists(imgname):
                self.save_remote_image(imgname)
            self.get_local_image(imgname)
            return
        url = ADDRESS + self.path[1:]
        response, content = h.request(url)
        self.apply_headers(response)
        doc = lxml.html.fromstring(content.decode(errors="replace"))
        doc = self.modify_html(doc)
        self.wfile.write(lxml.html.tostring(doc))
    
    def save_remote_image(self, imgname):
        response, remote_file = h.request(ADDRESS + imgname)
        for i in ["last-modified", "cache-control", "etag", "expires", "accept-ranges", "status"]:
            if i in response:
                self.send_header(i, response[i])
        #self.apply_headers(response)
        with open(imgname, 'wb') as local_file:
            local_file.write(remote_file)

    def get_local_image(self, imgname):
        with open(imgname, 'rb') as local_file:
            imgfile = local_file.read()
            mimetype = mimetypes.MimeTypes().guess_type(imgname)[0]
            self.send_header("Content-type", mimetype)
            self.end_headers()
            self.wfile.write(imgfile)

    def apply_headers(self, headers):
        for key in headers:
            self.send_header(key.lower(), headers[key])
        self.end_headers()

    def modify_html(self, tree):
        for node in tree.xpath("//*[normalize-space(string-length(text())) >= 6]"):
            if node.text:
                node.text = re.sub(r"((?<!\S)(\b\w{6}\b)((?!\S)))", r"\g<1>™", node.text)
        for node in tree.xpath("//a[contains(@href,'https://news.ycombinator.com')]"):
            node.set("href", "")
        return tree



httpd = socketserver.ForkingTCPServer(('', PORT), Proxy)
print("Now serving at " + str(PORT))
httpd.serve_forever()

