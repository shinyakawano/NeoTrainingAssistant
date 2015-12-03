#!/usr/bin/python3

# get cropped images
flag_save_crop = True

# report dump for unintended interruption
flag_report_dump = True
report_dump_interval = 5

# after create annotation, remove src images
flag_remove_src = False

# crop ratio (width / height)
# if you want make ratio free, set 0
# or you want square, set 1
aspect_ratio = 0

# image-size limit in main window
limit_upper_width  = 800
limit_upper_height = 600
limit_lower_width  = 500
limit_lower_height = 375

# button alert
alert_click_clear = True    # when push 'Clear'
alert_click_skip  = False   # when push 'Skip'
alert_click_next  = False   # when push 'Next'
