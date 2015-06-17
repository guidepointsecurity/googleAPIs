# googleAPIs

A tool kit to interact with Google's APIs and grab logs and reports
To be updated to include Google Drive API requests where possible
Note - In order to grab Drive access you need a Google Apps Unlimited license

=== BEFORE RUNNING ===

1.	Make sure the oauth2client and isodate libraries are installed:
	sudo easy_install oauth2client
	sudo easy_install isodate
2.	Make sure your paths are right in all your files, the files are currently written this way:
	pull-json-to-file.py:
		Data dropped in /opt/google
		Auth files dropped in /opt/local/bin
		Python script lives in /opt/local/bin
	config.py:
		All data is dropped locally;
		Recommend to run in /opt/google the first time then move oauth2.txt to /opt/local/bin along with pull-json-to-file.py
3.	I've run this with cron to execute every 15 minutes, YMMV
4.	Splunk configuration documentation to come for my deployment


=== TODO ===

1.	Add code to write output to either CSV or JSON
2.	Rewrite pull-to-json.py to be a function
3.	Rewrite Admin Reports and pull-to-json to use a configuration file
4.	Walk all accounts in domain and pull all Drive logs for all accounts in domain
