"""Headless smoke/usability check for a locally running MustaCHE server.

Usage:
    python scripts/verify_web_ui.py http://127.0.0.1:5000 output.png
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait


base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
screenshot = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("mustache-ui-smoke.png")

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")
options.add_argument("--window-size=1440,1100")
options.add_argument("--disable-gpu")
options.set_capability("goog:loggingPrefs", {"browser": "ALL"})

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 90)
report = {"pages": {}, "assertions": [], "browser_errors": []}


def record(name: str, condition: bool, detail: str = "") -> None:
    report["assertions"].append({"name": name, "passed": bool(condition), "detail": detail})
    if not condition:
        raise AssertionError(f"{name}: {detail}")


try:
    for path in ("/", "/datasets", "/projects", "/settings"):
        driver.get(base_url + path)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        images = driver.execute_script(
            "return [...document.images].map(i => ({alt:i.alt, src:i.src, width:i.naturalWidth}))"
        )
        report["pages"][path] = {"title": driver.title, "images": images}
        record(f"assets load on {path}", all(item["width"] > 0 for item in images), json.dumps(images))

    driver.get(base_url + "/?sample_dataset=iris")
    form = wait.until(EC.visibility_of_element_located((By.ID, "batch-form")))
    Select(form.find_element(By.NAME, "algorithm")).select_by_value("hdbscan")
    min_input = form.find_element(By.NAME, "min_mpts")
    max_input = form.find_element(By.NAME, "max_mpts")
    step_input = form.find_element(By.NAME, "step")
    for element, value in ((min_input, "2"), (max_input, "6"), (step_input, "2")):
        element.clear()
        element.send_keys(value)
    form.find_element(By.CSS_SELECTOR, "button[type='submit']").click()

    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#meta-dendrogram .scatterlayer .trace")) >= 2)
    wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR, "#hai-heatmap .heatmaplayer")) >= 1)
    record("batch renders dendrogram", True)
    record("batch renders HAI heatmap", True)

    traces = driver.find_elements(By.CSS_SELECTOR, "#meta-dendrogram .scatterlayer .trace")
    branch = next(trace for trace in traces if trace.find_elements(By.CSS_SELECTOR, ".js-line"))
    # Emit the same Plotly event produced by clicking a branch marker. The
    # backend inserts a transparent marker at each branch midpoint so that a
    # physical click has a reliable hit target.
    driver.execute_script(
        "const d=document.getElementById('meta-dendrogram');"
        "d.emit('plotly_click',{points:[{data:d.data[0],pointIndex:2}]});"
    )
    badge = wait.until(EC.visibility_of_element_located((By.ID, "selected-branches-badge")))
    selected_text = badge.text
    record("branch click selects descendant hierarchies", "mpts" in selected_text, selected_text)
    record("clear-selection control appears", driver.find_element(By.ID, "btn-clear-selection").is_displayed())

    driver.find_element(By.ID, "btn-clear-selection").click()
    wait.until(lambda d: not d.find_element(By.ID, "selected-branches-badge").is_displayed())
    record("manual selection can be cleared", True)

    driver.save_screenshot(str(screenshot.resolve()))
    report["screenshot"] = str(screenshot.resolve())

    driver.set_window_size(390, 844)
    driver.get(base_url + "/")
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "mustache-layout")))
    body_width = driver.execute_script("return document.body.scrollWidth")
    viewport_width = driver.execute_script("return window.innerWidth")
    report["mobile"] = {"body_width": body_width, "viewport_width": viewport_width}
    record("mobile page avoids severe horizontal overflow", body_width <= viewport_width + 30,
           f"body={body_width}, viewport={viewport_width}")

    for entry in driver.get_log("browser"):
        if entry["level"] == "SEVERE":
            report["browser_errors"].append(entry["message"])
    record("no severe browser-console errors", not report["browser_errors"], str(report["browser_errors"]))
finally:
    driver.quit()

print(json.dumps(report, indent=2, ensure_ascii=False))
