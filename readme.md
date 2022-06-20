# Description

This tool allows you to download recipes from hello-fresh so that you can print them out.

# Capabilities
using selenium this script connects to a hello fresh website, does some magic
then creates some snapshots of the relevant elements on the page and
depending on the command line options given shows you the result or sends a print job.

potentially in the future the script could be made to also generate only textually output it isn't hard to add.

## command-line usage
```
usage: freshPrint.py [-h] -u URL [-c CONFIG] [--print] [--show] [-o OUTPUT] [--verbose]

Download and Print Hello-Fresh recipes.

optional arguments:
  -h, --help                  show this help message and exit
  -u URL, --url URL           recipe url
  -c CONFIG, --config CONFIG  Config to load, default is Config.ini
  --print                     send a printjob.
  --show                      launch a system image viewer.
  -o OUTPUT, --output OUTPUT  set the output location for images.
  --verbose                   enable verbose printing.
```

# Requirements
the following packages are required:
 - python3
 - selenium
 - validators
 - gecko-driver (apt install firefox-geckodriver)

install requirements with pip:
```$ pip install -r requirements.txt```

# Config
This program looks for a config file name Config.ini
if one is not present then make sure to copy ExampleConfig.ini and rename it Config.ini

## [HelloFresh]
The values in this section are search for on the webpage and taken a screenshot of.
Having these in a config file allows to edit these if they do ever change on the webpage (idem for the cookie button element).

## [Cookie]
The site shows a cookie banner this section indicates what element to click in order to just accept them.

## [LinuxPrintingOpts]
These options translate to ``lpr`` command-line options pretty much 1 to 1
they will generate the -o options for that command.
