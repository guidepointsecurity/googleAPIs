#!/usr/bin/python
# Script to automatically configure the google admin sdk pulls
from oauth2client import client				# Google OAuth Client
from oauth2client.file import Storage		# Google OAuth key container reader
import httplib2								# Used for Google OAuth events to get a new Bearer key
import urllib2								# URLLIB2 to make the requests to Google's API
import json									# Used to read the JSON output from Google
import os									# file ops (symlink/remove/chmod/etc)
import sys									# Cleanup actions
import time									# silly file io hackery
import datetime 							# need to parse time to iterate through events
import isodate								# need to parse dates from the googz; additional library for easy_install

print "# Quick script to configure Google authentication, and pull the initial set of data into a JSON file, run this script as the Splunk user."
print "# 2013-10-17 / Matt Ahrens (matt.ahrens@guidepointsecurity.com)"
print "# Prepare by having a Google Admin configuring a Google API project from: https://cloud.google.com/console"
print "# Make sure to grant access for the API project to the Admin SDK and Audit APIs"
print "# Add a \"Registered App\" to the project called GApps_Login_Collector"
print "# Click the \"Donwload JSON\" button and save the file to client_secrets.json\n"

client_secrets_filename = raw_input("Please enter the path to your client_secrets.json file: ")

# Trying to get fancy with file IO

try:
	with open(client_secrets_filename, 'r'):
		time.sleep(1)
except IOError:
	print "No client secrets file found there time quit!"
	sys.exit()

# Parse the client_secrets.json file
clientSecretsData = open(client_secrets_filename, 'r')
clientSecretsJson = json.loads(clientSecretsData.read())
clientSecretsData.close()

# capture the right reidrect uri from the client secrets so the links worky
if(clientSecretsJson.has_key('web')):
	redirectUri = clientSecretsJson['web']['redirect_uris'][0]
elif(clientSecretsJson.has_key('installed')):
	redirectUri = clientSecretsJson['installed']['redirect_uris'][0]
else:
	print "Can't find the 'redirect_uris' key in the client_secrets.json file, please verify the client_secrets.json file and try again"
	exit	
# make the flow object for the oauth2 session
flow = client.flow_from_clientsecrets(client_secrets_filename, scope='https://www.googleapis.com/auth/admin.reports.audit.readonly', redirect_uri=redirectUri)

# get the auth_uri from the flow
auth_uri = flow.step1_get_authorize_url()

print "Goto this Website as a Google Admin, then copy/paste the authorization code in the link: " + auth_uri + '\n'

code = raw_input("Paste the authorization code here: ")

# get the credentials with the code you mashed in here
credentials = flow.step2_exchange(code)

# store the credentials in the right place

storage = Storage('oauth2.txt')
storage.put(credentials)

# verify our bearer token from the credential storage

if(credentials.access_token_expired): # Our Bearer token has expired, we need to get a new one
	http = httplib2.Http()
	credentials.refresh(http)

# Let's pull the last 1000 events from the domain:

request = urllib2.Request("https://www.googleapis.com/admin/reports/v1/activity/users/all/applications/login")

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

# let's iterate the first 1000 log events

eventcount=0

initial_json_dump = open("initial-log-dump.json", 'w')
last_time=""
first_time=""
for items in log_json['items']:
	json.dump(items, initial_json_dump)
	initial_json_dump.write('\n')
	last_time=items['id']['time'].encode('utf8')
	if(eventcount==0):
		first_time=items['id']['time'].encode('utf8')
	eventcount = eventcount + 1

# Work our way backwards with timestamps from the last event we wrote
time.sleep(5)
print str(eventcount) + " Events written, last event written was from " + last_time + '\n'

print "Pulling more data do you really want to do this, we'll sleep for 10 seconds while you think about it!"
time.sleep(10)
get_datetime = isodate.parse_datetime(last_time)
new_end = get_datetime - datetime.timedelta(seconds=1)
loop_request = urllib2.Request("https://www.googleapis.com/admin/reports/v1/activity/users/all/applications/login?endTime=" + new_end.isoformat("T").replace('+00:00','Z'))
loop_request.add_header("Authorization", bearertoken)
loop_lograw = urllib2.urlopen(loop_request)
log_json = json.loads(loop_lograw.read())

while(log_json.has_key('items')):
	for items in log_json['items']:
		json.dump(items, initial_json_dump)
		initial_json_dump.write('\n')
		last_time=items['id']['time'].encode('utf8')
		eventcount=eventcount+1
	print str(eventcount) + " Events written, last event written was from " + last_time + '\n'
	print "Pulling more data do you really want to do this, we'll sleep for 10 seconds while you think about it!"
	time.sleep(10)
	get_datetime = isodate.parse_datetime(last_time)
	new_end = get_datetime - datetime.timedelta(seconds=1)
	loop_request = urllib2.Request("https://www.googleapis.com/admin/reports/v1/activity/users/all/applications/login?endTime=" + new_end.isoformat("T").replace('+00:00','Z'))
	if(credentials.access_token_expired):
		http = httplib2.Http()
		credentials.refresh(http)
		bearertoken="Bearer " + credentials.access_token
	loop_request.add_header("Authorization", bearertoken)
	loop_lograw = urllib2.urlopen(loop_request)
	log_json = json.loads(loop_lograw.read())
	
print "All done, we have collected " + str(eventcount) + " from " + first_time + " to " + last_time + " into a file called initial-log-dump.json, now linking this to latest and saving our oauth2.txt file so we're ready to roll\n"

# prep for the pull script
os.symlink('initial-log-dump.json', 'latest')

# clean up permissions so only the owner can read this file
os.chmod('initial-log-dump.json', 0600)






