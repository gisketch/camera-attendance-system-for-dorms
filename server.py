from flask import Flask, render_template
import os
import json

app = Flask(__name__)

@app.route('/')
def view_log():
    log_file = 'log.json'
    log_data = []

    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            log_data = json.load(file)

    return render_template('log.html', log_data=log_data)

if __name__ == "__main__":
    app.run(debug=True)
