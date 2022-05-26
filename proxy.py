import http.server
import re
from os.path import exists
import mimetypes
from cgi import parse_header
from sys import getsizeof
from http.server import ThreadingHTTPServer
import httplib2
import lxml.html

#httplib2.debuglevel = 0
PORT = 8000
ADDRESS = "https://news.ycombinator.com/"


class Proxy(http.server.SimpleHTTPRequestHandler):
    _h = httplib2.Http('.cache')

    def do_GET(self):
        if self.path.endswith("gif") or self.path.endswith("ico"):
            imgname = self.path[1:]
            if not exists(imgname):
                self.save_remote_image(imgname)
            self.send_response(200)
            self.get_local_image(imgname)
            return
        url = ADDRESS + self.path[1:]
        response, content = self.make_request(url)
        types, _ = parse_header(response["content-type"])
        if "html" in types.split("/"):
            doc = lxml.html.fromstring(content.decode())
            doc = self.modify_html(lxml.html.fromstring(content.decode()))
            content = lxml.html.tostring(doc) # bytes btw KEKW
        self.apply_headers(response, length=getsizeof(content))
        self.wfile.write(content)

    def apply_headers(self, headers, end_header=True, length=None):
        for key in headers:
            if key.lower() == "transfer-encoding":
                continue
            if key.lower() == "content-length":
                self.send_header("content-length", str(length - 33))
                continue
            self.send_header(key.lower(), headers[key])
        if end_header:
            self.end_headers()

    def make_request(self, url):
        response, content = self._h.request(url)
        self.send_response(response.status)
        return response, content

    def log_into_file(self, entity, mode="w", name="log"):
        with open(name + ".text", mode) as file:
            if mode == "w":
                entity = str(entity)
            file.write(entity)
            file.close()

    def log_headers(self, headers):
        i=1
        for header in headers:
            with open("header{}.text".format(str(i)), "w") as file:
                for key in header:
                    file.write(str(key) + ": " + header[key])
                    file.write("\n")

    def save_remote_image(self, imgname):
        response, remote_file = self.make_request(ADDRESS + imgname)
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

    def modify_html(self, tree):
        for node in tree.xpath("//*[normalize-space(string-length(text())) >= 6]"):
            if node.text:
                node.text = re.sub(r"((?<!\S)|^|[\"\'\)\]\}])(\b\w{6}\b)($|\S(?!\S)|\s|[\"\'\)\]\}])", r"\g<1>\g<2>™\g<3>", node.text)
                if node.text.find("came") != -1:
                    for child in list(node):
                        if child.tail and len(child.tail) >= 6:
                            child.tail = re.sub(r"((?<!\S)|^|[\"\'\)\]\}])(\b\w{6}\b)($|\S(?!\S)|\s|[\"\'\)\]\}])", r"\g<1>\g<2>™\g<3>", child.tail)

        for node in tree.xpath("//a[contains(@href,'https://news.ycombinator.com')]"):
            node.set("href", "")
        return tree


httpd = ThreadingHTTPServer(('', PORT), Proxy)
print("Now serving at " + str(PORT))
httpd.serve_forever()
