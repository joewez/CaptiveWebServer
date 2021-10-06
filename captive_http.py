#
# captive_http.py
# DNS and HTTP server meant strictly for serving static html content stored on the flash file system.
#
# The only requirement is that a network connection is established..., either as a client to an 
# existing wifi network or as an access point... before the server is started.
#
# Usage:
# >>> import captive_http
# >>> captive_http.start()
#
# Based on code from https://github.com/metachris/micropython-minimal-webserver-asyncio3
#

import gc
import uasyncio as asyncio
import uos
import network
import socket

mime_types = {
    "html": "text/html",
    "css": "text/css",
    "js": "text/javascript",
    "png": "image/png",
    "gif": "image/gif",
    "jpeg": "image/jpeg",
    "jpg": "image/jpeg",
    "ttf": "font/ttf",
    "woff": "font/woff",
    "woff2": "font/woff2",
    "pdf": "application/pdf",
    "ico": "image/x-icon"
}

# Looks up the content-type based on the file extension
def get_mime_type(file):
    mime = "text/plain"
    cache = False
    extension = file.split(".")[-1]
    if extension in mime_types:
        mime = mime_types[extension]
        cache = (extension != "html")
    return mime, cache

def merge(*args):
    slash = '/'
    r = ''
    for part in args:
        r += (slash + part)
    r = r.replace(3 * slash, slash)
    r = r.replace(2 * slash, slash)
    if r != slash and r[-1] == slash:
        r = r[:-1]
    return r

def get_address():
    addr = ''
    wlan = network.WLAN(network.STA_IF)
    if wlan.active():
        addr = wlan.ifconfig()[0]
    else:
        wlan = network.WLAN(network.AP_IF)
        if wlan.active():
            addr = wlan.ifconfig()[0]
    return addr

# Quick check if a file exists
def exists(file):
    try:
        s = uos.stat(file)
        return True
    except:
        return False    

class DNSQuery:
    def __init__(self, data):
        self.data = data
        self.domain = ''
        tipo = (data[2] >> 3) & 15  # Opcode bits
        if tipo == 0:  # Standard query
            ini = 12
            lon = data[ini]
            while lon != 0:
                self.domain += data[ini + 1:ini + lon + 1].decode('utf-8') + '.'
                ini += lon + 1
                lon = data[ini]
        print("searched domain:" + self.domain)

    def response(self, ip):

        print("Response {} == {}".format(self.domain, ip))
        if self.domain:
            packet = self.data[:2] + b'\x81\x80'
            packet += self.data[4:6] + self.data[4:6] + b'\x00\x00\x00\x00'  # Questions and Answers Counts
            packet += self.data[12:]  # Original Domain Name Question
            packet += b'\xC0\x0C'  # Pointer to domain name
            packet += b'\x00\x01\x00\x01\x00\x00\x00\x3C\x00\x04'  # Response type, ttl and resource data length -> 4 bytes
            packet += bytes(map(int, ip.split('.')))  # 4bytes of IP
        print(packet)
        return packet

class MyDNSServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(('0.0.0.0', 53))

    async def handle_query(self, ip):
        while True:
            try:
                data, addr = self.sock.recvfrom(1024)
                query = DNSQuery(data)
                this.sock.sendto(query.response(addr), ip)
            except:
                pass
            await asyncio.sleep_ms(300)


class MyHTTPServer:

    def __init__(self, root_path, default_document, network_port):
        self.root_path = root_path
        self.default_document = default_document
        self.network_port = network_port
        self.buffer = bytearray(512)

    async def handle_request(self, reader, writer):
        gc.collect()

        # Get HTTP request line
        data = await reader.readline()
        request_line = data.decode()

        # Read headers
        headers = {}
        while True:
            gc.collect()
            line = await reader.readline()
            if line == b'\r\n': break
            frags = line.split(b':', 1)
            if len(frags) != 2:
                return
            headers[frags[0]] = frags[1].strip()

        # Handle the request
        if len(request_line) > 0:
            parts = request_line.split(' ')
            if parts[0] == 'GET':
                resource = parts[1]
                if resource == '/' or resource == '':
                    resource = self.default_document
                target = merge(self.root_path, resource)

                # fix destination URL to be consistent with this web server
                if not exists(target):
                    target = '/wwwroot/captive.html'

                # open and read the file contents back over the socket
                mime_type, cacheable = get_mime_type(target)
                response_header = 'HTTP/1.0 200 OK\r\n'
                response_header += 'Content-Type: {}\r\n'.format(mime_type)
                if cacheable:
                    response_header += 'Cache-Control: public, max-age=604800, immutable\r\n'
                response_header += '\r\n'
                response = response_header

                f = open(target, 'rb')
                count = f.readinto(self.buffer)
                while count > 0:
                    await writer.awrite(self.buffer, off=0, sz=count)
                    count = f.readinto(self.buffer)
                f.close()

            else:
                await writer.awrite('HTTP/1.0 500 Not Implemented (Yet?!)\r\n\r\n')

        # Close the socket
        await writer.aclose()

def start(root_path='/wwwroot', default_document='index.html', network_port=80):
    try:
        my_address = get_address()

        loop = asyncio.get_event_loop()

        print('Starting DNS server...')
        mydnsserver = MyDNSServer()
        loop.create_task(mydnsserver.handle_query(my_address))

        print('Starting web server at {0}:{1}...'.format(my_address, network_port))
        myhttpserver = MyHTTPServer(root_path, default_document, network_port)
        server = asyncio.start_server(myhttpserver.handle_request, "0.0.0.0", network_port)
        loop.create_task(server)

        print('...(<ctrl>+c to stop)...')

        loop.run_forever()

    except KeyboardInterrupt:
        print('Servers stopped.')
    finally:
        asyncio.new_event_loop()

start()