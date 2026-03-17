from flask import Flask, render_template, request
from modules.browser_history import get_browser_history
from modules.usb_tracker import get_usb_devices
from modules.file_hasher import hash_file
from modules.deleted_recovery import recover_deleted
from modules.timeline import get_timeline
from modules.report_generator import generate_report
from datetime import datetime
import webbrowser

app = Flask(__name__)

# current time function
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

    hashes = hash_file("history_copy.db")

    md5 = hashes["md5"]
    sha256 = hashes["sha256"]

    return f"""
    MD5 Hash : {md5} <br>
    SHA256 Hash : {sha256} <br>
    Time : {get_time()}
    """


@app.route("/deleted")
def deleted():
    files = recover_deleted()
    return f"Deleted Files: {files} | Time: {get_time()}"


@app.route("/timeline")
def timeline():
    data = get_timeline("data")
    return render_template("timeline.html", data=data, time=get_time())


@app.route("/report", methods=["GET", "POST"])
def report():

    if request.method == "POST":

        case_id = request.form["case_id"]
        case_name = request.form["case_name"]
        investigator = request.form["investigator"]

        browser_data = get_browser_history()
        usb_data = get_usb_devices()
        timeline_data = get_timeline("data")

        hashes = hash_file("history_copy.db")
        md5 = hashes["md5"]
        sha256 = hashes["sha256"]

        file = generate_report(
            browser_data,
            usb_data,
            timeline_data,
            case_id,
            case_name,
            investigator,
            md5,
            sha256
        )

        return f"""
        Report Generated Successfully <br><br>

        Case ID : {case_id} <br>
        Case Name : {case_name} <br>
        Investigator : {investigator} <br><br>

        MD5 Hash : {md5} <br>
        SHA256 Hash : {sha256} <br><br>

        File : {file} <br>
        Time : {get_time()}
        """

    return render_template("report_form.html", time=get_time())


if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:5000")
    app.run(debug=True)