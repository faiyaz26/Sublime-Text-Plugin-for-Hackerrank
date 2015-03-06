import sublime, sublime_plugin
import urllib, urllib2, threading
import json, time, random, hashlib
import sys, os, re
import Cookie
from sys import platform as _platform

class HackerRankRun(threading.Thread):
	def __init__(self, problem, lang, code):
		self.problem = problem
		self.code  = code
		self.lang  = lang
		self.done  = False
		threading.Thread.__init__(self)
		self.url = 'https://www.hackerrank.com/rest/contests/master/challenges/%s/compile_tests'%problem
		self.cookie = None
		self.submission_id = None
		self.submitted = False

	'''
	This function will submit code on Hackerrank and will get submission_id for successful submission
	'''
	def submit(self):
		try:
			json_dict = {"code": self.code,"language":self.lang,"customtestcase": 'false'} ## json request
			data = urllib.urlencode(json_dict)
			http_file = urllib2.urlopen(self.url, data)

			res = json.loads(http_file.read())
			tried = 0
			while self.submitted == False and tried < 5: #will try for 5 times
				tried = tried + 1
				if res['status']:
					headers = http_file.info()
					ck = Cookie.SimpleCookie(headers['Set-Cookie'])
					self.cookie = "hackerrank_mixpanel_token=" + ck['hackerrank_mixpanel_token'].value +";"+ "_hackerrank_session=" + ck['_hackerrank_session'].value + ";"
					if res['model']['id']:
						self.submission_id = res['model']['id']
						self.submitted = True
						print "Code Submitted. Waiting for result..."
					else:
						print "Error occurred during code submission. Will Try again in 1 seconds..."
						time.sleep(1)
			if self.submitted == False:
				print "Could not submit, try again"
		except (urllib2.HTTPError) as (e):
			print "Something went wrong. Check the problem slug"
		except (urllib2.URLError) as (e):
			print "Something went wrong buddy, try again"
		return

	'''
	This function will check for the final status of the submission and fetch the result
	'''
	def getResult(self):
		try:
			tried = 0
			while self.done == False and tried < 5:
				request = urllib2.Request(self.url + '/' + str(self.submission_id) + "?_="+str(time.time()*1000))
				request.add_header('Cookie', self.cookie)
				http_file = urllib2.urlopen(request)
				result = http_file.read()
				result = json.loads(result)
				if result['model']['status'] == 0:
					print "Compilation and Test Case run not finished yet, wait 1 more seconds"
					time.sleep(1)
				else:
					print "All done.. Printing Result"
					self.done = True
				tried = tried + 1

			if self.done == False:
				print "Something is wrong.."
			else:
				model = result['model']

				total = len(model['testcase_message'])
				success = 0
				for i in range(0, len(model['testcase_message'])):
					if model['testcase_message'][i] == 'Success':
						success = success + 1

				print "Total Testcases: %d, Passed: %d"% (total, success)

				for i in range(0, len(model['testcase_message'])):
					print "Testcase #%d: %s"%(i+1, model['testcase_message'][i])
		except (urllib2.HTTPError) as (e):
			print "Something went wrong. Check the problem slug"
		except (urllib2.URLError) as (e):
			print "Something went wrong buddy, try again"
		return


	'''
	Run the thread
	'''
	def run(self):
		self.submit()
		if self.submitted == True:
			self.getResult()
		print "------------------------------"
		return

'''
Core Code
'''
class HackerRankCompileAndRunCommand(sublime_plugin.TextCommand):
	def getFileAndExtension(self): # function to get the current view file name and extension
		file_path = self.view.file_name()
		if file_path == None:
			return None, None
		sep = '\\' # default for windows
		if _platform == "linux" or _platform == "linux2" or _platform == "darwin":
			sep = '/'

		file_name = file_path[file_path.rfind(sep)+1:] 
		sep2 = '.'
		ext  = file_name[file_name.rfind(sep2)+1:] # extension of the file
		file_name = file_name[:file_name.rfind(sep2)] #real file name
		return file_name, ext


	''' 
	This function will run the plugin. With this plugin one can directly compile and test on Hackerrank.
	File name should be the slug of the problem
	Based on extension it will select the language
	Currently it works with cpp, c, java, php
	Use Ctrl + Alt + H to run the test
	or use Ctrl + Shift + P, on command pallate type Hackerrank Run Code
	'''
	def run(self, edit):
		sublime.active_window().run_command("show_panel", {"panel": "console", "toggle": True})
		print "Hackerrank Plugin by Ahmad Faiyaz"
		print "Process started"
		print "------------------------------"
		file_name, ext = self.getFileAndExtension()
		content = self.view.substr(sublime.Region(0, self.view.size()))
		if file_name == None:
			print "Please save the file with correct problem slug and extension"
			print "------------------------------"
			return
		hackerrankRun = HackerRankRun(file_name, ext, content)
		hackerrankRun.start()
		return
