import streamlit as st
import hmac
import time
import os
import gspread
from google.oauth2.service_account import Credentials


# Password screen for dashboard (note: only very basic authentication!)
# Based on https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
def check_password():
    """Returns 'True' if the user has entered a correct password."""

    def login_form():
        """Form with widgets to collect user information"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether username and password entered by the user are correct."""
        if st.session_state.username in st.secrets.passwords and hmac.compare_digest(
            st.session_state.password,
            st.secrets.passwords[st.session_state.username],
        ):
            st.session_state.password_correct = True

        else:
            st.session_state.password_correct = False

        del st.session_state.password  # don't store password in session state

    # Return True, username if password was already entered correctly before
    if st.session_state.get("password_correct", False):
        return True, st.session_state.username

    # Otherwise show login screen
    login_form()
    if "password_correct" in st.session_state:
        st.error("User or password incorrect")
    return False, st.session_state.username


def check_if_interview_completed(directory, username):
    """Check if interview transcript/time file exists which signals that interview was completed."""

    # Test account has multiple interview attempts
    if username != "testaccount":

        # Check if file exists
        try:
            with open(os.path.join(directory, f"{username}.txt"), "r") as _:
                return True

        except FileNotFoundError:
            return False

    else:

        return False


def save_to_google_sheets(anonymous_id, start_time, duration, demographics, completion_status):
    """Save completed interview to Google Sheets (three tabs)."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"])

        participant_code = demographics.get("participant_code", "")

        # Tab 1 — Demographics: shared with client after removing Session ID and Participant Code columns
        spreadsheet.get_worksheet(0).append_row([
            anonymous_id,
            participant_code,
            demographics.get("age", ""),
            demographics.get("gender", ""),
            demographics.get("location", ""),
            demographics.get("ethnicity", ""),
            completion_status,
        ])

        # Tab 2 — Transcripts: shared with client after removing Session ID and Participant Code columns
        lines = []
        for m in st.session_state.messages:
            if m["role"] == "system":
                continue
            if m["role"] == "user" and m["content"] == "Hi":
                continue
            label = "Interviewer" if m["role"] == "assistant" else "Participant"
            lines.append(f"{label}:\n{m['content']}")
        transcript_text = "\n\n---\n\n".join(lines)

        spreadsheet.get_worksheet(1).append_row([
            anonymous_id,
            participant_code,
            time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(start_time)),
            f"{duration:.2f}",
            transcript_text,
        ])
    except Exception:
        pass


def save_progress_to_sheets(anonymous_id, participant_code, messages):
    """Save in-progress transcript to a Progress tab in Google Sheets, updating existing row if present."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        gc = gspread.authorize(creds)
        spreadsheet = gc.open_by_key(st.secrets["GOOGLE_SHEET_ID"])

        all_titles = [ws.title.lower() for ws in spreadsheet.worksheets()]
        if "progress" in all_titles:
            idx = all_titles.index("progress")
            progress_ws = spreadsheet.worksheets()[idx]
        else:
            progress_ws = spreadsheet.add_worksheet(title="Progress", rows=200, cols=5)

        lines = []
        for m in messages:
            if m["role"] == "system":
                continue
            if m["role"] == "user" and m["content"] == "Hi":
                continue
            label = "Interviewer" if m["role"] == "assistant" else "Participant"
            lines.append(f"{label}:\n{m['content']}")
        transcript_text = "\n\n---\n\n".join(lines)

        timestamp = time.strftime("%d/%m/%Y %H:%M:%S")
        messages_count = sum(
            1 for m in messages
            if m["role"] in ("user", "assistant") and m["content"] != "Hi"
        )
        row_data = [anonymous_id, participant_code, timestamp, messages_count, transcript_text]

        cell = progress_ws.find(participant_code, in_column=2)
        if cell is None:
            progress_ws.append_row(row_data)
        else:
            progress_ws.update([row_data], f"A{cell.row}:E{cell.row}")
    except Exception:
        pass


def save_interview_data(
    username,
    transcripts_directory,
    times_directory,
    file_name_addition_transcript="",
    file_name_addition_time="",
    final=False,
    completion_status="Complete",
):
    """Write interview data (transcript and time) to disk. On final save, also write to Google Sheets."""

    duration = (time.time() - st.session_state.start_time) / 60

    # Store chat transcript locally
    with open(
        os.path.join(
            transcripts_directory, f"{username}{file_name_addition_transcript}.txt"
        ),
        "w",
    ) as t:
        for message in st.session_state.messages:
            t.write(f"{message['role']}: {message['content']}\n")

    # Store file with start time and duration locally
    with open(
        os.path.join(times_directory, f"{username}{file_name_addition_time}.txt"),
        "w",
    ) as d:
        d.write(
            f"Start time (UTC): {time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(st.session_state.start_time))}\nInterview duration (minutes): {duration:.2f}"
        )

    # Only save to Google Sheets once on final save, not during backups or loop retries
    if final and not st.session_state.get("sheets_saved", False):
        save_to_google_sheets(
            anonymous_id=st.session_state.get("anonymous_id", username),
            start_time=st.session_state.start_time,
            duration=duration,
            demographics=st.session_state.get("demographics", {}),
            completion_status=completion_status,
        )
        st.session_state.sheets_saved = True
