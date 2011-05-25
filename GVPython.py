#!/usr/bin/env python
#
# -- Colorado Denver South Mission --
#  -  Google Voice API for Python  -
#
import time, sys, math
import socket, httplib, urllib, urllib2, form_grabber
import imaplib, json

###
# Config
###
ROOT_URL = "http://google.com/voice"
IMAP_SERVER = "imap.googlemail.com"
IMAP_PORT = 587
MAX_RETRIES = 5

#!# End Config #!#

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

    def login(self):
        """
        Log in to Google Voice
        Returns True if successful, or False if unsuccessful
        """

        # Grab the login page, and then parse out the FORM data
        page = self.__get_doc(ROOT_URL)
        action_url, data = form_grabber.process_form(page, ROOT_URL)
        data["Email"] = self.__username
        data["Passwd"] = self.__password

        # Prepare the login request and try logging in
        data = urllib.urlencode(data)
        request = urllib2.Request(action_url, data)
        response = self.__get_doc(request)

        # Process the server's response
        if "Sign out" not in response:
            return False
        self.__logged_in = True

        # Get _rnr_se variable
        rnr_se = response.split("\"_rnr_se\"")[1].split("value=\"")[1].split("\"")[0]
        self.__rnr_se = rnr_se

        return True

    def send_sms_message(self, phone_number, message, count=0):
        """
        Send an SMS message to a given phone number.
        (Limited to 160 chars)
        """
        return
        if count == 5:
            print "Failed"
            return False

        if not self.__logged_in:
            if not self.login():
                raise NameError("Could not log in, check credentials and try again.")
        if count == 0:
            self.__show_status("Sending message to %s" % phone_number)

        response = {}

        if len(message) > 160:
            count = 1
            for i in range(0, len(message), 150):
                message_ = "(%d/%d) %s" % (count, int(math.ceil(len(message)/150.0)), message[i:i+150])
                count += 1
                action_url = "https://www.google.com/voice/sms/send/"
                post_data = {"id": "",
                            "phoneNumber": phone_number,
                            "text": message_,
                            "sendErrorSms": "0",
                            "_rnr_se": self.__rnr_se}
                post_data = urllib.urlencode(post_data)
                request = urllib2.Request(action_url, post_data)
                response = self.__get_doc(request)
                response = json.loads(response)
        else:
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
            count += 1
            time.sleep(5)
            self.send_sms_message(phone_number, message, count)
        return response["ok"]

    def get_sms_messages(self, clear_messages=True):
        # Login to GMail's IMAP Server
        self.__show_status("Logging in to IMAP server")
        imap_connection = imaplib.IMAP4_SSL(IMAP_SERVER)
        imap_connection.login(self.__username, self.__password)
        print "Done"

        # Retrieve messages
        self.__show_status("Retrieving raw messages from server")
        raw_messages = []
        imap_connection.select("INBOX")
        status, data = imap_connection.search(None, 'ALL')
        for message_id in data[0].split():
            status, response = imap_connection.fetch(message_id, '(RFC822)')
            if status == "OK":
                # Get message body from response
                message_body = response[0][1]
                raw_messages.append(message_body)
        print "Done"

        # Process raw messages into message dictionary objects
        self.__show_status("Processing raw messages")
        messages = []
        for raw_message in raw_messages:
            # Instantiate message dictionary
            message = {}

            # Verify there's the message includes the proper MIME type for processing
            if not "Content-Type: text/plain;" in raw_message:
                continue

            # Get the FROM header
            for line in raw_message.split("\n"):
                if not line.startswith("From: "):
                    continue
                # get the 'display' and 'real' from information
                #   'display' = "3035073572"
                #   'real' = "17209242376.13035073572.RhKnXCbXS5@txt.voice.google.com"
                line = line.split("<")
                from_display = line[0]
                from_display = from_display.split("From: ")[1]
                from_display = from_display.strip()
                from_display = from_display.replace("\"", "")
                from_display = from_display.replace(" ", "")
                from_display = from_display.replace("(", "")
                from_display = from_display.replace(")", "")
                from_display = from_display.replace("-", "")
                from_real = line[1]
                from_real = from_real.split(">")[0]
                from_real = from_real.strip()
                from_information = {}
                from_information["display"] = from_display
                from_information["real"] = from_real
                message["from"] = from_information
                break

            # Make sure the messages is from a GV sms forwarding address
            if not message["from"]["real"].endswith("txt.voice.google.com"):
                continue

            # Get message body
            message_body = raw_message.split("Content-Type: text/plain;")[1]
            message_body = message_body.split("delsp=yes")[1]
            message_body = message_body.split("--\r\nSent using")[0]
            message_body = message_body.strip()
            message_body = message_body.lower()
            message["body"] = message_body
            # TODO - find and strip off signature
            messages.append(message)

        print "Done"

        if clear_messages:
        # Clear messages from inbox
            typ, data = imap_connection.search(None, 'ALL')
            for num in data[0].split():
               imap_connection.store(num, '+FLAGS', '\\Deleted')
            imap_connection.expunge()

        #close server
        imap_connection.close()
        imap_connection.logout()

        return messages