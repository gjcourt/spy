#!/usr/bin/env python
from flask import Flask
from flask import render_template
from spy import parse_status
app = Flask(__name__)
app = Flask(__name__, template_folder='/usr/local/spy/templates')


@app.route("/")
def monitor():
    return render_template('monitor.html', items=map(dict, parse_status()))

def run():
    app.run()

