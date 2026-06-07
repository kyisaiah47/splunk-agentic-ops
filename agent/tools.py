INVESTIGATION_TOOLS = [
    {
        "name": "run_spl_search",
        "description": (
            "Execute a Splunk SPL search query and return matching events as JSON. "
            "Use this to investigate logs, metrics, and events. Always include time bounds."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "SPL query string. Do NOT include leading 'search' keyword for piped queries.",
                },
                "earliest_time": {
                    "type": "string",
                    "description": "Search start time. Relative (e.g. '-1h', '-30m', '-7d@d') or ISO 8601.",
                    "default": "-4h",
                },
                "latest_time": {
                    "type": "string",
                    "description": "Search end time. Usually 'now'.",
                    "default": "now",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Cap on results returned. Keep <=200 for efficiency.",
                    "default": 100,
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_alert_context",
        "description": "Fetch the saved-search definition and recent trigger history for a named Splunk alert.",
        "input_schema": {
            "type": "object",
            "properties": {
                "alert_name": {
                    "type": "string",
                    "description": "Exact name of the Splunk saved search / alert.",
                }
            },
            "required": ["alert_name"],
        },
    },
    {
        "name": "get_index_summary",
        "description": "Return event-count and time-range metadata for a Splunk index. Useful for confirming data availability before searching.",
        "input_schema": {
            "type": "object",
            "properties": {
                "index_name": {
                    "type": "string",
                    "description": "Name of the Splunk index (e.g. 'main', 'web_logs').",
                }
            },
            "required": ["index_name"],
        },
    },
]
