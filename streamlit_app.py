import streamlit as st
from openai import OpenAI
import math
import datetime

st.markdown("""
<style>

div[data-testid="stRadio"] label p {font-size: 16px;}
div[data-testid="stNumberInput"] input {font-size: 16px;}
div[data-testid="stMarkdownContainer"] p {font-size: 16px;}

section[data-testid="stSidebar"] {background-color: #F0F2F6;}
[data-testid="stAppViewContainer"] {background-color: #e0fbfc;}
div[data-testid="stVerticalBlockBorderWrapper"] {background-color: #FFFFFF;}
div[data-testid="stForm"] {background-color: #FFFFFF !important;}

</style>
""", unsafe_allow_html=True)

APP_TITLE = "Meno Buddy"
APP_CAPTION = "Help you "

MODEL = "gemini-3.5-flash-lite"
QUESTION_MODEL = "gemini-3.5-flash-lite"

SYSTEM_PROMPT = """
You are an healthcare assistant.
"""

CHAT_GREETING = "Hi"

BACKUP_QUESTIONS = ["What does this page show?"]

OPTIONS_4 = {
    "0": 0,
    "1": 1,
    "2": 2,
    "3": 3,
    }

OPTIONS_2 = {
    "Yes": 1,
    "No": 0,
    }

INTERCEPT = -3.21874
COEFF = {
    "age": 0.0369965,
    "BMI": 0.0337405,
    "mood_0": -0.727168,
    "mood_1": 0.727221,
    "physical_activity_0": 0.198725,
    "physical_activity_1": -0.198672,
    "num_hotflush": 0.133809,
    }

FACTOR = {
    "age": "Age",
    "BMI": "BMI",
    "mood": "Mood",
    "activity": "Physical activity",
    "num_hotflush": "Number of hot flushes",
}

client = OpenAI(
    api_key=st.secrets["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

st.set_page_config(page_title=APP_TITLE, page_icon="💬")

def show_question(text):
    st.write(text)

def number_question(text, key):
    show_question(text)
    return st.number_input(text, value=None, key=key, label_visibility="collapsed")

def radio_question(text, options, key):
    show_question(text)
    return st.radio(text, options, index=None, key=key, label_visibility="collapsed")

def predict(answer):
    contribution = {name: coeff * answer[name] for name, coeff in COEFF.items()}
    score = INTERCEPT + sum(contribution.values())
    prob = 1 / (1+math.exp(-score)) #sigmoid function
    return prob, contribution

def go_to_chat(question):
    st.session_state["pending_question"] = question
    st.session_state["pending_source"] = st.session_state["page"]
    st.session_state["page"] = "Ask Meno Buddy"

def ask_buddy(label, question, key):
    st.button(label, key=key, on_click=go_to_chat, args=(question,))

def send_typed_question(text_key):
    text = st.session_state[text_key].strip()
    if text != "":
        go_to_chat(text)
        st.session_state[text_key] = ""

@st.cache_data(show_spinner=False)
def make_questions(page_content):
    request = (
        f"A user is looking at one page of a health information website for postmenopausal women."
        "Here is the content of the page:" + page_content + "Suggest 4 short questions (under 10 words each) that this user might want to ask an assistant about what is on this page."
        "Only suggest questions about general information, not diagnosis or treatment."
        "Reply with one question per line, no numbering, no extra text."
    )
    result = client.chat.completions.create(
        model=QUESTION_MODEL,
        messages=[{"role": "user", "content": request}],
    )
    lines = result.choices[0].message.content.strip().split("\n")

    questions = []
    for line in lines:
        line = line.strip().lstrip("-*0123456789. ").strip('"')
        if line != "":
            questions.append(line)
    if len(questions) == 0:
        raise ValueError("no questions generated")
    return questions[:4]

def ask_buddy_panel(page_content, prefix):
    with st.spinner("Thinking of questions..."):
        try:
            questions = make_questions(page_content)
        except Exception as error:
            st.warning(f"AI could not generate questions, using backup. Reason: {error}")
            questions = BACKUP_QUESTIONS

    with st.container(border=True, key=f"buddy_{prefix}"):
        st.subheader("Ask Meno Buddy about this page")

        left_col, right_col = st.columns(2)
        for i, question in enumerate(questions):
            if i % 2 == 0:
                with left_col:
                    ask_buddy(question, question, key=f"{prefix}_{i}")
            else:
                with right_col:
                    ask_buddy(question, question, key=f"{prefix}_{i}")
        text_key = f"{prefix}_text"
        input_col, button_col = st.columns([5, 1])
        
        with input_col:
            st.text_input(
                "Your question",
                key=text_key,
                placeholder="Or type your own question...",
                label_visibility="collapsed",
            )
        with button_col:
            st.button(
                "Ask",
                key=f"{prefix}_ask",
                on_click=send_typed_question,
                args=(text_key,),
            )

def show_message(message):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        source = message.get("source")
        if source is not None and source != "Ask Meno Buddy":
            st.caption(f"Sent from a button on {source}")

with st.sidebar:
    st.title(APP_TITLE)
    st.caption(APP_CAPTION)
    page = st.radio("Menu", ["Fill in the form", "My results", "Summary", "Ask Meno Buddy", "About"], 
                    key="page", label_visibility="collapsed",
    )
# ---------------------------------------------------------------

# Form
if page == "Fill in the form":
    st.title("Fill in the form")

    with st.form("Form"):
        age = number_question("1. How old are you?", key="age")
        st.write("")
        height = number_question("2. What is your height in cm?", key="height")
        st.write("")
        weight = number_question("3. What is your weight in kg?", key="weight")
        st.write("")
        st.write("4. Over the last two weeks, how often have you been bothered by the following problem?")
        mood_1 = radio_question("Little interst or pleasure in doing things.", list(OPTIONS_4.keys()), key="mood_1")
        mood_2 = radio_question("Feeling down, depressed, or hopeless.", list(OPTIONS_4.keys()), key="mood_2")
        st.write("")
        physical = radio_question("5. Are you physically active?", list(OPTIONS_2.keys()), key="physical")
        st.write("")
        num_hotflush = number_question("6. Over the past week, how many hot flushes have you had?", key="num_hotflush")
        st.write("")

        submitted = st.form_submit_button("See my results")

    if submitted:
        if age is None or height is None or weight is None or mood_1 is None or mood_2 is None or physical is None or num_hotflush is None:
            st.warning("Please answer all the questions")
        else:
            mood_total = OPTIONS_4[mood_1] + OPTIONS_4[mood_2]
            mood_flag = 1 if (OPTIONS_4[mood_1] + OPTIONS_4[mood_2]) >= 3 else 0
            physical_activity = OPTIONS_2[physical]
            bmi = round(weight / ((height/100)**2), 1)
            st.session_state["answers"] = {
                "age": age,
                "BMI": bmi,
                "mood_0": 1 if mood_flag == 0 else 0,
                "mood_1": 1 if mood_flag == 1 else 0,
                "mood_total": mood_total,
                "physical_activity_0": 1 if physical_activity == 0 else 0,
                "physical_activity_1": 1 if physical_activity == 1 else 0,
                "num_hotflush": num_hotflush,
                }

            st.success("Form submitted. Please view 'My Results'")
            
    form_content = "A form with questions about age, height, weight, mood, physical activity and hot flushes"
    ask_buddy_panel(form_content, "form")

# Result
elif page == "My results":
    st.title("My results")
    if "answers" not in st.session_state:
        st.info("Please fill in the form first")
    else:
        answer = st.session_state["answers"]
        prob, contribution = predict(answer)

        st.metric("Probability of having a bad sleep", f"{prob:.0%}")

        contribution["mood"] = contribution.pop("mood_0") + contribution.pop("mood_1")
        contribution["physical_activity"] = contribution.pop("physical_activity_0") + contribution.pop("physical_activity_1")
        st.bar_chart(contribution, horizontal=True)

        top_factor = max(contribution, key=contribution.get)
        with st.container(border=True):
            st.subheader("Main factor: ")
            if contribution[top_factor] > 0:
                st.markdown(f"**{FACTOR[top_factor]}**")
            else:
                st.write("No single factor stands out in your answers.")

        factor_text = FACTOR[top_factor] if contribution[top_factor] > 0 else "none stands out"     
        ask_buddy_panel(
            f"Results page. Estimated likelihood of poor sleep: {prob:.0%}. "
            f"Main factor: {factor_text}. "
            "The page also shows a chart of how each factor affects the result.",
            "results",
        )

# Summary
elif page == "Summary":
    st.title("Summary")
    st.write("This summary was generated from a self-completed questionnaire to help you describe your symptoms clearly to your doctor and discuss what support may be right for you. It is not a diagnosis.")

    if "answers" not in st.session_state:
        st.info("Please fill in the form first")
    else:
        answer = st.session_state["answers"]
        prob, contribution = predict(answer)
        mood_total = answer["mood_total"]
        mood_note = "above screening shreshold" if mood_total >= 3 else "below the screening threshold"
        physical_note = "No" if answer["physical_activity_0"] == 1 else "Yes"

        note = st.text_area("What else do you want to inform your doctor?")

        summary = f"""
        **date** {datetime.date.today(): %d %B %Y}

        ### Background
        - **Age:** {answer["age"]}
        - **Physically active:** {physical_note}
        - **BMI:** {answer["BMI"]}
        
        ### Related factors
        - **Mood (PHQ-2):** {mood_total}/6, {mood_note}
        - **Number of hot flushes:** {answer["num_hotflush"]}
        
        ### Estimated likelihood
        - **Result description:** {prob:.0%} estimated likelihood of poor sleep quality, based on research data (not a diagnosis).
        
        ### Additional notes from you
        {note if note else "None"}
        """

        st.markdown(summary)
        st.download_button("Download summary", data=summary, file_name="meno_buddy_summary.txt",)

        ask_buddy_panel(
            f"Summary page for the user's doctor. Estimated likelihood of poor "
            f"sleep: {prob:.0%}. Mood score {mood_total}/6 ({mood_note}). "
            f"Hot flushes in the past week: {answer['num_hotflush']}. "
            f"Physically active: {physical_note}.",
            "summary",
        )

# Ask Meno Buddy
elif page == "Ask Meno Buddy":
    st.title("Ask Meno Buddy")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "assistant", "content": CHAT_GREETING},
        ]

    # History
    for message in st.session_state.messages:
        if message["role"] == "system":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Ask anything")
    if "pending_question" in st.session_state:
        prompt = st.session_state.pop("pending_question")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        stream = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})

# About
elif page == "About":
    st.title("About")
    st.write("Source")

