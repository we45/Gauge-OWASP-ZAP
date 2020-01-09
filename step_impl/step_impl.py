from getgauge.python import step, before_scenario, Messages, data_store
from zapv2 import ZAPv2 as ZAP
import subprocess
import os
import requests
from time import sleep
import datetime

zap_proxy = {"http": "http://127.0.0.1:8090", "https": "http://127.0.0.1:8090"}
zap = ZAP(proxies=zap_proxy)

# --------------------------
# Gauge step implementations
# --------------------------


@step("Start ZAP and Open URL <target_url>")
def zap_open_url(target_url):
    cmd = "/Applications/ZAP_28.app/Contents/Java/zap.sh -config api.disablekey=true -port {0}".format(
        8090
    )
    subprocess.Popen(cmd.split(" "), stdout=open(os.devnull, "w"))
    while True:
        try:
            status_req = requests.get("http://127.0.0.1:8090")
            if status_req.status_code == 200:
                break
        except Exception:
            pass
    zap.urlopen(target_url)
    sleep(3)


@step("Run spider against target <target_url>")
def zap_spider_target(target_url):
    spider_id = zap.spider.scan(target_url)
    data_store.spec.spider_id = spider_id


@step("Get spider status")
def spider_status():
    while int(zap.spider.status(data_store.spec["spider_id"])) < 100:
        print(
            "Spider running at {}%".format(
                int(zap.spider.status(data_store.spec["spider_id"]))
            )
        )
        sleep(5)


@step("Start Active Scan against <target_url>")
def zap_active_scan(target_url):
    scan_id = zap.ascan.scan(target_url, scanpolicyname="Light")
    data_store.spec.scan_id = scan_id
    sleep(4)


@step("Get Active Scan status")
def ascan_status():
    while int(zap.ascan.status(data_store.spec["scan_id"])) < 100:
        print(
            "Active Scan running at {}%".format(
                int(zap.ascan.status(data_store.spec["scan_id"]))
            )
        )
        sleep(5)


@step("Shutdown ZAP")
def stop_zap():
    zap.core.shutdown()


@step("Export ZAP Report for <app_name> in <format> format with <filename> for <company_name> with <report_title>")
def export_zap_report(app_name, format, filename, company_name, report_title):
    url = "http://127.0.0.1:8090/JSON/exportreport/action/generate/"
    report_time = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")
    source_info = "{0};{1};ZAP Team;{2};{3};v1;v1;{4}".format(
        report_title, "Author", report_time, report_time, report_title
    )
    alert_severity = "t;t;t;t"  # High;Medium;Low;Info
    alert_details = "t;t;t;t;t;t;t;t;t;t"  # CWEID;#WASCID;Description;Other Info;Solution;Reference;Request Header;Response Header;Request Body;Response Body
    data = {
        "absolutePath": filename,
        "fileExtension": format,
        "sourceDetails": source_info,
        "alertSeverity": alert_severity,
        "alertDetails": alert_details,
    }

    r = requests.post(url, data=data)
    if r.status_code == 200:
        print("Report generated")
        pass
    else:
        print("Unable to generate report")
        raise Exception("Unable to generate report")


@step("Login to <url> with username <username> and password <password>")
def login(url, username, password):
    login = requests.post(
        url, proxies=zap_proxy, json={"username": username, "password": password}
    )
    if login.status_code == 200:
        auth_token = login.headers["Authorization"]
        data_store.spec.token = auth_token
        print(data_store.spec.token)


@step("Search for customer <customer_name> in customer db")
def search(customer_name):
    search = requests.post(
        "http://127.0.0.1:5050/search",
        proxies=zap_proxy,
        headers={"Authorization": data_store.spec.token},
        json = {"search": customer_name}
    )
    if search.status_code == 200:
        print(search.json())
