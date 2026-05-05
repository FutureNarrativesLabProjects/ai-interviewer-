import streamlit as st
import time
import uuid
from utils import (
    check_password,
    check_if_interview_completed,
    save_interview_data,
)
import os
import base64
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
if "demographics_submitted" not in st.session_state:
    st.session_state.demographics_submitted = False
if "demographics" not in st.session_state:
    st.session_state.demographics = {}
if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False
# Exit page — shown after interview is fully completed
if st.session_state.interview_completed:
    st.markdown(
        """
        <div style="text-align: center; padding: 80px 20px;">
            <h2 style="font-size: 2rem; font-weight: 600; margin-bottom: 1rem;">Thank you for completing the interview</h2>
            <p style="font-size: 1.15rem; color: #555; max-width: 500px; margin: 0 auto;">
                Your reflections will play an important part in shaping London Play's next strategy. We really appreciate your time.
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
        # Custom CSS — bigger button, centred radio buttons
        st.markdown(
            """
            <style>
            div[data-testid="stButton"] > button {
                height: 3.2rem;
                font-size: 1.1rem;
                font-weight: 600;
            }
            div[data-testid="stRadio"] > div {
                justify-content: center;
            }
</style>
            """,
            unsafe_allow_html=True,
        )

        img_dir = os.path.join(os.path.dirname(__file__), "images")

        # Title
        st.markdown(
            "<h2 style='text-align: center; font-size: 1.8rem; font-weight: 600; margin-bottom: 1rem;'>"
            "London Play Strategy Interview</h2>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Start the Interview", use_container_width=True, type="primary"):
                landing.empty()
                st.session_state.entered = True
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Data notice
        st.markdown("**Your data**")
        st.markdown(
            """
- **Anonymous** — no name, email, or personal details are collected at any point
- **Not used to train AI** — the AI provider does not train its models on your responses
- **Who sees your responses** — London Play and Future Narratives Lab will receive anonymised findings
- **Withdrawal** — you can stop at any time before the interview concludes; once complete, responses cannot be individually removed as they are fully anonymous
"""
        )

        # Collapsed FAQs
        with st.expander("More information"):
            st.markdown(
                """
**Is this really anonymous?**
Yes. The only thing stored alongside your responses is a randomly generated session code — no name, email address, or any personal detail is collected or recorded at any point.

**Will my responses be used to train AI?**
No. The AI that powers this interview is provided by Mistral AI, a French company based in Paris. As an EU-based provider, Mistral is GDPR compliant and does not train its models on data submitted via its API.

**Who is running this research?**
This interview is run by Future Narratives Lab, in partnership with King's College London, for London Play, to gather trustee reflections ahead of the strategy away day.

**Can I stop partway through?**
Yes — click the **Quit button** at any time. This will end the interview and your responses will not be recorded. Note: if you tell the interviewer you wish to stop, the conversation will be saved as a completed interview.

**Can I have my data deleted?**
Once the interview is complete, it is not possible to remove your individual responses. Because the data is fully anonymous, there is no way to identify which responses belong to you. Raw interview transcripts will be deleted by 30 September 2026. Anonymised findings and analysis drawn from the research may be retained and used in published outputs.

**What if I have concerns about AI use?**
We want to hear that too — your critique is a valid and valuable perspective. You can also contact us at info@futurenarrativeslab.org

**Who do I contact with questions?**
Contact us at info@futurenarrativeslab.org
"""
            )

        st.markdown("<br><br>", unsafe_allow_html=True)

        # Logos — small row at bottom, centred
        def img_b64(path, mime):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode(), mime

        kings_b64, kings_mime = img_b64(os.path.join(img_dir, "logo-kings.png"), "image/png")
        lp_b64, lp_mime = img_b64(os.path.join(img_dir, "logo-london-play.gif"), "image/gif")
        fnl_b64, fnl_mime = img_b64(os.path.join(img_dir, "logo-fnl.png"), "image/png")

        st.markdown(
            f"""
            <div style="display:flex; justify-content:center; align-items:center; gap:40px; margin-top:10px;">
                <img src="data:{kings_mime};base64,{kings_b64}" style="height:65px; width:auto; border-radius:0;">
                <img src="data:{lp_mime};base64,{lp_b64}" style="height:55px; width:auto; border-radius:0;">
                <img src="data:{fnl_mime};base64,{fnl_b64}" style="height:113px; width:auto; border-radius:0;">
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.stop()

# Pre-interview form
if not st.session_state.demographics_submitted:
    st.markdown("### Before we begin")
    st.markdown("Please fill in a few quick details. This takes less than a minute.")
    st.markdown("<br>", unsafe_allow_html=True)

    with st.form("demographics_form"):
        participant_code = st.text_input("Participant code")
        age = st.selectbox(
            "Age range",
            ["Prefer not to say", "Under 18", "18–24", "25–34", "35–44", "45–54", "55–64", "65+"],
        )
        gender = st.selectbox(
            "Gender",
            ["Prefer not to say", "Woman", "Man", "Non-binary", "Self-describe"],
        )
        location = st.text_input("Borough or area you live in")
        ethnicity = st.text_input("Ethnicity (in your own words)")
        submitted = st.form_submit_button("Begin Interview", type="primary")

    if submitted:
        valid_codes = [
            c.strip() for c in st.secrets.get("PARTICIPANT_CODES", "").split(",") if c.strip()
        ]
        if not participant_code:
            st.error("Please enter your participant code.")
        elif valid_codes and participant_code not in valid_codes:
            st.error("That code wasn't recognised. Please check your code and try again.")
        else:
            st.session_state.demographics = {
                "participant_code": participant_code,
                "age": age,
                "gender": gender,
                "location": location,
                "ethnicity": ethnicity,
            }
            st.session_state.demographics_submitted = True
            st.rerun()
    st.stop()

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

                    # Display closing message in chat
                    closing_message = config.CLOSING_MESSAGES[code]
                    st.markdown(closing_message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": closing_message}
                    )

                    # Store final transcript and save to Google Sheets
                    completion_status = "Complete" if code == "x7y8" else "Terminated"
                    save_interview_data(
                        username=st.session_state.username,
                        transcripts_directory=config.TRANSCRIPTS_DIRECTORY,
                        times_directory=config.TIMES_DIRECTORY,
                        final=True,
                        completion_status=completion_status,
                    )

                    st.session_state.interview_completed = True

# Show continue button after interview completes
if st.session_state.get("interview_completed") and not st.session_state.get("interview_active"):
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("Continue", use_container_width=True, type="primary"):
            st.rerun()
