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


def save_to_google_sheets(anonymous_id, start_time, duration):
    """Save completed interview transcript and metadata to Google Sheets."""
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(st.secrets["GOOGLE_SHEET_ID"]).sheet1

        # Format transcript readably, skipping system prompt and silent opening "Hi" trigger
        lines = []
        for m in st.session_state.messages:
            if m["role"] == "system":
                continue
            if m["role"] == "user" and m["content"] == "Hi":
                continue
            label = "Interviewer" if m["role"] == "assistant" else "Participant"
            lines.append(f"{label}:\n{m['content']}")
        transcript_text = "\n\n---\n\n".join(lines)

        sheet.append_row([
            anonymous_id,
            time.strftime("%d/%m/%Y %H:%M:%S", time.localtime(start_time)),
            f"{duration:.2f}",
            transcript_text,
        ])
    except Exception:
        pass


def save_interview_data(
    username,
    transcripts_directory,
    times_directory,
    file_name_addition_transcript="",
    file_name_addition_time="",
    final=False,
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
        )
        st.session_state.sheets_saved = True
