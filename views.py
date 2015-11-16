#!/usr/bin/python3

# modules
import os
import re
import sys
import json
import settings
import argparse
from flask import *
from PIL import Image


# flask
app = Flask(__name__)
app.secret_key = "neo-trainingassitant-2015"


# global variables
try:
    script_path = os.path.realpath(__file__)
except:
    script_path = os.path.realpath('__file__')

root_path   = os.path.dirname(script_path)
report_path = os.path.join(root_path, "report.json")
input_path  = ""
crop_path   = ""

count = -1
records = []
flag_finished = False
flag_skip = False


# report dump interval
interval = 5
if type(settings.report_dump_interval) in {int, float}:
    interval = int(settings.report_dump_interval)


# report check
if os.path.exists(report_path):
    flag_skip = True


# parsing of argument
desc_str = "This program for creation of OpenCV annotation data."
parser = argparse.ArgumentParser(description=desc_str)
parser.add_argument("-d", "--imgpath",  help="Path of input directory")
parser.add_argument("-s", "--croppath", help="Path of output directory")

if not flag_skip:
    args = parser.parse_args()

    if args.imgpath is None:
        input_path = os.path.join(root_path, "static/img")
    else:
        input_path = os.path.join(os.getcwd(), args.imgpath)
        input_path = os.path.abspath(input_path)

    if args.croppath is None:
        head, tail  = os.path.split(input_path)
        crop_path = os.path.join(head, "{0}_crop".format(tail))
    else:
        crop_path = os.path.join(os.getcwd(), args.croppath)
        crop_path = os.path.abspath(crop_path)

    input_path = os.path.relpath(input_path, os.getcwd())
    crop_path  = os.path.relpath(crop_path,  os.getcwd())

    if ".." in input_path:
        print("Error: Input path can't be out of " + \
              "Neo Training Assistant directory.")
        sys.exit(1)

    if not os.path.exists(input_path):
        print("Error: Input path not found.")
        sys.exit(1)


# preparation of images
image_dir = input_path
images = [os.path.join(image_dir, x)
            for x in sorted(os.listdir(image_dir))
            if x.split(".")[-1]
            in {"jpg","jpeg","png","bmp","gif"}]

if not len(images) > 0:
    sys.exit("Error: Images not found.")
else:
    records = []



# functions
def dump_report(report_path, records):
    global input_path
    global crop_path

    f = open(report_path, "w")
    data = {
        "input_path": input_path,
        "crop_path": crop_path,
        "records": records
    }
    json_data = json.dumps(data)
    f.write(json_data)
    f.close()

    return


def load_report(report_path):
    global input_path
    global crop_path
    global records

    f = open(report_path, "r")
    data = json.load(f)

    input_path = data["input_path"]
    crop_path  = data["crop_path"]
    records    = data["records"]
    f.close()


def create_annotation(path, records):
    pos_f = open(os.path.join(path, "positive.dat"), "w")
    neg_f = open(os.path.join(path, "negative.dat"), "w")
    log_f = open(os.path.join(path, "log.dat"), "w")

    if not os.path.exists(path):
        os.makedirs(path)

    for item in records:
        if item["type"] == "positive":
            tmp = ""
            for coord in item["coords"]:
                coord_list = [str(int(x/coord[-1])) for x in coord[:-1]]
                tmp = "  ".join([tmp, " ".join(coord_list)])

            s = "{0}  {1}{2}\n".format(
                item["path"], len(item["coords"]), tmp)
            pos_f.write(s)
            log_f.write(s)

        elif item["type"] == "negative":
            s = "{0}\n".format(item["path"])
            neg_f.write(s)
            log_f.write(s)

    pos_f.close()
    neg_f.close()
    log_f.close()

    return


def crop_images(path, records):
    if not os.path.exists(path):
        os.makedirs(path)

    for item in records:
        if item["type"] == "positve":
            print(item)

    return



# flask views
@app.route("/")
def index():
    global count
    global interval
    global images
    global records
    global report_path

    imgnum = len(images)
    counter = "{0} of {1}".format(count+1, imgnum)

    if settings.flag_report_dump:
        if count > 0 and count % interval == 0:
            report_dump(report_path, records)

    # check finished
    if not flag_finished:
        if count < 0:
            return render_template("index.html", imgsrc="", \
                       imgnum=imgnum, count=0, counter=counter)

        elif count < imgnum:
            imgsrc = images[count]
            return render_template("index.html", imgsrc=imgsrc, \
                       imgnum=imgnum, count=count, counter=counter)

    else:
        return "Error: Please don't reload after finished."


@app.route("/_next")
def _next():
    # variables
    global count
    global images
    global flag_finished
    global crop_path

    # check whether skip image
    skip = request.args.get("skip")
    image_path = images[count]


    if skip == "0" and not flag_finished:
        # coords of enclosed area
        coords = request.args.get("coords")
        coords = json.loads(coords)

        # check positive or negative
        if len(coords) == 0:
            if count > 0:
                data = {
                    "type": "negative",
                    "path": image_path,
                }
                records.append(data)

        else:
            data = {
                "type": "positive",
                "path": image_path,
                "coords": coords
            }
            records.append(data)

    elif skip == "1" and not flag_finished:
        data = {
            "type": "negative",
            "path": image_path,
        }
        records.append(data)


    # check existance of remaining
    imgsrc = ""
    if count+1 < len(images):
        imgsrc = images[count+1]
    else:
        flag_finished = True
        create_annotation(input_path, records)
        if settings.flag_save_crop:
            crop_images(crop_path, records)

    count += 1

    # load report data
    if count == 0 and os.path.exists(report_path):
        load_report(report_path)
        count  = len(records)
        imgsrc = records[count-1]["path"]

    return jsonify(imgsrc=imgsrc, finished=flag_finished, count=count)



# main function
if __name__ == "__main__":

    # show path
    print("\nInput image Path : {0}".format(os.path.abspath(input_path)))
    print("Annotation file Path : {0}".format(os.path.abspath(input_path)))
    if settings.flag_save_crop:
        print("Cropped Image Path : {0}\n".format(os.path.abspath(crop_path)))

    # run flask
    app.run(debug=True, use_reloader=False)


