# Captive Web Server
Simple MicroPython web server for serving a website from a captive portal
(Generally meant for an ESP8266 Device)

 - Copy the application file _captive_http.py_ to the root of an ESP8266 device running a recent version of MicroPython
 - Create a directory on your file system called /wwwroot
 - Place the **capture.html** file along with the rest of your content including an **index.html** file
 - The script does not setup the AP (Type **help()** at the REPL prompt for information on this)
   - The script however assumes that it is acting as an AP
   - Make sure the DNS server is set to 192.168.4.1
   - See https://github.com/joewez/ESP8266-WiFi-Utilities
  - Simply import the script to run the server (or import it in your _main.py_)

<p>
    >>> import wifi <br />
    >>> wifi.access_point('tester', 'password', dns=True) <br />
    >>> import captive_http() <br />
</p>

DNS Server code culled from:
    https://github.com/amora-labs/micropython-captive-portal
