# -*- coding: utf-8 -*-
"""
    Flaskr
    ~~~~~~

    A microblog example application written as Flask tutorial with
    Flask and sqlite3.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import requests
from sqlite3 import dbapi2 as sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify
import time
import datetime

# create our little application :)
from flask import json

app = Flask(__name__)

# Load default config and override config from an environment variable
app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flaskr.db'),
    DEBUG=True,
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)


def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def init_db():
    """ Thực hiện tạo database."""
    db = get_db()
    with app.open_resource('schema.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


@app.route('/')
def show_entries():
    db = get_db()
    cur = db.execute('SELECT title, text FROM entries ORDER BY id DESC')
    entries = cur.fetchall()
    return render_template('show_entries.html', entries=entries)


@app.route('/add', methods=['POST'])
def add_entry():
    if not session.get('logged_in'):
        abort(401)
    db = get_db()
    db.execute('INSERT INTO entries (title, text) VALUES (?, ?)',
               [request.form['title'], request.form['text']])
    db.commit()
    flash('New entry was successfully posted')
    return redirect(url_for('show_entries'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in')
            return redirect(url_for('show_entries'))
    return render_template('login.html', error=error)


@app.route('/visualize', methods=['GET', 'POST'])
def visualize():
    error = None
    # if request.method == 'POST':
    #     if request.form['username'] != app.config['USERNAME']:
    #         error = 'Invalid username'
    #     elif request.form['password'] != app.config['PASSWORD']:
    #         error = 'Invalid password'
    #     else:
    #         session['logged_in'] = True
    #         flash('You were logged in')
    #         return redirect(url_for('show_entries'))


    # respond = requests.post("https://lbasense-hust.appspot.com/data", data={},
    #                         headers={'type': 'StatsSummary', 'user': 'student-hust', 'pass': '123456a@', 'region': '1',
    #                                  'startTime': '2016-10-02T00:00:00', 'endTime': '2016-10-06T00:00:00',
    #                                  'resolution': 'days'})
    # print (respond.content)
    # return render_template('show_visualize.html', data=respond.content)


    return render_template('show_visualize.html')


@app.route('/multiline', methods=['GET', 'POST'])
def multiline():
    return render_template('show_multi_line.html')


# Hàm ajax nhận request hiển thị đồ thị
# Dữ liệu trả về {data=data,resolution=resolution,region=region}


@app.route("/ajax", methods=['POST'])
def ajax():
    # respond = requests.post("https://lbasense-hust.appspot.com/data", data={},
    #                         headers={'type': 'StatsSummary', 'user': 'student-hust', 'pass': '123456a@', 'region': '1',
    #                                  'startTime': '2016-09-20T00:00:00', 'endTime': '2016-11-06T00:00:00',
    #                                  'resolution': 'days'})

    # Chuẩn hóa lại startTime
    startTime = request.json['startTime'];
    d = datetime.datetime.strptime(startTime, "%d/%m/%Y %H:%M:%S")
    startTime = d.strftime("%Y-%m-%dT%H:%M:%S")

    # Chuẩn hóa lại endTime
    endTime = request.json['endTime'];
    d = datetime.datetime.strptime(endTime, "%d/%m/%Y %H:%M:%S")
    endTime = d.strftime("%Y-%m-%dT%H:%M:%S")

    # Kiểu lấy dữ liệu : visits hoặc là returrn
    charType = request.json['charType']

    # Kiểu hiển thị days hoặc hourse
    resolution = request.json['resolution'];

    # Region cần lấy số liệu:
    # 00 là tất cả
    # 01, 02, 03, 04 theo thứ tự region HUST1. HUST2. HUST3. HUST4.
    region = request.json['region'];

    print "START_TIME" + startTime
    print "end_TIME" + startTime
    print "resolution" + resolution
    print "region" + region
    print "charType" + charType
    if region != "0":
        reponds = requests.post("https://lbasense-hust.appspot.com/data", data={},
                                headers={'type': 'StatsSummary',
                                         'user': 'student-hust',
                                         'pass': '123456a@',
                                         'region': region,
                                         'startTime': startTime,
                                         'endTime': endTime,
                                         'resolution': resolution})
        result = jsonify(data=reponds.content, resolution=resolution, region=region, charType=charType)
        return result
    else:  # Chọn hiển thị tất cả
        # Lấy số lượng region
        infoRegions = requests.post("https://lbasense-hust.appspot.com/data", data={},
                                    headers={'type': 'RegionNames', 'user': 'student-hust',
                                             'pass': '123456a@'}).content
        print infoRegions;

        inforRegionJson = json.loads(infoRegions).keys();
        print infoRegions
        numberRegion = len(inforRegionJson);
        print "NUMBERREGION" + str(numberRegion)
        # Lần lượt request theo region lấy số liệu
        array_total = []
        for i in range(len(inforRegionJson)):
            reponds = requests.post("https://lbasense-hust.appspot.com/data", data={},
                                    headers={'type': 'StatsSummary',
                                             'user': 'student-hust',
                                             'pass': '123456a@',
                                             'region': inforRegionJson[i],
                                             'startTime': startTime,
                                             'endTime': endTime,
                                             'resolution': resolution})
            array_total.append(json.loads(reponds.content)['summaryStats'])

        data = process(array_total, charType)
        result = jsonify(data=data, resolution=resolution, region=region, charType=charType)
        return result


def process(array_total, charType):
    array_date = []
    indexs = []
    for i in range(len(array_total)):
        indexs.append(0)

    while True:
        dates = []

        countFinish = 0;
        teampDates = []
        for i in range(len(indexs)):
            if indexs[i] >= len(array_total[i]):
                countFinish = countFinish + 1;

        if countFinish == len(indexs):
            break;

        for i in range(len(indexs)):
            if indexs[i] < len(array_total[i]):
                date = array_total[i][indexs[i]]['date']
                dates.append(date)
                teampDates.append(date)
            else:
                teampDates.append("")

        minDate = min(dates)
        added = False
        for i in range(0, len(indexs)):
            if teampDates[i] == minDate:
                indexs[i] = indexs[i] + 1;
                if not added:
                    added = True
                    array_date.append(minDate)

    print array_date
    # result = "["
    result = ""
    # Vơí mỗi ngày
    for i in range(len(array_date)):
        dateEach = array_date[i]
        result += '{"date":' + '"' + dateEach + '",'
        # Tìm kiếm trong danh sách mảng
        for j in range(len(array_total)):
            value = ""
            isExist = False
            # Trong mảng của mỗi phẩn tử
            for k in range(len(array_total[j])):
                if (array_total[j][k]['date'] == dateEach):
                    value = '"0' + str(j) + '":"' + str(array_total[j][k][charType]) + '",'
                    isExist = True
                    break;

            if isExist:
                result += value;
            else:
                result += '"0' + str(j) + '":' + '"0",'

        # Xóa dấu , ở cuối cùng
        potision = result.rfind(",")
        result = list(result)

        result[potision] = ''
        result = ''.join(result)

        result += "},"
    # result += "]"
    potision = result.rfind(",")
    result = list(result)

    result[potision] = ''
    result = ''.join(result)

    print result
    return result


#
# @app.route("/ajax_multi", methods=['POST'])
# def ajax_multi():
#     # respond = requests.post("https://lbasense-hust.appspot.com/data", data={},
#     #                         headers={'type': 'StatsSummary', 'user': 'student-hust', 'pass': '123456a@', 'region': '1',
#     #                                  'startTime': '2016-09-20T00:00:00', 'endTime': '2016-11-06T00:00:00',
#     #                                  'resolution': 'days'})
#
#     startTime = request.json['startTime'];
#     d = datetime.datetime.strptime(startTime, "%d/%m/%Y %H:%M:%S")
#     startTime = d.strftime("%Y-%m-%dT%H:%M:%S")
#
#     endTime = request.json['endTime'];
#     d = datetime.datetime.strptime(endTime, "%d/%m/%Y %H:%M:%S")
#     endTime = d.strftime("%Y-%m-%dT%H:%M:%S")
#
#     resolution = request.json['resolution'];
#     region1 = requests.post("https://lbasense-hust.appspot.com/data", data={},
#                             headers={'type': 'StatsSummary', 'user': 'student-hust', 'pass': '123456a@', 'region': '1',
#                                      'startTime': startTime, 'endTime': endTime,
#                                      'resolution': resolution})
#
#     region2 = requests.post("https://lbasense-hust.appspot.com/data", data={},
#                             headers={'type': 'StatsSummary', 'user': 'student-hust', 'pass': '123456a@', 'region': '2',
#                                      'startTime': startTime, 'endTime': endTime,
#                                      'resolution': resolution})
#
#     array = [json.loads(region1)['summaryStats'], json.loads(region2)['summaryStats']]
#
#     result = "{["
#     regionFirst = []
#     for i in range(0, len(region1)):
#         result += '{"date:"' + '"' + region1[i]['date'] + '",'
#         for j in range(0, len(array)):
#             result += '"' + j + '":' + array[j][i]['']
#
#         "{" + regionFirst['summaryStats']['datetime']
#
#     #

# respond = requests.post("https://lbasense-hust.appspot.com/data", data={},
#                         headers={'type': 'StatsSummary', 'user': 'student-hust', 'pass': '123456a@', 'region': '1',
#                                  'startTime': '2016-09-20T00:00:00', 'endTime': '2016-10-10T00:00:00',
#                                  'resolution': 'hours'})
# print "START_TIME:" + startTime;
# print "START_TIME:" + endTime;
# print "START_TIME:" + resolution;
# data = "data"
# result = jsonify(region1=region1.content, region2=region2.content, resolution=resolution)
# return result


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out')
    return redirect(url_for('show_entries'))
