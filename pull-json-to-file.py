#!/usr/bin/python
from oauth2client import client			# Google OAuth Client
from oauth2client.file import Storage		# Google OAuth key container reader
import httplib2					# Used for Google OAuth events to get a new Bearer key
import urllib2					# URLLIB2 to make the requests to Google's API
import json					# Used to read the JSON output from Google
import datetime					# Get time data to pull logs from an hour ago
import isodate					# need to parse dates from the googz
import os					# file ops

# Open up the oauth2.txt file in the credential storage item:

storage = Storage('/opt/local/bin/oauth2.txt')
credentials = storage.get()

if(credentials.access_token_expired): # Our Bearer token has expired, we need to get a new one
	http = httplib2.Http()
	credentials.refresh(http)

# Now that we have a good Bearer token let's setup a request
# First let's grab the time in UTC:
lasthour = datetime.datetime.utcnow() 

# open the file with our json data
lastpull = open('/opt/google/latest', 'r')

#get the latest event in the file
latest_json = json.loads(lastpull.readline())

# get the latest event that occurred from within the google json file
last_event = latest_json['id']['time'].encode('utf8')

#need to parse that time object with isodate

get_datetime = isodate.parse_datetime(last_event)

# and augment the time by 1 second

new_start = get_datetime + datetime.timedelta(seconds=1)

#close the datafile
lastpull.close()

# Now let's setup our GET request, special attention needs to be paid to the new start time need to make it Google pretty by removing the +00:00 tail and replacing it with Z for Zulu


request = urllib2.Request("https://www.googleapis.com/admin/reports/v1/activity/users/all/applications/login?startTime=" + new_start.isoformat("T").replace('+00:00','Z'))

#this request should pull all activity from 1 second beyond the last event captured in the google log
# Now add a request_header with our Bearer token:

bearertoken="Bearer " + credentials.access_token
request.add_header("Authorization", bearertoken)

# Great now we have our request ready to roll, let's execute it with urrlib2:

response = urllib2.urlopen(request)

# the response should include the entire response, but let's read out a json blob:

log_raw = response.read()

# Great now we have the json_data, let's parse it

log_json = json.loads(log_raw)

# log file parsed, now let's try to write this to a file based on our date-time stamp; first we open a file
# Make sure there were events since the last event

if(log_json.has_key('items')):

	json_filename = "/opt/google/" + lasthour.isoformat().replace(':','_') + ".json"

	# open the log file for Splunk to append data to

	line_delimited_json_file = open(json_filename, 'a')

	# iterate the json blob and write it to the file then make the file interesting for Splunk

	for item in log_json['items']:
		json.dump(item, line_delimited_json_file)
		line_delimited_json_file.write('\n')

	# Close the file and make sure we exit nicely

	line_delimited_json_file.close()
	os.chmod(json_filename, 0600)
	os.remove("/opt/google/latest")
	os.symlink(json_filename, '/opt/google/latest')
# If nothing was found print a message to the screen
else:
	message = "No events from " + lasthour.isoformat("T")
	error_output = "/opt/google/" + lasthour.isoformat().replace(':','_') + ".error"
	error_file = open(error_output, 'w')
	error_file.write(message)
	error_file.write('\n')
	error_file.close()
