#!/usr/bin/python3

# modules
import os
import re
import sys
import json
import settings
import argparse
from flask import *

# flask
app = Flask(__name__)
app.secret_key = "neo-trainingassitant-2015"

# variables
count = -1
flag_finished = False

# data file for positive and negative
pos_f = open("positive.dat", "a")
neg_f = open("negative.dat", "a")
log_f = open("log.dat", "w")

# preparation of images
image_dir = os.path.join("static", "img")
images = [x for x in os.listdir(image_dir) \
            if x.split(".")[-1] \
            in {"jpg","jpeg","png","bmp","gif"}]

if not len(images) > 0:
    sys.exit("Error: Could not find images")


@app.route("/")
def index():
    # variables
    global count
    global images
    imgnum = len(images)
    counter = "{0} of {1}".format(count+1, imgnum)

    # check finished
    if not flag_finished:
        if count < 0:
            return render_template("index.html", \
                               imgnum=imgnum, count=0, counter=counter)
        elif count < imgnum:
            imgsrc  = os.path.join(image_dir, images[count])
            return render_template("index.html", imgsrc=imgsrc, \
                               imgnum=imgnum, count=count, counter=counter)
    else:
        return "Error : Please don't reload after finished."


@app.route("/_next")
def _next():
    # variables
    global count
    global images
    global pos_f, neg_f, log_f
    global flag_finished

    # check whether skip image
    skip = request.args.get("skip")

    if skip == "0":
        # coords of enclosed area
        coords = request.args.get("coords")
        coords = json.loads(coords)

        # path of current image
        image_path = os.path.join(image_dir, images[count])

        # check positive or negative
        if len(coords) == 0:
            s = "{0}\n".format(image_path)
            neg_f.write(s)
            log_f.write(s)
        else:
            tmp = ""
            for coord in coords:
                tmp = "  ".join([tmp, " ".join([str(int(x)) for x in coord])])
            s = "{0}  {1}{2}\n".format(image_path, len(coords), tmp)
            pos_f.write(s)

        log_f.flush()

    # check existance of remaining
    imgsrc = ""

    if count+1 < len(images):
        imgsrc = os.path.join(image_dir, images[count+1])
    else:
        flag_finished = True
        pos_f.close()
        neg_f.close()
        log_f.close()

    count += 1
    return jsonify(imgsrc=imgsrc, finished=flag_finished, count=count)


# main function
if __name__ == "__main__":
    # run flask
    app.debug = True
    app.run()

