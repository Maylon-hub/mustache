from flask import Blueprint, render_template, url_for, current_app as app
from collections import OrderedDict
import os
import operator
import json
import glob

home = Blueprint('home', __name__)


def get_datasets():
    root = app.config['WORKSPACE']
    datasets = {}

    dirlist = [item for item in os.listdir(
        root) if os.path.isdir(os.path.join(root, item))]

    for dir in dirlist:

        file = glob.glob(os.path.join(
            os.path.join(root, dir), "settings"))[0]

        file2 = glob.glob(os.path.join(
            os.path.join(root, dir), "progress.json"))[0]

        with open(file) as f:
            data = json.load(f)

        with open(file2) as f:
            progress = json.load(f)

        if progress['stage'] == 'meta-clustering' and progress['state']['current'] == 1:
            data['state'] = {'stage': 'done', 'message': '',
                             'state': {'current': 1, 'end': 1}}
        else:
            data['state'] = progress

        datasets[dir] = data

    return OrderedDict(sorted(datasets.items(), key=lambda x: float(x[1]['date_added']), reverse=True))


@home.route('/')
def index():
    try:
        if app.config['WORKSPACE']:
            datasets = get_datasets()
        else:
            datasets = {}
    except Exception as e:
        print(e)
        datasets = {}
    return render_template("home/index.html", datasets=datasets)
