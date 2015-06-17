#!/usr/bin/python

# 2013-10-28 - Matt Ahrens / matt@guidepointsecurity.com
# Script to be run daily to pull Google usage reports to a JSON file to be read by Splunkity-Splunk
# config.py is around for the initial pull of these events and the google list API

from oauth2client import client			# Google OAuth Client
from oauth2client.file import Storage		# Google OAuth key container reader
import httplib2					# Used for Google OAuth events to get a new Bearer key
import urllib2					# URLLIB2 to make the requests to Google's API
import json					# Used to read the JSON output from Google
import datetime					# Get time data to pull logs from an hour ago
import isodate					# need to parse dates from the googz
import os					# file ops

# just a function to snag reports for a specific date modifier, that's an integer used to decrement the date (usually 3 days is what we want for a daily run of this script)
def get_usage_reports(date_modifier):
   # Snag the right date variable
   d = datetime.date.today()-datetime.timedelta(days=date_modifier)
   request_date=str(d) # convert it to a string
   # get Google credentials out of storage
   storage = Storage('oauth2.txt')
   credentials = storage.get()
   if(credentials.access_token_expired): # check to see if our google oauth token needs to get fixed, if it does, go get us a new one
      http = httplib2.Http()
      credentials.refresh(http)
   request = urllib2.Request('https://www.googleapis.com/admin/reports/v1/usage/users/all/dates/' + request_date) # build request
   bearertoken = "Bearer " + credentials.access_token # format bearer token
   request.add_header("Authorization", bearertoken) # add authorization header to authorize request
   try: response = urllib2.urlopen(request) # let's get fancy and try the request, if we get a HTTP error it's time to stop
   except urllib2.HTTPError as e: # snag the HTTP error
   	   print "URLLib2 returned HTTP code: " + str(e.code) + " at date " + request_date
   	   return False # exit the function cleanly and tell our automator scripts we've hit the end of the time Google has for us
   log_raw = response.read() # if this succeeds, we need to check the data
   outputfilename = request_date + '.json' # write the output based on the date the events occurred
   outfile = open(outputfilename, 'w') # open the file in read/write mode
   log_json=json.loads(log_raw) # load the JSON output
   if(log_json.has_key('usageReports')): # check to see if there were any events, for some reason one or two days had no events (maybe a google issue?)
      for reports in log_json['usageReports']: # itirerate through the events line by line to wash Google's formatting
         json.dump(reports, outfile) # write the events to a "json" file
         outfile.write('\n') # make it easier for Splunk to read
   else:
      print "No usage report for " + request_date + '\n' # this is if we found no usageReports for the date, just printing an error to screen
   return True # success!

get_usage_reports(3) # just a simple call of the function we wrote for other itireration