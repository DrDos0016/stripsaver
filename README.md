# Stripsaver

A tool to save comics created on [stripcreator](http://www.stripcreator.com)
as PNG images.

## Features

* Download individual comics or complete accounts
* Save comic information as JSON
* Obscenity filter toggle

## Usage

````
python3 stripsaver.py [-d] [-g] source
````

### positional arguments:

**source** URL of individual comic or account page

### optional arguments:

**-d, --details** : Save detailed comic information as JSON data

**-g, --g-rated** : Turn on Stripcreator's obscenity filter

## Issues and Incomplete Features

* Account downloading not yet implemented
* Silent characters get empty word balloons
* No support for panel narrations
* Panels do not stretch to accomodate very tall/wide word balloons
* Drop-in font replacement
* Still several issues with word balloon placement
