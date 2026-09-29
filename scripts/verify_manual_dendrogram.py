"""Real-pointer E2E for manual meta-dendrogram selection.

Run with ``python scripts/verify_manual_dendrogram.py OUTPUT_DIR`` after
``pip install playwright`` with Google Chrome installed.
The script starts the installed MustaCHE package in a fresh project directory.
Pass ``--base-url`` only when testing an already-running local development server.
No Plotly event is synthesized: every branch selection uses a browser mouse click.
"""

from __future__ import annotations

import argparse
import csv
from io import BytesIO
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from zipfile import ZipFile

from playwright.sync_api import sync_playwright


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_for_server(url: str) -> None:
    from urllib.request import urlopen

    for _ in range(100):
        try:
            with urlopen(url, timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"MustaCHE server did not start at {url}")


def marker_data(page) -> dict:
    return page.evaluate("""() => {
        const plot = document.getElementById('meta-dendrogram');
        const trace = plot.data.at(-1);
        return {role: trace.meta?.role, ids: trace.customdata, x: trace.x,
            groups: trace.meta?.branch_members, count: plot.data.length,
            ordered: [...document.querySelectorAll('#inspect-mpts option')].map(o => Number(o.value))};
    }""")


def marker(page, index: int):
    return page.locator("#meta-dendrogram .scatterlayer .trace:last-child .points path").nth(index)


def physical_click(page, index: int) -> dict:
    # Attach a passive observer to the current Plotly instance. Mode changes
    # can purge/recreate it, so an observer attached earlier may be stale.
    install_event_observer(page)
    dot = marker(page, index)
    box = dot.bounding_box()
    assert box and box["width"] >= 7 and box["height"] >= 7, "Marker has no usable hit target"
    with page.expect_response(lambda response: response.url.endswith("/cut_dendrogram"), timeout=15000) as observed:
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    response = observed.value
    assert response.ok, response.text()
    events = page.evaluate("window.realPlotlyClicks")
    assert len(events) >= 1, ("Physical click did not emit plotly_click",
                              {"events": events, "response": response.json(), "box": box})
    assert events[-1]["curve"] == marker_data(page)["count"] - 1, "Click hit a line, not the marker trace"
    return response.json()


def install_event_observer(page) -> None:
    page.evaluate("""() => {
        if (window.realPlotlyClickPlot && window.realPlotlyClickObserver) {
            window.realPlotlyClickPlot.removeListener('plotly_click', window.realPlotlyClickObserver);
        }
        window.realPlotlyClicks = [];
        window.realPlotlyClickPlot = document.getElementById('meta-dendrogram');
        window.realPlotlyClickObserver = event =>
            window.realPlotlyClicks.push({curve: event.points?.[0]?.curveNumber,
                point: event.points?.[0]?.pointNumber,
                node: event.points?.[0]?.customdata});
        window.realPlotlyClickPlot.on('plotly_click', window.realPlotlyClickObserver);
    }""")


def select_mode(page, value: str) -> None:
    with page.expect_response(lambda response: response.url.endswith("/cut_dendrogram"), timeout=15000) as observed:
        page.locator("#meta-selection-mode").select_option(value)
    assert observed.value.ok, observed.value.text()
    page.wait_for_load_state("networkidle")


def batch(page, base: str, minimum: int, maximum: int, step: int = 2) -> dict:
    page.goto(base + "/?sample_dataset=iris")
    form = page.locator("#batch-form")
    form.wait_for(state="visible")
    assert form.locator('[name="algorithm"]').input_value() == "core-sg"
    for name, value in (("min_mpts", minimum), ("max_mpts", maximum), ("step", step)):
        form.locator(f'[name="{name}"]').fill(str(value))
    with page.expect_response(lambda response: response.url.endswith("/batch"), timeout=120000) as observed:
        form.locator('[type="submit"]').click()
    response = observed.value
    assert response.ok, response.text()
    page.locator("#meta-dendrogram .scatterlayer .trace:last-child .points path").first.wait_for()
    return response.json()


def medoid(group: list[int], ordered: list[int], hai: list[list[float]]) -> int:
    return min(group, key=lambda value: (sum(1 - hai[ordered.index(value)][ordered.index(other)]
                                             for other in group), ordered.index(value)))


def run(base: str, output: Path, project_root: Path | None = None, restart_server=None) -> dict:
    report = {"checks": [], "console_errors": [], "failed_responses": []}

    def check(name: str, condition: bool) -> None:
        report["checks"].append({"name": name, "passed": bool(condition)})
        assert condition, name

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000}, accept_downloads=True)
        page = context.new_page()
        page.on("console", lambda message: report["console_errors"].append(message.text) if message.type == "error" else None)
        page.on("pageerror", lambda error: report["console_errors"].append(str(error)))
        page.on("response", lambda response: report["failed_responses"].append((response.url, response.status))
                if response.status >= 400 else None)
        page.on("dialog", lambda dialog: dialog.accept())

        data = batch(page, base, 4, 12)
        ordered = data["analysis"]["ordered_mpts"]
        check("five real CORE-SG hierarchies", ordered == [4, 6, 8, 10, 12])
        select_mode(page, "manual")
        page.get_by_text("5 unselected").wait_for()
        page.locator("#manual-selection-help").wait_for(state="visible")
        check("manual instructions visible", page.locator("#manual-selection-help").is_visible())
        check("manual unselected are not outliers", "0 outliers" in page.locator("#cache-indicator").inner_text())
        targets = marker_data(page)
        check("one visible target per internal node", targets["role"] == "branch-targets"
              and len(targets["ids"]) == len(ordered) - 1
              and marker(page, 0).is_visible())
        hover_box = marker(page, 0).bounding_box()
        page.mouse.move(hover_box["x"] + hover_box["width"] / 2,
                        hover_box["y"] + hover_box["height"] / 2)
        page.wait_for_function("document.querySelector('#meta-dendrogram .draglayer .nsewdrag')?.style.cursor === 'pointer'")
        check("interactive marker has pointer cursor", page.locator(
              "#meta-dendrogram .draglayer .nsewdrag").evaluate("element => getComputedStyle(element).cursor") == "pointer")
        check("marker hover explains branch", "Select hierarchy group" in
              page.locator("#meta-dendrogram .hoverlayer").text_content())
        install_event_observer(page)
        page.screenshot(path=str(output / "before-manual-click.png"), full_page=True)

        small_index = min(range(len(targets["ids"])), key=lambda i: len(targets["groups"][str(targets["ids"][i])]))
        small_group = targets["groups"][str(targets["ids"][small_index])]
        initial_fill = marker(page, small_index).evaluate("element => getComputedStyle(element).fill")
        selected = physical_click(page, small_index)
        check("real click updates backend group", selected["manual_groups"] == [small_group])
        check("medoid minimizes within-group 1 - HAI", list(selected["medoids"].values()) ==
              [medoid(small_group, ordered, data["analysis"]["hai_matrix"])])
        check("visible branch count", page.locator("#selected-branches-badge").is_visible()
              and "1 branch selected" in page.locator("#selected-branches-badge").inner_text())
        check("marker visually changes", marker(page, small_index).evaluate("element => getComputedStyle(element).fill") != initial_fill)
        check("representative reachability shown", page.locator(".reachability-plot-wrapper").count() == 1
              and f"mpts = {list(selected['medoids'].values())[0]}" in page.locator("#reachability-container").inner_text())
        page.screenshot(path=str(output / "after-manual-click.png"), full_page=True)

        toggled = physical_click(page, small_index)
        check("repeated click deselects", toggled["manual_groups"] == []
              and page.locator("#selected-branches-badge").is_hidden())
        root_index = max(range(len(targets["ids"])), key=lambda i: len(targets["groups"][str(targets["ids"][i])]))
        root = physical_click(page, root_index)
        check("root selects all descendants", root["manual_groups"] == [ordered])
        child = physical_click(page, small_index)
        check("child replaces overlapping parent", child["manual_groups"] == [small_group])
        check("selection updates representative", list(child["medoids"].values()) ==
              [medoid(small_group, ordered, data["analysis"]["hai_matrix"])])

        select_mode(page, "automatic")
        check("automatic mode hides inactive manual selection", page.locator("#selected-branches-badge").is_hidden())
        select_mode(page, "threshold")
        select_mode(page, "manual")
        check("manual choice survives mode switch", "1 branch selected" in page.locator("#selected-branches-badge").inner_text())

        page.locator("#btn-save-top").click()
        page.locator("#main-save-proj-name").fill("Real pointer selection — Iris")
        with page.expect_response(lambda response: response.url.endswith("/api/projects/save")) as observed:
            page.get_by_role("button", name="Save project", exact=True).click()
        save = observed.value.json()
        check("save succeeds", observed.value.ok and bool(save["project"]["id"]))
        project_id = save["project"]["id"]
        if restart_server is not None:
            restart_server()
            check("server restarted before project reopen", True)
        page.goto(base + "/?project_id=" + project_id)
        page.locator("#meta-dendrogram .scatterlayer .trace:last-child .points path").first.wait_for()
        check("manual mode restored", page.locator("#meta-selection-mode").input_value() == "manual")
        check("selected branch restored visually", "1 branch selected" in page.locator("#selected-branches-badge").inner_text())
        check("representative restored", f"mpts = {list(child['medoids'].values())[0]}" in
              page.locator("#reachability-container").inner_text())
        restored = page.request.get(base + "/api/projects/" + project_id + "/data").json()
        check("manual state persists", restored["analysis"]["manual_groups"] == [small_group]
              and restored["analysis"]["selected_mpts"] == small_group)
        with page.expect_download() as download_info:
            page.locator("#btn-export-csv").click()
        download = download_info.value
        exported = output / "manual-selection.csv"
        download.save_as(exported)
        with exported.open(newline="", encoding="utf-8-sig") as stream:
            columns = next(csv.reader(stream))
        check("CSV exports only selected hierarchies", {int(column.split("_")[-1]) for column in columns
              if column.startswith("Cluster_mpts_")} == set(small_group))
        zip_response = page.request.get(base + f"/api/projects/{project_id}/export_zip")
        check("ZIP export available", zip_response.ok)
        with ZipFile(BytesIO(zip_response.body())) as archive:
            saved = json.loads(archive.read("results.json"))
        check("ZIP retains manual partition", saved["analysis"]["manual_groups"] == [small_group])
        report["project_id"] = project_id

        if project_root is not None:
            # Simulate a project saved by the previous RC: each U-shaped line
            # contained an invisible midpoint marker, and hover was disabled.
            # Reopen through the real project API, then click the upgraded node.
            path = project_root / project_id / "results.json"
            old_project = json.loads(path.read_text(encoding="utf-8"))
            old_figure = json.loads(old_project["analysis"]["meta_dendrogram_json"])
            old_figure["data"].pop()  # no separate branch-target trace
            for trace in old_figure["data"]:
                x, y = trace["x"], trace["y"]
                trace["x"] = [x[0], x[1], (x[1] + x[2]) / 2, x[2], x[3]]
                trace["y"] = [y[0], y[1], y[1], y[2], y[3]]
                trace["mode"] = "lines+markers"
                trace["marker"] = {"size": 18, "opacity": 0}
            old_figure["layout"]["hovermode"] = False
            old_project["analysis"]["meta_dendrogram_json"] = json.dumps(old_figure)
            path.write_text(json.dumps(old_project), encoding="utf-8")
            page.goto(base + "/?project_id=" + project_id)
            page.locator("#meta-dendrogram .scatterlayer .trace:last-child .points path").first.wait_for()
            check("old saved figure upgraded on reopen", marker_data(page)["role"] == "branch-targets")
            old_targets = marker_data(page)
            old_root = max(range(len(old_targets["ids"])),
                           key=lambda i: len(old_targets["groups"][str(old_targets["ids"][i])]))
            check("upgraded old project receives a real click", physical_click(page, old_root)["manual_groups"] == [ordered])

        medium = batch(page, base, 2, 20)
        medium_targets = marker_data(page)
        check("medium dendrogram targets", len(medium_targets["ids"]) == len(medium["analysis"]["ordered_mpts"]) - 1)
        select_mode(page, "manual")
        install_event_observer(page)
        independent = next(((i, j) for i, left in enumerate(medium_targets["ids"])
                            for j, right in enumerate(medium_targets["ids"]) if j > i and
                            not set(medium_targets["groups"][str(left)]) & set(medium_targets["groups"][str(right)])), None)
        check("independent internal branches exist", independent is not None)
        first, second = independent
        first_group = medium_targets["groups"][str(medium_targets["ids"][first])]
        second_group = medium_targets["groups"][str(medium_targets["ids"][second])]
        physical_click(page, first)
        pair = physical_click(page, second)
        check("two independent branches coexist", pair["manual_groups"] == [first_group, second_group]
              and "2 branches selected" in page.locator("#selected-branches-badge").inner_text()
              and page.locator(".reachability-plot-wrapper").count() == 2)
        page.screenshot(path=str(output / "medium-two-branches.png"), full_page=False)
        medium_root_index = max(range(len(marker_data(page)["ids"])),
                                key=lambda i: len(marker_data(page)["groups"][str(marker_data(page)["ids"][i])]))
        check("root replaces both child branches", physical_click(page, medium_root_index)["manual_groups"] ==
              [medium["analysis"]["ordered_mpts"]])
        page.screenshot(path=str(output / "medium-desktop.png"), full_page=False)

        many = batch(page, base, 2, 50)
        check("many dendrogram targets", len(marker_data(page)["ids"]) == len(many["analysis"]["ordered_mpts"]) - 1)
        page.set_viewport_size({"width": 390, "height": 844})
        select_mode(page, "manual")
        install_event_observer(page)
        mobile = marker_data(page)
        check("mobile dendrogram scrolls", page.evaluate("""() => {
            const pane = document.querySelector('.dendrogram-scroll');
            return pane.scrollWidth > pane.clientWidth;
        }"""))
        check("mobile page has no horizontal overflow", page.evaluate(
              "document.body.scrollWidth <= window.innerWidth + 2"))
        rightmost = max(range(len(mobile["ids"])), key=lambda i: mobile["x"][i])
        dot = marker(page, rightmost)
        dot.scroll_into_view_if_needed()
        check("far marker reachable by horizontal scroll", page.evaluate(
              "document.querySelector('.dendrogram-scroll').scrollLeft > 0"))
        mobile_result = physical_click(page, rightmost)
        check("mobile real click works", mobile_result["manual_groups"] ==
              [mobile["groups"][str(mobile["ids"][rightmost])]])
        page.screenshot(path=str(output / "many-mobile.png"), full_page=False)

        check("no browser errors", not report["console_errors"])
        check("no failed HTTP responses", not report["failed_responses"])
        browser.close()
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--base-url", help="Use an already running local server instead of starting one")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    server = None
    with tempfile.TemporaryDirectory(prefix="mustache-manual-e2e-") as isolated:
        base = args.base_url
        restart_server = None
        if not base:
            import mustache
            import core_sg

            prefix = Path(sys.prefix).resolve()
            packages = {"mustache": str(Path(mustache.__file__).resolve()),
                        "core_sg": str(Path(core_sg.__file__).resolve())}
            assert all(Path(path).is_relative_to(prefix) for path in packages.values()), packages
            port = free_port()
            base = f"http://127.0.0.1:{port}"
            env = dict(os.environ, MUSTACHE_PROJECTS_DIR=str(Path(isolated) / "projects"))
            env.pop("PYTHONPATH", None)

            def start_server():
                nonlocal server
                server = subprocess.Popen([sys.executable, "-m", "mustache.cli", "--host", "127.0.0.1",
                                           "--port", str(port)], cwd=isolated, env=env,
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                wait_for_server(base)

            def restart_server():
                old_pid = server.pid
                server.terminate()
                server.wait(timeout=10)
                start_server()
                assert server.pid != old_pid, "Server process was not replaced"

            start_server()
        try:
            report = run(base, output, None if args.base_url else Path(isolated) / "projects", restart_server)
            if not args.base_url:
                report["installed_package_paths"] = packages
            report["status"] = "PASS"
        except Exception as error:
            report = {"status": "FAIL", "error": repr(error)}
            raise
        finally:
            (output / "manual-e2e.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
            print(json.dumps(report, indent=2), flush=True)
            if server:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()
