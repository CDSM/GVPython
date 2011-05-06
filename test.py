#!/usr/bin/env python
# GVPython API testing script
import GVPython

if __name__ == '__main__':
    gv = GVPython.session("cdsm.tech@gmail.com", "captainmoroni")
    sms_messages = gv.get_sms_messages(clear_messages=False)
    print "[+] %d new SMS messages" % len(sms_messages)
    print "[+] Behold the text messages!"
    for message in sms_messages:
            print "-"*50
            print "From: %s" % message["from"]["display"]
            print "--"
            print message["body"]
            print "-"*50