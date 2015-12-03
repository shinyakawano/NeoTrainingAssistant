## About this repository

This repository is fork of http://github.com/shkh/TrainingAssistant.git

NeoTrainingAssistant is a tool to create annotation data for OpenCV, and to crop images.


## How to Install

1. Clone repository:

		% git clone git@github.com:furaibo/NeoTrainingAssistant.git

2. Add Jcrop:

		% cd NeoTrainingAssistant
		% git submodule init
		% git submodule update
		% cd static/Jcrop
		% git checkout master

3. Install python modules via pip3

		% sudo pip3 install -r freezed.txt


## How to use

1. Add images to `static/img`

2. Run server

		% python3 views.py

This command starts the Flask server on port 5000, and please access `http://localhost:5000` with browser.

![リス可愛い](http://farm9.staticflickr.com/8334/8131692997_6cd40c380a_z.jpg)

3. Get data
After all images will be processed, you will get `positive.txt`, `negative.txt` and crop images in `static/img_dst/[%DATETIME%]`;

