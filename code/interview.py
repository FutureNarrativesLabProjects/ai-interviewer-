import streamlit as st
import time
import uuid
from utils import (
    check_password,
    check_if_interview_completed,
    save_interview_data,
)
import os
import config

# Load API library
if "gpt" in config.MODEL.lower():
    api = "openai"
    from openai import OpenAI

elif "claude" in config.MODEL.lower():
    api = "anthropic"
    import anthropic

elif "mistral" in config.MODEL.lower():
    api = "mistral"
    from mistralai import Mistral

else:
    raise ValueError(
        "Model does not contain 'gpt', 'claude', or 'mistral'; unable to determine API."
    )

# Set page title and icon
st.set_page_config(page_title="Interview", page_icon=config.AVATAR_INTERVIEWER)

# Initialise session state flags
if "entered" not in st.session_state:
    st.session_state.entered = False
if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False
if "language" not in st.session_state:
    st.session_state.language = "English"

# Exit page — shown after interview is fully completed
if st.session_state.interview_completed:
    if st.session_state.language == "Español":
        st.markdown(
            """
            <div style="text-align: center; padding: 80px 20px;">
                <h2 style="font-size: 2rem; font-weight: 600; margin-bottom: 1rem;">Muchas gracias</h2>
                <p style="font-size: 1.15rem; color: #555; max-width: 500px; margin: 0 auto;">
                    Ha completado la entrevista. Su contribución ayudará a dar forma a la Oportunidad de la Calle Walworth. Apreciamos mucho su tiempo.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="text-align: center; padding: 80px 20px;">
                <h2 style="font-size: 2rem; font-weight: 600; margin-bottom: 1rem;">Thank you for completing the interview</h2>
                <p style="font-size: 1.15rem; color: #555; max-width: 500px; margin: 0 auto;">
                    Your contribution will help shape the Walworth Road Opportunity. We really appreciate your time.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.stop()

# Landing page
if not st.session_state.entered:
    landing = st.empty()
    with landing.container():
        # Logos
        img_dir = os.path.join(os.path.dirname(__file__), "images")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.image(os.path.join(img_dir, "logo-kings.png"), use_container_width=True)
        with col2:
            st.image(os.path.join(img_dir, "logo-pembroke.svg"), use_container_width=True)
        with col3:
            st.image(os.path.join(img_dir, "logo-fnl.png"), use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            """
            <div style="text-align: center;">
                <h2 style="font-size: 1.8rem; font-weight: 600; margin-bottom: 0.75rem;">Walworth Road Opportunity — Community Interview</h2>
                <p style="font-size: 1.1rem; color: #555; max-width: 520px; margin: 0 auto 2rem;">
                    This interview is part of Pembroke House's research into what community ownership could look like for a new food space in Walworth.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Language selector
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            language = st.radio(
                "Select language / Seleccione idioma",
                ["English", "Español"],
                horizontal=True,
            )
            st.session_state.language = language

        st.markdown("<br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Enter Interview", use_container_width=True, type="primary"):
                landing.empty()
                st.session_state.entered = True
                st.rerun()
    st.stop()

# Build effective system prompt based on language
if st.session_state.language == "Español":
    effective_system_prompt = config.SYSTEM_PROMPT + (
        "\n\nIMPORTANT: This participant has chosen to conduct the interview in Spanish. "
        "Please conduct the entire interview in Spanish (Español) from your very first message. "
        "All your questions, follow-ups, and responses must be in Spanish."
    )
else:
    effective_system_prompt = config.SYSTEM_PROMPT

# Check if usernames and logins are enabled
if config.LOGINS:
    pwd_correct, username = check_password()
    if not pwd_correct:
        st.stop()
    else:
        st.session_state.username = username
else:
    st.session_state.username = "testaccount"

# Create directories if they do not already exist
if not os.path.exists(config.TRANSCRIPTS_DIRECTORY):
    os.makedirs(config.TRANSCRIPTS_DIRECTORY)
if not os.path.exists(config.TIMES_DIRECTORY):
    os.makedirs(config.TIMES_DIRECTORY)
if not os.path.exists(config.BACKUPS_DIRECTORY):
    os.makedirs(config.BACKUPS_DIRECTORY)

# Initialise session state
if "interview_active" not in st.session_state:
    st.session_state.interview_active = True

if "messages" not in st.session_state:
    st.session_state.messages = []

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
    st.session_state.start_time_file_names = time.strftime(
        "%Y_%m_%d_%H_%M_%S", time.localtime(st.session_state.start_time)
    )

if "anonymous_id" not in st.session_state:
    st.session_state.anonymous_id = str(uuid.uuid4())

# Check if interview previously completed
interview_previously_completed = check_if_interview_completed(
    config.TIMES_DIRECTORY, st.session_state.username
)

if interview_previously_completed and not st.session_state.messages:
    st.session_state.interview_active = False
    st.markdown("Interview already completed.")

# Add 'Quit' button to dashboard
col1, col2 = st.columns([0.85, 0.15])
with col2:
    if st.session_state.interview_active and st.button("Quit", help="End the interview."):
        st.session_state.interview_active = False
        quit_message = "You have cancelled the interview."
        st.session_state.messages.append({"role": "assistant", "content": quit_message})
        save_interview_data(
            st.session_state.username,
            config.TRANSCRIPTS_DIRECTORY,
            config.TIMES_DIRECTORY,
        )

# Display previous conversation (skip system prompt, "Hi" trigger, and coded messages)
for message in st.session_state.messages[1:]:
    if message["role"] == "system":
        continue
    if message["role"] == "assistant":
        avatar = config.AVATAR_INTERVIEWER
    else:
        avatar = config.AVATAR_RESPONDENT
    if not any(code in message["content"] for code in config.CLOSING_MESSAGES.keys()):
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])

# Load API client
if api == "openai":
    client = OpenAI(api_key=st.secrets["API_KEY_OPENAI"])
    api_kwargs = {"stream": True}
elif api == "anthropic":
    client = anthropic.Anthropic(api_key=st.secrets["API_KEY_ANTHROPIC"])
    api_kwargs = {"system": effective_system_prompt}
elif api == "mistral":
    client = Mistral(api_key=st.secrets["API_KEY_MISTRAL"])
    api_kwargs = {}

# API kwargs
api_kwargs["messages"] = st.session_state.messages
api_kwargs["model"] = config.MODEL
api_kwargs["max_tokens"] = config.MAX_OUTPUT_TOKENS
if config.TEMPERATURE is not None:
    api_kwargs["temperature"] = config.TEMPERATURE

# Generate first message if interview just started
if not st.session_state.messages:

    if api == "openai":
        st.session_state.messages.append(
            {"role": "system", "content": effective_system_prompt}
        )
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            stream = client.chat.completions.create(**api_kwargs)
            message_interviewer = st.write_stream(stream)

    elif api == "anthropic":
        st.session_state.messages.append({"role": "user", "content": "Hi"})
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            message_placeholder = st.empty()
            message_interviewer = ""
            with client.messages.stream(**api_kwargs) as stream:
                for text_delta in stream.text_stream:
                    if text_delta is not None:
                        message_interviewer += text_delta
                    message_placeholder.markdown(message_interviewer + "▌")
            message_placeholder.markdown(message_interviewer)

    elif api == "mistral":
        st.session_state.messages.append(
            {"role": "system", "content": effective_system_prompt}
        )
        st.session_state.messages.append({"role": "user", "content": "Hi"})
        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):
            message_placeholder = st.empty()
            response = client.chat.complete(
                model=config.MODEL,
                messages=st.session_state.messages,
                max_tokens=config.MAX_OUTPUT_TOKENS,
            )
            message_interviewer = response.choices[0].message.content
            message_placeholder.markdown(message_interviewer)

    st.session_state.messages.append(
        {"role": "assistant", "content": message_interviewer}
    )

    save_interview_data(
        username=st.session_state.username,
        transcripts_directory=config.BACKUPS_DIRECTORY,
        times_directory=config.BACKUPS_DIRECTORY,
        file_name_addition_transcript=f"_transcript_started_{st.session_state.start_time_file_names}",
        file_name_addition_time=f"_time_started_{st.session_state.start_time_file_names}",
    )


# Main chat if interview is active
if st.session_state.interview_active:

    if message_respondent := st.chat_input("Your message here"):
        st.session_state.messages.append(
            {"role": "user", "content": message_respondent}
        )

        with st.chat_message("user", avatar=config.AVATAR_RESPONDENT):
            st.markdown(message_respondent)

        with st.chat_message("assistant", avatar=config.AVATAR_INTERVIEWER):

            message_placeholder = st.empty()
            message_interviewer = ""

            if api == "openai":
                stream = client.chat.completions.create(**api_kwargs)
                for message in stream:
                    text_delta = message.choices[0].delta.content
                    if text_delta is not None:
                        message_interviewer += text_delta
                    if len(message_interviewer) > 5:
                        message_placeholder.markdown(message_interviewer + "▌")
                    if any(code in message_interviewer for code in config.CLOSING_MESSAGES.keys()):
                        message_placeholder.empty()
                        break

            elif api == "anthropic":
                with client.messages.stream(**api_kwargs) as stream:
                    for text_delta in stream.text_stream:
                        if text_delta is not None:
                            message_interviewer += text_delta
                        if len(message_interviewer) > 5:
                            message_placeholder.markdown(message_interviewer + "▌")
                        if any(code in message_interviewer for code in config.CLOSING_MESSAGES.keys()):
                            message_placeholder.empty()
                            break

            elif api == "mistral":
                response = client.chat.complete(
                    model=config.MODEL,
                    messages=st.session_state.messages,
                    max_tokens=config.MAX_OUTPUT_TOKENS,
                )
                message_interviewer = response.choices[0].message.content
                if not any(code in message_interviewer for code in config.CLOSING_MESSAGES.keys()):
                    message_placeholder.markdown(message_interviewer)
                else:
                    message_placeholder.empty()

            # No code — display and store normally
            if not any(code in message_interviewer for code in config.CLOSING_MESSAGES.keys()):
                if api != "mistral":
                    message_placeholder.markdown(message_interviewer)
                st.session_state.messages.append(
                    {"role": "assistant", "content": message_interviewer}
                )
                try:
                    save_interview_data(
                        username=st.session_state.username,
                        transcripts_directory=config.BACKUPS_DIRECTORY,
                        times_directory=config.BACKUPS_DIRECTORY,
                        file_name_addition_transcript=f"_transcript_started_{st.session_state.start_time_file_names}",
                        file_name_addition_time=f"_time_started_{st.session_state.start_time_file_names}",
                    )
                except:
                    pass

            # Code detected — save data and trigger exit page
            for code in config.CLOSING_MESSAGES.keys():
                if code in message_interviewer:
                    st.session_state.messages.append(
                        {"role": "assistant", "content": message_interviewer}
                    )
                    st.session_state.interview_active = False

                    # Store final transcript and save to Google Sheets
                    save_interview_data(
                        username=st.session_state.username,
                        transcripts_directory=config.TRANSCRIPTS_DIRECTORY,
                        times_directory=config.TIMES_DIRECTORY,
                        final=True,
                    )

                    st.session_state.interview_completed = True
                    st.rerun()
