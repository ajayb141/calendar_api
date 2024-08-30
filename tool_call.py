tools = [
    {
        "type": "function",
        "function": {
            "name": "create_event",
            "description": "Create a Google Calendar event based on emails, Title, start and end",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "The title of the event",
                    },
                    "emails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email id of the user (e.g., abcd@example.com)",
                    },
                    "start": {
                        "type": "string",
                        "description": "start date and time of the event.",
                    },
                    "end": {
                        "type": "string",
                        "description": "start date and time of the event.",
                    },
                    "timezone_str": {
                        "type": "string",
                        "description": "Timezone for the event. If not specified, the default timezone is UTC.(optional)",
                        "default": "UTC",
                    },
                },
                "required": ["title", "emails", "start", "end"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "free_busy_schedule",
            "description": "Checking if the person is available or not, based on the emails with email id",
            "parameters": {
                "type": "object",
                "properties": {
                    "emails": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Email id of the user (e.g., abcd@example.com)",
                    },
                    "time_min": {
                        "type": "string",
                        "description": "Start point of the time (optional)",
                    },
                    "time_max": {
                        "type": "string",
                        "description": "End point of the time (optional)",
                    },
                    "timezone_str": {
                        "type": "string",
                        "description": "Timezone for the event. If not specified, the default timezone is UTC.(optional)",
                        "default": "UTC",
                    },
                },
                "required": ["emails"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_event",
            "description": "Cancel an event or meeting from the Google Calendar for a specific period of time or the whole day.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "The start date or start date with time of the event.",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "The end date or end date with time of the event (optional)",
                    },
                    "timezone_str": {
                        "type": "string",
                        "description": "Timezone for the event. If not specified, the default timezone is UTC.(optional)",
                        "default": "UTC",
                    },
                },
                "required": ["start_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_events",
            "description": "list/get/search/find/show events or meetings from Google Calendar.",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {
                        "type": "string",
                        "description": "The start date or start date with time of the event",
                    },
                    "end_date": {
                        "type": "string",
                        "description": "The end date or end date with time of the event(optional)",
                    },
                    "timezone_str": {
                        "type": "string",
                        "description": "Timezone for the event. If not specified, the default timezone is UTC.(optional)",
                        "default": "UTC",
                    },
                },
                "required": ["start_date"],
            },
        },
    },
]