#!/usr/bin/env python

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import io
import sys
import time
import argparse
import subprocess
import validators
import configparser

from PIL import Image, ImageOps

config = None

imagePrefix = "fresh_image_"

def StoreImages(images, output):
	print(f"storing images in {output}")
	for i, image in enumerate(images):
		imageIdentifier = f"{imagePrefix}{i}.png"
		imageFilePath = os.path.join(output, imageIdentifier)

		print(f"Storing image as: {imageFilePath}")
		with open(imageFilePath, "wb") as f:
			f.write(image)

def ViewImage(path):
	subprocess.Popen(['xdg-open', path])

def ViewImages(images, path):
	StoreImages(images, path)
	for i in range(0, len(images)):
		imageFilePath = os.path.join(path, f"{imagePrefix}{i}.png")
		print(f"Launching viewer for image: {imageFilePath}")
		ViewImage(imageFilePath)

def FindElementClass(driver, className):
	elements = driver.find_elements_by_xpath('//*[@class]')
	for element in elements:
		try:
			attr = element.get_attribute('class')
			if attr == className:
				return element
		except Exception as e:
			pass # just ignore the 'StaleElementReferenceException'

def GetElementImage(driver, element):
	return element.screenshot_as_png

def ImageToGrayScale(imageRaw):
	image = Image.open(io.BytesIO(imageRaw))
	image = ImageOps.grayscale(image)
	data = io.BytesIO()
	image.save(data, format='PNG')

	return data.getvalue()

def GetRecipe(url):
	""" Load the needed class descriptions for elements of interest. """
	elementClasses = []
	for key in config['HelloFresh']:
		value = config['HelloFresh'][key]
		elementClasses.append(value)
	
	options = Options()
	options.headless = True

	driver = webdriver.Firefox(options=options)
	driver.get(url)
	
	# accept the cookie.
	CookieAcceptId = config['Cookie']['CookieElemId']
	WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, CookieAcceptId))).click()
	
	# images that are dynamically loaded need to be scrolled into view.
	body = driver.find_element_by_css_selector('body')
	for i in range(0, 10):
		body.send_keys(Keys.PAGE_DOWN)
		time.sleep(1.0)
	
	imageResults = []
	for elementClass in elementClasses:
		element = FindElementClass(driver, elementClass)
		elementImage = GetElementImage(driver, element)

		grayscaled = ImageToGrayScale(elementImage)
		imageResults.append(grayscaled)
	
	driver.quit()

	return imageResults

def SendToPrinter(images):
	""" Generate printing options from config file."""
	printCommandOpts = []
	for key in config['LinuxPrintingOpts']:
		value = config['LinuxPrintingOpts'][key]
		subOptStr = f"{key}={value}" if value else f"{key}"
		printCommandOpts.append("-o " + subOptStr)
	print(f"lpr command-line options: {printCommandOpts}")
	
	""" Send images to the printer. """
	printCommand = ['lpr', *printCommandOpts]
	print(f"command: {printCommand}")
	for image in images:
		lpr = subprocess.Popen(printCommand, stdin=subprocess.PIPE)
		stdout, stderr = lpr.communicate(input=image)

def LoadConfig(configFile):
	config = configparser.ConfigParser()
	config.read(configFile)
	return config

def ValidateHelloFreshUrl(url):
	validUrl = bool(validators.url(url))
	hellofreshUrl = "hellofresh" in url

	if not (validUrl and hellofreshUrl):
		raise argparse.ArgumentTypeError
	
	return url

def CheckConfigExists(config):
	if os.path.exists(config):
		return config
	
	raise argparse.ArgumentTypeError(f"No such file or directory, {config}")

def Host(args):
	from flask import Flask, render_template_string, request
	formTemplate = """
	<form "/data" method="POST">
    	<p>Recipe URL <input type="text" name="recipe"/></p>
	</form>
	"""

	app = Flask(__name__)

	@app.route("/", methods=['GET', 'POST'])
	def form():
		if request.method == 'POST':
			recipeUrl = request.form['recipe']
			print(f"recipe url: {recipeUrl}")
			images = []
			try:
				images = GetRecipe(recipeUrl)
			except Exception as e:
				print(f"got exception: {e}")
				render_template_string(formTemplate)
			if args.print:
				print("Sending a recipe print job.")
				SendToPrinter(images)
			else:
				print("Not sending a recipe print job.")
			
			if args.show:
				print("Launching image viewer.")
				ViewImages(images, args.output)
			else:
				print("Not showing images.")
		
		return render_template_string(formTemplate)
	app.run(host='192.168.178.25', port=8080)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Download and Print Hello-Fresh recipes.")
	
	parser.formatter_class = lambda prog: argparse.RawTextHelpFormatter(prog, max_help_position=30)

	parser.add_argument('-u', '--url',
						type=ValidateHelloFreshUrl,
						default=None,
						required=False,
						help="recipe url")
	parser.add_argument('-c', '--config',
						type=CheckConfigExists,
						default="Config.ini",
						required=False,
						help="Config to load, default is Config.ini")
	parser.add_argument('--host',
						default=False,
						required=False,
						action='store_true',
						help='host recipe url entry page')
	parser.add_argument('--print',
						default=False,
						required=False,
						action='store_true',
						help="send a printjob.")
	parser.add_argument('--show',
						default=False,
						required=False,
						action='store_true',
						help="launch a system image viewer.")
	parser.add_argument('-o', '--output',
						default="/tmp",
						required=False,
						help="set the output location for images.")
	parser.add_argument('--verbose',
						required=False,
						action="store_true",
						help="enable verbose printing.")

	args = parser.parse_args()

	# if verbose then print everything to stdout
	if not args.verbose:
		print = lambda *args, **kwargs: None
	
	print(args)

	print(f"Hello-fresh url received:	"f"{args.url}")
	print(f"Using Config:				"f"{args.config}")
	print(f"Send printjob:				"f"{args.print}")
	print(f"Launch image view:			"f"{args.show}")
	print(f"Output images to:			"f"{args.output}")

	scriptFilePath = os.path.realpath(__file__)
	scriptPath = os.path.dirname(scriptFilePath)

	configFilename = args.config
	configFilePath = os.path.join(scriptPath, configFilename)

	print("scriptFilePath:	"f"{scriptFilePath}")
	print("scriptPath:		"f"{scriptPath}")
	print("configFilename:	"f"{configFilename}")
	print("configFilePath:	"f"{configFilePath}")

	config = LoadConfig(configFilePath)

	images = []
	if args.url:
		images = GetRecipe(args.url)

	if args.host:
		print("Start hosting at http://localhost:8080/")
		Host(args)
		exit(0)

	if args.print:
		print("Sending a recipe print job.")
		SendToPrinter(images)
	else:
		print("Not sending a recipe print job.")
	
	if args.show:
		print("Launching image viewer.")
		ViewImages(images, args.output)
	else:
		print("Not showing images.")
