from flask import Flask, render_template, request, send_file
from modules.browser_history import get_browser_history
from modules.file_hasher import hash_file
from modules.deleted_recovery import recover_deleted
from modules.timeline import create_timeline
from modules.report_generator import generate_report
from datetime import datetime
import platform
import webbrowser
import threading

app = Flask(__name__)


# Safe USB import (Windows/Linux)
if platform.system() == "Windows":
    try:
        from modules.usb_tracker import get_usb_devices
    except Exception:
        def get_usb_devices():
            return [{"Device Name": "Error", "Friendly Name": "USB module error", "Checked Time": "-"}]
else:
    def get_usb_devices():
        return [{"Device Name": "Not Supported", "Friendly Name": "USB works only on Windows", "Checked Time": "-"}]


def get_time():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


@app.route("/")
def home():
    return render_template("index.html", time=get_time())


@app.route("/browser")
def browser():
    data = get_browser_history()
    return render_template("browser.html", data=data, time=get_time())


@app.route("/usb")
def usb():
    data = get_usb_devices()
    return render_template("usb.html", data=data, time=get_time())


@app.route("/hash")
def hash_page():
    try:
        hashes = hash_file("history_temp.db")

        return f"""
        <h2>File Hash Result</h2>
        MD5 : {hashes['md5']} <br><br>
        SHA256 : {hashes['sha256']} <br><br>
        Time : {get_time()}
        """
    except Exception:
        return f"""
        <h2>Error</h2>
        history_temp.db file not found<br><br>
        Please open Browser History page first.<br><br>
        Time : {get_time()}
        """


@app.route("/deleted")
def deleted():
    files = recover_deleted()
    return render_template("deleted.html", files=files, time=get_time())


@app.route("/timeline")
def timeline():
    data = create_timeline()
    return render_template("timeline.html", data=data, time=get_time())


@app.route("/report", methods=["GET", "POST"])
def report():
    if request.method == "POST":
        try:
            case_id = request.form["case_id"]
            case_name = request.form["case_name"]
            investigator = request.form["investigator"]

            browser_data = get_browser_history()
            usb_data = get_usb_devices()
            timeline_data = create_timeline()

            try:
                hashes = hash_file("history_temp.db")
                md5 = hashes["md5"]
                sha256 = hashes["sha256"]
            except Exception:
                md5 = "Not Available"
                sha256 = "Not Available"

            file_path = generate_report(
                browser_data,
                usb_data,
                timeline_data,
                case_id,
                case_name,
                investigator,
                md5,
                sha256
            )

            return send_file(file_path, as_attachment=True)

        except Exception as e:
            return f"""
            <h2>Report Generation Failed</h2>
            Error: {str(e)} <br><br>
            Time : {get_time()}
            """

    return render_template("report_form.html", time=get_time())


def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)