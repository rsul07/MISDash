"""Capture reproducible MIS Dash screenshots through the WebDriver protocol."""

from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import socket
import subprocess
import time
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = Path(__file__).resolve().parent
DESKTOP_SIZE = (1600, 900)
MOBILE_SIZE = (390, 844)


class WebDriver:
    """Small standard-library client for a local ChromeDriver session."""

    def __init__(self, *, chromedriver: str = "chromedriver") -> None:
        self.port = _free_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.process = subprocess.Popen(
            [
                chromedriver,
                f"--port={self.port}",
                "--allowed-ips=127.0.0.1",
                "--log-level=WARNING",
            ],
            cwd=ROOT,
        )
        _wait_until(lambda: _is_reachable(f"{self.base_url}/status"))
        response = self._request(
            "POST",
            "/session",
            {
                "capabilities": {
                    "alwaysMatch": {
                        "browserName": "chrome",
                        "goog:chromeOptions": {
                            "binary": "/usr/bin/chromium",
                            "args": [
                                "--headless=new",
                                "--no-sandbox",
                                "--disable-dev-shm-usage",
                                f"--window-size={DESKTOP_SIZE[0]},{DESKTOP_SIZE[1]}",
                                "--force-device-scale-factor=1",
                            ],
                        },
                    }
                }
            },
        )
        self.session_id = response["sessionId"]

    def close(self) -> None:
        if hasattr(self, "session_id"):
            try:
                self._request("DELETE", f"/session/{self.session_id}")
            except OSError:
                pass
        self.process.terminate()
        self.process.wait(timeout=5)

    def open(self, url: str) -> None:
        self._session_request("POST", "/url", {"url": url})

    def resize(self, width: int, height: int) -> None:
        self._session_request(
            "POST",
            "/window/rect",
            {"width": width, "height": height, "x": 0, "y": 0},
        )

    def execute(self, script: str) -> Any:
        return self._session_request(
            "POST",
            "/execute/sync",
            {"script": script, "args": []},
        )

    def wait_for(self, condition: str, *, timeout: float = 30) -> None:
        _wait_until(lambda: bool(self.execute(f"return Boolean({condition})")), timeout)

    def click_text(self, text: str) -> None:
        encoded = json.dumps(text, ensure_ascii=False)
        script = (
            """
            const normalize = (value) => value.replace(/\\s+/g, " ").trim();
            const target = normalize(%s);
            const element = [...document.querySelectorAll(
              "button, label, [role='tab']"
            )].find((item) => normalize(item.innerText || item.textContent) === target);
            if (!element || element.disabled) return false;
            element.click();
            return true;
            """
            % encoded
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if self.execute(script):
                return
            time.sleep(0.15)
        raise RuntimeError(f"Could not find control: {text}")

    def capture(self, filename: str) -> None:
        self.execute("window.scrollTo(0, 0); return true;")
        time.sleep(1.2)
        encoded = self._session_request("GET", "/screenshot")
        (OUTPUT_DIR / filename).write_bytes(base64.b64decode(encoded))

    def _session_request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        return self._request(
            method,
            f"/session/{self.session_id}{path}",
            payload,
        )

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        body = json.dumps(payload).encode() if payload is not None else None
        request = Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=30) as response:
            result = json.load(response)["value"]
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(result["message"])
        return result


def capture(url: str) -> None:
    driver = WebDriver()
    try:
        driver.open(url)
        driver.wait_for("document.body.innerText.includes('MIS Dash')")
        driver.click_text("Сгенерировать синтетическую выгрузку")
        driver.wait_for(
            "[...document.querySelectorAll('button')].some("
            "item => item.innerText.includes('Сгенерировать и открыть'))"
        )
        driver.click_text("Сгенерировать и открыть")
        driver.wait_for(
            "document.body.innerText.includes('Файл обработан')",
            timeout=90,
        )

        _capture_section(driver, "Обзор", "dashboard-overview.png", ".mis-patient-marker")
        _capture_section(
            driver,
            "Динамика",
            "dashboard-metrics.png",
            "[data-testid='stPlotlyChart']",
        )
        _capture_section(
            driver,
            "Приёмы",
            "dashboard-visits.png",
            ".mis-visit-table",
        )

        driver.resize(*MOBILE_SIZE)
        time.sleep(1)
        _close_sidebar(driver)
        _capture_section(
            driver,
            "Обзор",
            "dashboard-mobile-overview.png",
            ".mis-patient-marker",
        )
        _capture_section(
            driver,
            "Приёмы",
            "dashboard-mobile-visits.png",
            ".mis-visit-table",
        )
    finally:
        driver.close()


def _capture_section(
    driver: WebDriver,
    section: str,
    filename: str,
    ready_selector: str,
) -> None:
    driver.click_text(section)
    selector = json.dumps(ready_selector)
    driver.wait_for(f"document.querySelector({selector})")
    driver.wait_for(
        "window.innerWidth <= 720 || "
        "document.querySelector(\"[data-testid='stSidebar']\")"
        "?.innerText.includes('JSON-файл пациента')"
    )
    driver.capture(filename)


def _close_sidebar(driver: WebDriver) -> None:
    driver.execute(
        """
        const control = document.querySelector(
          "[data-testid='stSidebarCollapseButton'] button,"
          + " [data-testid='stSidebarCollapseButton']"
        );
        if (control) control.click();
        return true;
        """
    )
    time.sleep(0.5)


def _free_port() -> int:
    with socket.socket() as candidate:
        candidate.bind(("127.0.0.1", 0))
        return int(candidate.getsockname()[1])


def _is_reachable(url: str) -> bool:
    try:
        with urlopen(url, timeout=0.2):
            return True
    except OSError:
        return False


def _wait_until(
    predicate: Any,
    timeout: float = 10,
    interval: float = 0.1,
) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            if predicate():
                return
        except OSError:
            pass
        time.sleep(interval)
    raise TimeoutError("Timed out while waiting for browser state")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    arguments = parser.parse_args()
    capture(arguments.url)


if __name__ == "__main__":
    main()
