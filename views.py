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


# global variables
app = Flask(__name__)
app.secret_key = "neo-trainingassitant-2015"


# settings
size = [
    settings.limit_upper_width,
    settings.limit_upper_height,
    settings.limit_lower_width,
    settings.limit_lower_height
]

alert = [
    settings.alert_click_clear,
    settings.alert_click_skip,
    settings.alert_click_next
]

interval = 5
if type(settings.report_dump_interval) in {int, float}:
    interval = int(settings.report_dump_interval)


# functions
def dump_report(report_path, data):
    f = open(report_path, "w")
    json_data = json.dumps(data)
    f.write(json_data)
    f.close()
    return


def load_report(report_path):
    f = open(report_path, "r")
    data = json.load(f)
    f.close()
    return data


def create_annotation(path, records):
    global root_path

    pos_f = open(os.path.join(path, "positive.dat"), "w")
    neg_f = open(os.path.join(path, "negative.dat"), "w")
    log_f = open(os.path.join(path, "log.dat"), "w")

    if not os.path.exists(path):
        os.makedirs(path)

    for item in records:
        tmp_path = os.path.join(root_path, item["path"])

        if item["type"] == "positive":
            tmp = ""
            for coord in item["coords"]:
                coord_list = [str(int(x/coord[-1])) for x in coord[:-1]]
                tmp = "  ".join([tmp, " ".join(coord_list)])

            s = "{0}  {1}{2}\n".format(
                    tmp_path, len(item["coords"]), tmp)
            pos_f.write(s)
            log_f.write(s)

        elif item["type"] == "negative":
            s = "{0}\n".format(tmp_path)
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
    global next_count
    global flag_skip
    global images
    global records

    count = -1
    imgnum = len(images)
    counter = "{0} of {1}".format(count+1, imgnum)

    # check finished
    if not flag_finished:
        if count < 0:
            if flag_skip:
                count = next_count - 1
            return render_template("index.html", imgsrc="", \
                       imgnum=imgnum, count=0, counter=counter)

        elif count < imgnum:
            imgsrc = images[count]
            return render_template("index.html", imgsrc=imgsrc, \
                       imgnum=imgnum, count=count, counter=counter)

    else:
        sys.exit(0)
        #return "Error: Please don't reload after finished."


@app.route("/_next")
def _next():
    global count
    global images
    global flag_finished
    global crop_path
    global report_path
    global size
    global alert
    global interval

    skip = request.args.get("skip")
    image_path = ""

    try:
        if count >= len(images):
            image_path = images[-1]
        else:
            image_path = images[count]
    except NameError:
        count = -1

    # check skip
    if skip == "0" and not flag_finished:
        # coords of enclosed area
        coords = request.args.get("coords")
        coords = json.loads(coords)

        # check positive or negative
        if len(coords) == 0:
            data = {
                "type": "negative",
                "path": image_path,
                "coords": []
            }
            records[count] = data

        else:
            data = {
                "type": "positive",
                "path": image_path,
                "coords": coords
            }
            records[count] = data

    elif skip == "1" and not flag_finished:
        if count >= 0:
            data = {
                "type": "negative",
                "path": image_path,
                "coords": []
            }
            records[count] = data


    # dump report
    if settings.flag_report_dump:
        if (count+1) != 0 and (count+1) % interval == 0:
            data = {
                "input_path": input_path,
                "crop_path": crop_path,
                "records": records,
                "images": images,
                "count": count + 1
            }
            dump_report(report_path, data)

    # check existance of remaining
    imgsrc = ""
    coords = []

    if count+1 < len(images):
        imgsrc = images[count+1]
        coords = records[count+1]["coords"]
    elif count+1 == len(images):
        flag_finished = True
        create_annotation(input_path, records)
        if settings.flag_save_crop:
            crop_images(crop_path, records)
        print(report_path)
        if os.path.exists(report_path):
            os.remove(report_path)


    count += 1

    return jsonify(imgsrc=imgsrc, finished=flag_finished, \
                    count=count, coords=coords, size=size, alert=alert)


@app.route("/_back")
def _back():
    global count
    global size
    global alert

    imgsrc = ""
    coords = []

    if count > 0:
        count -= 1
        imgsrc = images[count]
        coords = records[count]["coords"]

    return jsonify(imgsrc=imgsrc, finished=False, \
                    count=count, coords=coords, size=size, alert=alert)


# main function
if __name__ == "__main__":
    global flag_skip
    global flag_finished
    global next_count

    global root_path
    global report_path
    global input_path; global input_relpath;
    global crop_path;  global crop_relpath;

    global images
    global records

    # variables
    records = []
    flag_skip = False
    flag_finished = False

    # file path
    try:
        script_path = os.path.realpath(__file__)
    except:
        script_path = os.path.realpath('__file__')

    root_path   = os.path.dirname(script_path)
    report_path = os.path.join(root_path, "report.json")
    input_path  = ""; input_relpath = ""
    crop_path   = ""; crop_relpath  = ""

    # parsing of argument
    desc_str = "This program for creation of OpenCV annotation data."
    parser = argparse.ArgumentParser(description=desc_str)
    parser.add_argument("-d", "--imgpath",  help="Path of input directory")
    parser.add_argument("-s", "--croppath", help="Path of output directory")

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

    if not os.path.exists(input_path):
        print("Error: Input path not found.")
        sys.exit(1)

    input_relpath = os.path.relpath(input_path, root_path)
    crop_relpath  = os.path.relpath(crop_path,  root_path)


    # preparation of images
    images = [os.path.join(input_relpath, x)
                for x in sorted(os.listdir(input_relpath))
                if x.split(".")[-1]
                in {"jpg","jpeg","png","bmp","gif"}]

    if not len(images) > 0:
        sys.exit("Error: Images not found.")
    else:
        records = [{
            "input_path": "",
            "crop_path": "",
            "coords": []
        }] * len(images)


    # load report data
    if os.path.exists(report_path):
        data = load_report(report_path)
        input_path = data["input_path"]
        crop_path  = data["crop_path"]
        records    = data["records"]
        images     = data["images"]
        next_count = data["count"]
        flag_skip = True

    # show path
    print("\nInput image Path : {0}".format(os.path.abspath(input_path)))
    print("Annotation file Path : {0}".format(os.path.abspath(input_path)))
    if settings.flag_save_crop:
        print("Cropped Image Path : {0}\n".format(os.path.abspath(crop_path)))

    # run flask
    app.run(
        debug=True,
        use_reloader=False,
    )


