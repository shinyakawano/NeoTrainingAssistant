#!/usr/bin/python3

# modules
import os
import re
import sys
import json
import shutil
import settings
import argparse
from flask import *
from PIL import Image
from datetime import datetime


# global variables
app = Flask(__name__)
app.secret_key = "neo-trainingassitant-2015"

ttime = datetime.now()
datestr = ttime.strftime("%Y%m%d%H%M%S")


# settings
config = {
    "aspect_ratio"        : settings.aspect_ratio,
    "limit_upper_width"   : settings.limit_upper_width,
    "limit_upper_height"  : settings.limit_upper_height,
    "limit_lower_width"   : settings.limit_lower_width,
    "limit_lower_height"  : settings.limit_lower_height,
    "alert_click_clear"   : settings.alert_click_clear,
    "alert_click_overall" : settings.alert_click_overall,
    "alert_click_skip"    : settings.alert_click_skip,
    "alert_click_next"    : settings.alert_click_next
}

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


def crop_image(src, dst, coord):
    coord = [int(x/coord[-1]) for x in coord[:-1]]
    img = Image.open(src)

    x = coord[0]
    y = coord[1]
    w = x + coord[2]
    h = y + coord[3]

    img.crop((x, y, w, h)).save(dst)
    return


def create_annotation(path, records):
    global root_path
    global copy_relpath

    pos_f = open(os.path.join(path, "positive.dat"), "w")
    neg_f = open(os.path.join(path, "negative.dat"), "w")
    log_f = open(os.path.join(path, "log.dat"), "w")

    if not os.path.exists(path):
        os.makedirs(path)

    for item in records:
        fname = os.path.basename(item["path"])
        tmp_path = os.path.join(copy_relpath, fname)

        if item["type"] == "positive":
            tmp = ""
            for i, coord in enumerate(item["coords"]):
                if settings.flag_save_crop:
                    root, ext = os.path.splitext(tmp_path)
                    fname = "{0}_{1}{2}".format(os.path.basename(root), i+1, ext)
                    dst = os.path.join(crop_path, fname)
                    crop_image(item["path"], dst, coord)

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
        if os.path.exists(report_path):
            os.remove(report_path)

        return "Error: Please don't reload after finished."
        #sys.exit(0)


@app.route("/_next")
def _next():
    global count
    global images
    global flag_finished
    global dst_path
    global crop_path
    global copy_path; copy_relpath
    global report_path
    global config
    global interval

    skip = request.args.get("skip")
    img_path = ""

    try:
        if count >= len(images):
            img_path = images[-1]
        else:
            img_path = images[count]
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
                "type"   : "negative",
                "path"   : img_path,
                "coords" : []
            }
            records[count] = data

        else:
            data = {
                "type"   : "positive",
                "path"   : img_path,
                "coords" : coords
            }
            records[count] = data

    elif skip == "1" and not flag_finished:
        if count >= 0:
            data = {
                "type"   : "negative",
                "path"   : img_path,
                "coords" : []
            }
            records[count] = data


    # dump report
    if settings.flag_report_dump:
        if (count+1) != 0 and (count+1) % interval == 0:
            data = {
                "src_path"  : src_path,
                "dst_path"  : dst_path,
                "crop_path" : crop_path,
                "copy_path" : copy_path,
                "records"   : records,
                "images"    : images,
                "count"     : count + 1
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

        if not os.path.exists(dst_path):
            os.makedirs(dst_path)

        if not os.path.exists(copy_path):
            shutil.copytree(src_path, copy_path)
            if settings.flag_remove_src:
                shutil.rmtree(src_path)
                os.makedirs(src_path)

        if not os.path.exists(crop_path):
            os.makedirs(crop_path)

        create_annotation(dst_path, records)

        if os.path.exists(report_path):
            os.remove(report_path)

    count += 1

    return jsonify(imgsrc=imgsrc, finished=flag_finished, \
                    count=count, coords=coords, config=config)


@app.route("/_back")
def _back():
    global count
    global config

    imgsrc = ""
    coords = []

    if count > 0:
        count -= 1
        imgsrc = images[count]
        coords = records[count]["coords"]

    return jsonify(imgsrc=imgsrc, finished=False, \
                    count=count, coords=coords, config=config)


# main function
if __name__ == "__main__":
    global flag_skip
    global flag_finished
    global next_count

    global root_path
    global report_path
    global src_path;  global src_relpath
    global dst_path;  global dst_relpath
    global crop_path
    global copy_path; global copy_relpath

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
    src_path  = "";  src_relpath  = ""
    dst_path  = "";  dst_relpath  = ""
    crop_path = ""
    copy_path = ""

    # parsing of argument
    desc_str = "This program for creation of OpenCV annotation data."
    parser = argparse.ArgumentParser(description=desc_str)
    parser.add_argument("-s", "--srcpath", help="Path of input directory")
    parser.add_argument("-d", "--dstpath", help="Path of output directory")

    args = parser.parse_args()
    if args.srcpath is None:
        src_path = os.path.join(root_path, "static/img")
    else:
        src_path = os.path.join(os.getcwd(), args.srcpath)
        src_path = os.path.abspath(src_path)

    if args.dstpath is None:
        head, tail = os.path.split(src_path)
        dst_path  = os.path.join(head, "{0}_dst/{1}".format(tail, datestr))
    else:
        dst_path = os.path.join(os.getcwd(), args.dstpath)
        dst_path = os.path.abspath(dst_path)

    crop_path = os.path.join(dst_path, "{0}_crop".format(tail))
    copy_path = os.path.join(dst_path, "img")

    if not os.path.exists(src_path):
        print("Error: Input path not found.")
        sys.exit(1)

    src_relpath  = os.path.relpath(src_path, root_path)
    dst_relpath  = os.path.relpath(dst_path, root_path)
    copy_relpath = os.path.relpath(copy_path, dst_path)


    # preparation of images
    images = [os.path.join(src_relpath, x)
                for x in sorted(os.listdir(src_relpath))
                if x.split(".")[-1]
                in {"jpg","jpeg","png","bmp","gif"}]

    if not len(images) > 0:
        sys.exit("Error: Images not found.")
    else:
        records = [{
            "type"   : "",
            "path"   : "",
            "coords" : []
        }] * len(images)


    # load report data
    if os.path.exists(report_path):
        data = load_report(report_path)
        if data["count"] < len(images):
            src_path   = data["src_path"]
            dst_path   = data["dst_path"]
            crop_path  = data["crop_path"]
            copy_path  = data["copy_path"]
            records    = data["records"]
            images     = data["images"]
            next_count = data["count"]
            flag_skip  = True
        else:
            os.remove(report_path)


    # show path
    print("\nSource Path : {0}".format(os.path.abspath(src_path)))
    print("Destination Path : {0}".format(os.path.abspath(dst_path)))
    if settings.flag_save_crop:
        print("Cropped image Path : {0}".format(os.path.abspath(crop_path)))
    print()

    # run flask
    app.run(
        debug=True,
        use_reloader=False,
    )


