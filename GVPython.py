#!/usr/bin/env python
#
# -- Colorado Denver South Mission --
# Google Voice API for Python
#
import time, sys
import socket, httplib, urllib, urllib2, form_grabber
import json
from xml.dom import minidom

###
# Config
###
ROOT_URL = "http://google.com/voice"
SMS_INBOX_URL = "https://www.google.com/voice/inbox/recent/sms/"
MAX_RETRIES = 5

# super cool debug function
def display_dict(dictionary, header):
    print "-" * 50
    print "- %s" % header
    print "-" * 50
    for key in dictionary.keys():
        print "'%s' => '%s'" % (key, dictionary[key])
        print
    print "-" * 50
    print

class session:
    def __init__(self, username, password):
        """
        Initialize Google Voice session class
        """
        self.__username = username
        self.__password = password
        self.__opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        self.__opener.addheaders = [('User-agent', 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)')]
        self.__logged_in = False
        self.__rnr_se = "" # session variable needed for sending SMS messages

    def __get_doc(self, url):
        """
        Return HTML string contents of a given URL
        """
        for i in range(0, MAX_RETRIES):
            try:
                page = self.__opener.open(url).read()
                return page
            except urllib2.URLError:
                time.sleep(3)
            except httplib.BadStatusLine or httplib.InvalidURL:
                time.sleep(3)
            except socket.error or socket.timeout:
                time.sleep(3)
            except:
                import traceback
                traceback.print_exc()
                count += 1
        raise NameError("Failed to grab URL: %s", url)

    def __show_status(self, message):
        """
        Print line to console without \n
        """
        sys.stdout.write("[+] %s, " % message)
        sys.stdout.flush()

    def login(self):
        """
        Log in to Google Voice
        Returns True if successful, or False if unsuccessful
        """

        # Grab the login page, and then parse out the FORM data
        self.__show_status("Getting login page")
        page = self.__get_doc(ROOT_URL)
        action_url, data = form_grabber.process_form(page, ROOT_URL)
        data["Email"] = self.__username
        data["Passwd"] = self.__password
        print "Done"

        # Prepare the login request and try logging in
        self.__show_status("Attempting login")
        data = urllib.urlencode(data)
        request = urllib2.Request(action_url, data)
        response = self.__get_doc(request)
        print "Done"

        # Process the server's response
        if "Sign out" not in response:
            return False
        self.__logged_in = True

        # Get _rnr_se variable
        rnr_se = response.split("\"_rnr_se\"")[1].split("value=\"")[1].split("\"")[0]
        self.__rnr_se = rnr_se

        return True

    def get_SMS_messages(self, unread_only=False):
        """
        IN PROGRESS
        Get array of text messages from GV
        """
        if not self.__logged_in:
            raise NameError("Not logged in, log in first.")

        # Get the XML file with all the SMS goodies in it
        self.__show_status("Getting SMS Messages page")
        page = self.__get_doc(SMS_INBOX_URL)
        a = open("page.xml", "w")
        a.write(page)
        a.close()
        print "Done"

        # Begin parsing XML response
        # Parse root JSON node from XML response
        xmldata = minidom.parseString(page)
        json_data = xmldata.getElementsByTagName("json")[0]
        json_data = json_data.childNodes[0].data
        json_data = json.loads(json_data)
        
        # start parsing through received messages
        messages = json_data["messages"]
        for key in messages.keys():
            message = messages[key]
            display_dict(message, "Message")

    def send_sms_message(self, phone_number, message):
        """
        Send an SMS message to a given phone number.
        (Limited to 160 chars)
        """
        if not self.__logged_in:
            raise NameError("Not logged in, log in first.")
        if len(message) > 160:
            raise NameError("SMS mess has can be no longer than 160 characters.")

        self.__show_status("Sending message to %s" % phone_number)
        action_url = "https://www.google.com/voice/sms/send/"
        post_data = {"id": "",
                    "phoneNumber": phone_number,
                    "text": message,
                    "sendErrorSms": "0",
                    "_rnr_se": self.__rnr_se}
        post_data = urllib.urlencode(post_data)
        request = urllib2.Request(action_url, post_data)
        response = self.__get_doc(request)
        response = json.loads(response)
        if response["ok"]:
            print "Done"
        else:
            print "Failed"
        return response["ok"]


