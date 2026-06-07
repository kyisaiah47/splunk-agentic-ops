import os
import time
import json
from typing import Any, Dict, List

import splunklib.client as splunk_client
import splunklib.results as splunk_results


class SplunkClient:
    def __init__(self):
        self._service: splunk_client.Service | None = None

    def _connect(self) -> splunk_client.Service:
        if self._service is None:
            self._service = splunk_client.connect(
                host=os.getenv("SPLUNK_HOST", "localhost"),
                port=int(os.getenv("SPLUNK_PORT", "8089")),
                username=os.getenv("SPLUNK_USERNAME", "admin"),
                password=os.getenv("SPLUNK_PASSWORD", ""),
                scheme=os.getenv("SPLUNK_SCHEME", "https"),
            )
        return self._service

    # ------------------------------------------------------------------
    # Tool dispatch
    # ------------------------------------------------------------------

    def execute_tool(self, tool_name: str, tool_input: Dict) -> Any:
        if tool_name == "run_spl_search":
            return self.run_search(
                query=tool_input["query"],
                earliest=tool_input.get("earliest_time", "-1h"),
                latest=tool_input.get("latest_time", "now"),
                max_results=tool_input.get("max_results", 100),
            )
        if tool_name == "get_alert_context":
            return self.get_alert_context(tool_input["alert_name"])
        if tool_name == "get_index_summary":
            return self.get_index_summary(tool_input["index_name"])
        return {"error": f"Unknown tool: {tool_name}"}

    # ------------------------------------------------------------------
    # Core search
    # ------------------------------------------------------------------

    def run_search(
        self,
        query: str,
        earliest: str = "-1h",
        latest: str = "now",
        max_results: int = 100,
    ) -> List[Dict]:
        svc = self._connect()
        spl = query if query.strip().startswith("search ") else f"search {query}"
        job = svc.jobs.create(
            spl,
            earliest_time=earliest,
            latest_time=latest,
            max_count=max_results,
        )
        # Poll until done
        while not job.is_done():
            time.sleep(0.5)

        rows = []
        reader = splunk_results.JSONResultsReader(
            job.results(output_mode="json", count=max_results)
        )
        for item in reader:
            if isinstance(item, dict):
                rows.append(item)
        job.cancel()
        return rows

    # ------------------------------------------------------------------
    # Alert / index helpers
    # ------------------------------------------------------------------

    def get_alert_context(self, alert_name: str) -> Dict:
        try:
            svc = self._connect()
            for ss in svc.saved_searches:
                if ss.name == alert_name:
                    return {
                        "name": ss.name,
                        "search": ss["search"],
                        "cron_schedule": ss.get("cron_schedule", ""),
                        "is_scheduled": ss.get("is_scheduled", False),
                        "alert_threshold": ss.get("alert_threshold", ""),
                    }
            return {"error": f"Alert '{alert_name}' not found"}
        except Exception as exc:
            return {"error": str(exc)}

    def get_index_summary(self, index_name: str) -> Dict:
        try:
            svc = self._connect()
            for idx in svc.indexes:
                if idx.name == index_name:
                    return {
                        "name": idx.name,
                        "total_event_count": idx["totalEventCount"],
                        "earliest_time": idx.get("earliestTime", ""),
                        "latest_time": idx.get("latestTime", ""),
                    }
            return {"error": f"Index '{index_name}' not found"}
        except Exception as exc:
            return {"error": str(exc)}
