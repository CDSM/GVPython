#!/usr/bin/env python
# GVPython API testing script
import GVPython

if __name__ == '__main__':
    gv = GVPython.session("cdsm.tech@gmail.com", "captainmoroni")
    if gv.login():
        print gv.get_SMS_messages(unread_only=True)
#        print gv.send_sms_message("9704242914", "this will probably be my last test text for the day <3 smith")
    else:
        print "[!] Failed to log in, oh no!"
