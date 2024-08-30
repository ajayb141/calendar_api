from gcsa.conference import ConferenceSolutionCreateRequest, SolutionType
from gcsa.event import Event
from gcsa.google_calendar import GoogleCalendar
from gcsa.attendee import Attendee
from gcsa.reminders import EmailReminder
import dateparser
import pytz
import torch
import json
from datetime import timedelta, datetime
from groq import Groq
from tool_call import tools
import gradio as gr

import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama3-groq-70b-8192-tool-use-preview"

gc = GoogleCalendar(credentials_path=os.getenv("CREDENTAILS_PATH"))
# timezone = pytz.UTC


def check_busy_events(start, end, timezone):
    min_time = dateparser.parse(start).astimezone(timezone)
    max_time = dateparser.parse(end).astimezone(timezone)
    lst = []
    for event in gc.get_events(min_time, max_time):
        lst.append(event)
    if lst:
        return f"You are busy during the provided timeslot."
    else:
        return None


def merge_intervals(intervals):
    merged = []
    for start, end in sorted(intervals):
        if not merged or merged[-1][1] < start:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return merged


def subtract_intervals(full_interval, busy_intervals):
    free_intervals = []
    current_start = full_interval[0]

    for start, end in busy_intervals:
        if current_start < start:
            free_intervals.append((current_start, start))
        current_start = max(current_start, end)

    if current_start < full_interval[1]:
        free_intervals.append((current_start, full_interval[1]))

    return free_intervals


def busy_schedule(emails, timezone, time_min="", time_max=""):
    min_time = dateparser.parse(time_min).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone)
    max_time = dateparser.parse(time_max).replace(hour=23, minute=59, second=59, microsecond=59).astimezone(timezone)

    free_busy = gc.get_free_busy(emails, time_min=min_time, time_max=max_time, ignore_errors=True)

    busy_periods = set()
    for email in emails:
        if email in free_busy.calendars:
            for start, end in free_busy.calendars[email]:
                start_time = start.astimezone(timezone)
                end_time = end.astimezone(timezone)
                busy_periods.add((start_time, end_time))
        else:
            busy_periods.add((f"No schedule for {email} in the provided time.", ""))

    busy_intervals = [(start, end) for start, end in busy_periods if isinstance(start, datetime) and isinstance(end, datetime)]

    merged_intervals = merge_intervals(busy_intervals)

    full_day_interval = (min_time, max_time)

    free_intervals = subtract_intervals(full_day_interval, merged_intervals)

    formatted_free_intervals = [f"{start.strftime('%Y-%m-%d %H:%M:%S')} to {end.strftime('%Y-%m-%d %H:%M:%S')}" for start, end in free_intervals]

    format_free = "\n".join(formatted_free_intervals)
    return format_free


def check_users_availability(emails, start, end, timezone):
    min_time = dateparser.parse(start).astimezone(timezone)
    max_time = dateparser.parse(end).astimezone(timezone)

    free_busy = gc.get_free_busy(emails, time_min=min_time, time_max=max_time, ignore_errors=True)
    busy_periods = []

    for email in emails:
        if email in free_busy.calendars:
            for busy_start, busy_end in free_busy.calendars[email]:
                busy_start = busy_start.astimezone(timezone)
                busy_end = busy_end.astimezone(timezone)
                if not (busy_end <= min_time or busy_start >= max_time):
                    busy_periods.append((busy_start, busy_end))

    if busy_periods:
        common_free_slots = busy_schedule(emails, timezone, start, end)
        return False, f"Some users were busy during the provided slot. Please choose another timeslot:\n{common_free_slots}"
    else:
        return True, None


def create_event(title, emails, start, end, timezone_str=""):
    try:
        timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        timezone = pytz.UTC
    reminder_minutes = 30
    min_time = dateparser.parse(start).astimezone(timezone)
    max_time = dateparser.parse(end).astimezone(timezone)

    busy_info = check_busy_events(start, end, timezone)
    if busy_info:
        return busy_info
    all_free, busy_details = check_users_availability(emails, start, end, timezone)
    if not all_free:
        return f"{busy_details}"

    try:
        attendees = [Attendee(email=email) for email in emails]
        event = Event(
            title,
            start=min_time,
            end=max_time,
            reminders=[EmailReminder(minutes_before_start=reminder_minutes)],
            attendees=attendees,
            conference_solution=ConferenceSolutionCreateRequest(solution_type=SolutionType.HANGOUTS_MEET),
        )
        event = gc.add_event(event)
        return f"Event '{title}' created successfully."

    except ValueError as ve:
        return f"Error: {ve}"


def free_busy_schedule(emails, timezone_str="", time_min="", time_max=""):
    try:
        timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        timezone = pytz.UTC
    min_time = dateparser.parse(time_min).astimezone(timezone)
    max_time = dateparser.parse(time_max).astimezone(timezone)
    free_busy = gc.get_free_busy(emails, time_min=min_time, time_max=max_time, ignore_errors=True)

    busy_periods = []
    for email in emails:
        if email in free_busy.calendars:
            for start, end in free_busy.calendars[email]:
                print(type(start))
                start_time = start.strftime("%I%p").lower().lstrip("0")
                end_time = end.strftime("%I%p").lower().lstrip("0")
                output = f"{email} is busy from {start_time} to {end_time}"
                print(f"{min_time}-{start_time}")
                busy_periods.append(output)
        else:
            busy_periods.append(f"No schedule for {email} in the provided time. The user is free!")

    format_busy = f"\n".join(str(events) for events in busy_periods)
    return str(format_busy)


def cancel_event(start_date, timezone_str="", end_date=""):
    try:
        timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        timezone = pytz.UTC
    start_date = dateparser.parse(start_date).astimezone(timezone)
    end_date = dateparser.parse(end_date).astimezone(timezone) if end_date else start_date + timedelta(days=1)
    lst = []
    for event in gc.get_events(start_date, end_date):
        lst.append(event)
    if lst != []:
        for event in gc.get_events(start_date, end_date):
            gc.delete_event(event.event_id)
        return "Event deleted successfully!"
    else:
        return "The requested timeslot is empty. Please provide correct title and time for cancellation!"


def list_events(start_date, timezone_str="", end_date=""):
    try:
        timezone = pytz.timezone(timezone_str)
    except pytz.UnknownTimeZoneError:
        timezone = pytz.UTC
    schedule = []
    start_date = dateparser.parse(start_date).astimezone(timezone)
    end_date = dateparser.parse(end_date).astimezone(timezone) if end_date else start_date + timedelta(days=1)
    for event in gc.get_events(time_min=start_date, time_max=end_date):
        start = event.start
        end = event.end
        start_formatted = start.strftime("%Y-%m-%d %H:%M:%S")
        end_formatted = end.strftime("%Y-%m-%d %H:%M:%S")
        event_schedule = f"{event.summary} - from {start_formatted} to {end_formatted} "
        schedule.append(event_schedule)
    str_schedule = "\n".join(str(events) for events in schedule)
    if schedule != []:
        return str(str_schedule)
    else:
        return "There are no events scheduled. Enjoy your time..."


def chat_completion_request(messages, tools=None, model=MODEL):
    try:
        response = client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="auto", max_tokens=4096)
        response_message = response.choices[0].message
        # print("response_message = ",response_message)
        tool_calls = response_message.tool_calls
        # print("tool_calls = ",tool_calls)
        return response
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e

msg = {
                "role": "system",
                "content": "You are an experienced google calendar assistant. Use the tools provided to you to process requests. Don't make assumptions about what values to plug into functions. Ask for clarification if a user request is ambiguous.",
            }
messages = [msg]
def run_conversation(user_input, history):
    global messages
    messages.append({"role": "user", "content": user_input})
    response = chat_completion_request(messages, tools)
    re_msg = response.choices[0].message
    if re_msg.tool_calls == None:
        return str(re_msg.content)
    else:
        tool_call_lst = re_msg.tool_calls
        print(tool_call_lst)
        available_functions = {
            "create_event": create_event,
            "free_busy_schedule": free_busy_schedule,
            "cancel_event": cancel_event,
            "list_events": list_events,
        }
        messages = [msg]
        for tool_call in tool_call_lst:
            print("tool_call", tool_call)
            function_name = tool_call.function.name
            print("function_name :", function_name)
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            print("function_args :", function_args)
            function_response = function_to_call(**function_args)
            print(function_response) 
            return str(function_response)

iface = gr.ChatInterface(
    fn=run_conversation,
    title="Calendar-API",
).launch()
