from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QObject, Signal


@dataclass
class AuditResult:
    id: str
    title: str
    description: str
    score: float | None
    display_value: str
    score_display_mode: str


class PageSpeedSignals(QObject):
    log = Signal(str)
    progress = Signal(int)
    finished = Signal(bool, dict, str)  # success, data (score and audits), error_message


class PageSpeedService:
    def __init__(self) -> None:
        self.base_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

    def test_accessibility(self, url: str, api_key: str, signals: PageSpeedSignals) -> None:
        signals.log.emit(f"Preparing to test accessibility for: {url}")
        signals.progress.emit(10)
        
        try:
            params = {
                "url": url,
                "category": "accessibility"
            }
            if api_key:
                params["key"] = api_key

            query_string = urllib.parse.urlencode(params)
            request_url = f"{self.base_url}?{query_string}"
            
            signals.log.emit("Sending API request to Google PageSpeed Insights...")
            signals.progress.emit(30)
            
            req = urllib.request.Request(request_url, headers={"User-Agent": "Mozilla/5.0"})
            
            with urllib.request.urlopen(req, timeout=60) as response:
                signals.log.emit("Response received. Parsing JSON...")
                signals.progress.emit(70)
                
                body = response.read()
                data = json.loads(body)
                
                # Extract Accessibility Score (value is 0 to 1, we map to 0 to 100)
                score_fraction = data.get("lighthouseResult", {}).get("categories", {}).get("accessibility", {}).get("score", 0)
                final_score = int(score_fraction * 100)
                
                signals.log.emit(f"Extracted overall accessibility score: {final_score}/100")
                signals.progress.emit(85)
                
                # Extract Audits
                audits_data = data.get("lighthouseResult", {}).get("audits", {})
                category_refs = data.get("lighthouseResult", {}).get("categories", {}).get("accessibility", {}).get("auditRefs", [])
                
                # Filter only audits that are part of the accessibility category
                accessibility_audit_ids = [ref["id"] for ref in category_refs]
                
                audits: list[AuditResult] = []
                for audit_id in accessibility_audit_ids:
                    audit_info = audits_data.get(audit_id)
                    if audit_info:
                        audits.append(
                            AuditResult(
                                id=audit_info.get("id", ""),
                                title=audit_info.get("title", ""),
                                description=audit_info.get("description", ""),
                                score=audit_info.get("score"),
                                display_value=audit_info.get("displayValue", ""),
                                score_display_mode=audit_info.get("scoreDisplayMode", "")
                            )
                        )
                
                signals.log.emit(f"Extracted {len(audits)} specific accessibility audits.")
                signals.progress.emit(100)
                
                result_data = {
                    "score": final_score,
                    "audits": audits
                }
                signals.finished.emit(True, result_data, "")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            msg = f"HTTP Error {e.code}: {e.reason}\nDetails: {error_body}"
            signals.log.emit(f"[ERROR] {msg}")
            signals.finished.emit(False, {}, msg)
        except urllib.error.URLError as e:
            msg = f"URL Error: {e.reason}"
            signals.log.emit(f"[ERROR] {msg}")
            signals.finished.emit(False, {}, msg)
        except Exception as e:
            msg = f"Unexpected Error: {str(e)}"
            signals.log.emit(f"[ERROR] {msg}")
            signals.finished.emit(False, {}, msg)
