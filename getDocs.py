#!/usr/bin/python

# 2015-05-28 - Matt Ahrens / matt.ahrens@guidepointsecurity.com
# Script to be run to grab all Google Docs access for a specific user.
# config.py is around for the initial pull of these events and the google list API
# Usage - python ./getDocs.py user@domain.com

from oauth2client import client			# Google OAuth Client
from oauth2client.file import Storage		# Google OAuth key container reader
import httplib2					# Used for Google OAuth events to get a new Bearer key
import urllib2					# URLLIB2 to make the requests to Google's API
import json					# Used to read the JSON output from Google
import datetime					# Get time data to pull logs from an hour ago
import isodate					# need to parse dates from the googz
import os					# file ops
import sys

def getDrive(username):
   # Snag the right date variable
   #d = datetime.date.today()-datetime.timedelta(days=date_modifier)
   #request_date=str(d) # convert it to a string
   # get Google credentials out of storage
   storage = Storage('/opt/local/bin/oauth2.txt')
   credentials = storage.get()
   if(credentials.access_token_expired): # check to see if our google oauth token needs to get fixed, if it does, go get us a new one
      http = httplib2.Http()
      credentials.refresh(http)
   request = urllib2.Request('https://www.googleapis.com/admin/reports/v1/activity/users/' + username + '/applications/drive')# build request
   bearertoken = "Bearer " + credentials.access_token # format bearer token
   request.add_header("Authorization", bearertoken) # add authorization header to authorize request
   try: response = urllib2.urlopen(request) # let's get fancy and try the request, if we get a HTTP error it's time to stop
   except urllib2.HTTPError as e: # snag the HTTP error
   	   print "URLLib2 returned HTTP code: " + str(e.code) + " at date " + request_date
   	   return False # exit the function cleanly and tell our automator scripts we've hit the end of the time Google has for us
   log_raw = response.read() # if this succeeds, we need to check the data
   print log_raw


if(len(sys.argv)<2):
   print "Usage: " + sys.argv[0] + " user@domain.com"
else:
   getDrive(sys.argv[1])

