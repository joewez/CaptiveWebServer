# CaptiveWebServer
Simple web server for serving a website from a captive portal

 - Requires uasyncio
 - Modify the webroot variable to match the location of your content
 - The script does not setup the AP
 - The script however assumes that it is acting as an AP
 - Simply import the script to run the server
 
DNS Server code culled from:
    https://github.com/amora-labs/micropython-captive-portal
