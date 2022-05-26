from ctypes import sizeof
import socketserver
import http.server
import re
from os.path import exists
import mimetypes
import httplib2
import lxml.html
import requests
from sys import getsizeof
from http import HTTPStatus


#httplib2.debuglevel = 0
h = httplib2.Http('.cache')
PORT = 8000
ADDRESS = "https://news.ycombinator.com/"


class Proxy(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        if self.path.endswith("gif") or self.path.endswith("ico"):
            imgname = self.path[1:]
            if not exists(imgname):
                self.save_remote_image(imgname)
            self.get_local_image(imgname)
            return
        #self.log_headers()

        url = ADDRESS + self.path[1:]
        response, content = h.request(url)
        # new_request = requests.get(url, headers = self.trim_header(self.headers))
        # self.apply_headers(new_request.headers, False)
        # #self.log_headers([new_request.headers, new_request.request.headers])
        # with open("header1.text", "w") as f:
        #     for key in new_request.headers:
        #         f.write(str(key) + ": " + new_request.headers[key])
        #         f.write("\n")
        # with open("header2.text", "w") as f:
        #     for key in new_request.request.headers:
        #         f.write(str(key) + ": " + new_request.request.headers[key])
        #         f.write("\n")
        # self.wfile.write(new_request.content)
        # return
        # self.log_headers(response)
        
        body = content.decode()
        doc = lxml.html.fromstring(body) # bytes btw KEKW
        doc = self.modify_html(doc)
        # result = lxml.html.tostring(doc, encoding="unicode") # this is actually bytes
        result = lxml.html.tostring(doc)
        print((str(type(result))).capitalize())
        print((str(type(result))).capitalize())
        print((str(type(result))).capitalize())
        self.log_into_file(result, "w")
        # with open("page.html", "wb") as f:
        #     f.write(result)
        # print(body == result)
        self.log_into_file(body, name="body")
        self.log_into_file(content, name="content")
        self.log_into_file(result, name="result")
        self.log_headers([response])

        x = self.wfile
        self.wfile.flush()
        print(x == self.wfile)
        self.log_into_file(response, name="response1")
        self.apply_headers(response)
        self.log_into_file(response, name="response2")
       # print(content == bytes(result, 'utf-8'))
        self.log_into_file(self.headers, name="/Users/Svetlana/Desktop/VSCode/headers5")
        # print(self.wfile.readable())
        # self.log_into_file(self.wfile.read(), name="wfile_original", mode="wb")
        # logging.basicConfig(filename='loglog.log', encoding='utf-8', level=logging.DEBUG, filemode="w")
        # logging.debug(content)
        # logging.debug(result)
        self.wfile.write(result)
        self.log_into_file(self.rfile.read(), name="buf")
    
    def apply_headers(self, headers, end_header=True):
        for key in headers:
            if key.lower() == "content-length":
                self.send_header("Content-Length", str(int(headers[key]) + 10))
            self.send_header(key.lower(), headers[key])
        if end_header:
            self.end_headers()
    
    def log_into_file(self, x, mode="w", name="log"):
        with open(name + ".text", mode) as f:
            if mode == "w":
                x = str(x)
            f.write(x)
            f.close()

    def log_headers(self, headers):
        i=1
        for header in headers:             
            with open("header{}.text".format(str(i)), "w") as f:
                for key in header:
                    f.write(str(key) + ": " + header[key])
                    f.write("\n")
            # f.writelines(str(i))
            # f.writelines(str("  "))
            # f.writelines(str(self.headers[i]) + "\n")
    
    def save_remote_image(self, imgname):
        response, remote_file = h.request(ADDRESS + imgname)
        for i in ["last-modified", "cache-control", "etag", "expires", "accept-ranges", "status"]:
            if i in response:
                self.send_header(i, response[i])
        #self.apply_headers(response)
        with open(imgname, 'wb') as local_file:
            local_file.write(remote_file)
    
    def trim_header(self, header):
        whitelist = ["connection", "cache-control", "sec-ch-ua", "sec-ch-ua-mobile", "sec-ch-ua-platform",
        "User-Agent", "Accept-Encoding"]
        trimmed = {}
        for key in header:
            if key.lower() in whitelist:
                trimmed[key.lower()] = header[key]
        return trimmed

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
                node.text = re.sub(r"((?<!\S)(\b\w{6}\b)((?!\S)))", r"\g<1>™", node.text)
        for node in tree.xpath("//a[contains(@href,'https://news.ycombinator.com')]"):
            node.set("href", "")
        return tree



httpd = socketserver.ForkingTCPServer(('', PORT), Proxy)
print("Now serving at " + str(PORT))
httpd.serve_forever()

