from flask import Flask, render_template
import os
import json
import socket

app = Flask(__name__)

def get_ip_address():
    try:
        hostname = socket.gethostname()
        ip_address = socket.getaddrinfo(hostname, None, family=socket.AF_INET)[0][-1][0]
        return ip_address
    except:
        return "Unable to get IP address"


@app.route('/')
def view_log():
    log_file = 'log.json'
    log_data = []

    if os.path.exists(log_file):
        with open(log_file, 'r') as file:
            log_data = json.load(file)

    return render_template('log.html', log_data=log_data)

if __name__ == "__main__":
    ip_address = get_ip_address()
    print(f"Raspberry Pi IP address: {ip_address}")
    app.run(debug=True, host='0.0.0.0')
