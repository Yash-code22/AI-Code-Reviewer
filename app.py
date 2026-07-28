import json
import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
def calculate_score(review):
    score = 10

    score -= len(review.get("bugs", [])) * 2
    score -= len(review.get("security", [])) * 2
    score -= len(review.get("performance", []))
    score -= min(len(review.get("best_practices", [])), 2)

    return max(0, min(score, 10))

def create_pdf(review):

    score = calculate_score(review)

    buffer = io.BytesIO()

    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph("AI Code Review Report", styles["Title"])
    )

    content.append(Spacer(1, 12))


    content.append(
        Paragraph(
            f"Code Quality Score: {score}/10",
            styles["Normal"]
        )
    )

    content.append(Spacer(1, 12))


    sections = [
        ("Summary", review.get("summary", "")),
        ("Bugs", review.get("bugs", [])),
        ("Improvements", review.get("improvements", [])),
        ("Performance", review.get("performance", [])),
        ("Security", review.get("security", [])),
        ("Best Practices", review.get("best_practices", []))
    ]


    for title, data in sections:

        content.append(
            Paragraph(title, styles["Heading2"])
        )

        if isinstance(data, list):

            if data:
                for item in data:
                    content.append(
                        Paragraph(
                            "• " + item,
                            styles["Normal"]
                        )
                    )
            else:
                content.append(
                    Paragraph(
                        "• No issues found.",
                        styles["Normal"]
                    )
                )

        else:
            content.append(
                Paragraph(
                    data,
                    styles["Normal"]
                )
            )

        content.append(Spacer(1, 12))


    doc.build(content)

    buffer.seek(0)

    return buffer

# Load API Key
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=api_key)
MODEL_NAME = "gemini-3.5-flash"

st.set_page_config(
    page_title="AI Code Reviewer",
    page_icon="🤖",
    layout="wide"
)

st.markdown("""
<style>
.main-title{
    font-size:70px !important;
    font-weight:900;
    text-align:center;
    line-height:1.2;
    background: linear-gradient(90deg,#4F46E5,#06B6D4);
    -webkit-background-clip:text;
    -webkit-text-fill-color:transparent;
    margin-bottom:5px;
}
.subtitle{
    text-align:center;
    color:#9CA3AF;
    font-size:18px;
    margin-bottom:30px;
}
.card{
    padding:20px;
    border-radius:15px;
    background:#111827;
    box-shadow:0px 4px 20px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    '<h1 class="main-title">🤖 AI Code Reviewer</h1>',
    unsafe_allow_html=True
)

st.markdown(
    '<p class="subtitle">AI-Powered Code Analysis using Gemini</p>',
    unsafe_allow_html=True
)

# File Upload Feature
uploaded_file = st.file_uploader(
    "📂 Upload Code File",
    type=["py", "java", "cpp", "js", "txt", "cs"]
)

if "review" not in st.session_state:
    st.session_state.review = None

if "code" not in st.session_state:
    st.session_state.code = ""


if uploaded_file is not None:
    code = uploaded_file.read().decode("utf-8")

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    with st.expander("View Uploaded Code"):
        st.code(code)


else:
    code = st.text_area(
        "Paste your code here",
        height=300
    )


if st.button("Review Code"):

    if code.strip() == "":
        st.warning("Please upload a file or paste some code first.")

    else:

        prompt = f"""
You are an expert Software Engineer.

Review the following code.

Return ONLY valid JSON.

Do not add markdown.
Do not add ```.

Use this exact structure:

{{
  "summary": "",
  "bugs": [],
  "improvements": [],
  "performance": [],
  "security": [],
  "best_practices": []
}}

Analyze the following code:


Code:

{code}
"""


        try:
            with st.spinner("Reviewing code..."):
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt
                )

        except Exception as e:
            error_message = str(e)

            if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                st.error("⚠️ Gemini API quota exceeded.")
                st.info(
                    "Free Gemini API limit has ended.\n\n"
                    "• Please try again later\n"
                    "• Or use new project/API key"
                )
            else:
                st.error(f"Error: {error_message}")

            st.stop()


        


        if hasattr(response, "text") and response.text:
            clean_response = response.text.replace("```json", "").replace("```", "").strip()

            try:
                review = json.loads(clean_response)
                # st.json(review)
                st.session_state.review = review
                st.session_state.code = code

                st.success("Review Complete!")

            except json.JSONDecodeError:
                st.error("AI returned invalid JSON. Please try again.")
                st.write(response.text)
                st.stop()

        else:
            st.error("No response received from AI.")
            st.stop()

            


if st.session_state.review is not None:

    review = st.session_state.review
    code = st.session_state.code
    st.subheader("📊 Code Review Dashboard")
    st.caption("AI-generated analysis of your source code")


    # Score Validation
    score = calculate_score(review)


    # ⭐ Star Rating
    stars = "⭐" * int(score) + "☆" * (10 - int(score))


    st.write("### ⭐ Code Quality Score")

    col1, col2 = st.columns(2)


    with col1:
        st.metric(
            label="⭐ Quality Score",
            value=f"{score}/10"
        )


    with col2:
        st.markdown(f"### {stars}")


    # Progress Bar
    st.progress(score / 10)
    if score >= 8:
        st.success("🏆 Excellent Code Quality")
    elif score >= 6:
        st.warning("👍 Good Code - Some Improvements Needed")
    else:
        st.error("⚠️ Poor Code Quality")


    st.divider()


    # Summary Card
    st.write("### 📝 Summary")

    st.info(review.get("summary", "No summary available."))

    st.divider()


    # Three Cards
    col1, col2, col3 = st.columns(3)


    with col1:
        st.write("🐞 Bugs")
        st.metric(
            "Issues Found",
            len(review["bugs"])
        )


    with col2:
        st.write("🔐 Security")
        if len(review["security"]) == 0:
            st.success("Safe")
        else:
            st.warning("Review Needed")


    with col3:
        st.write("⚡ Performance")
        if len(review["performance"]) == 0:
            st.success("Good")
        else:
            st.warning("Needs Improvement")

    st.subheader("🐞 Bugs")

    if review["bugs"]:
        for bug in review["bugs"]:
            st.info(bug)
    else:
        st.success("No bugs found 🎉")

    st.subheader("💡 Improvements")

    if review["improvements"]:
        for item in review["improvements"]:
            st.info(item)
    else:
        st.success("No improvements suggested.")

    st.subheader("⚡ Performance")

    if review["performance"]:
        for item in review["performance"]:
            st.info(item)
    else:
        st.success("Performance looks good.")

    st.subheader("🔐 Security")

    if review["security"]:
        for item in review["security"]:
            st.warning(item)
    else:
        st.success("No security issues found.")

    st.subheader("✅ Best Practices")

    if review["best_practices"]:
        for item in review["best_practices"]:
            st.info(item)
    else:
        st.success("Following best practices.")

    st.divider()

    
    pdf = create_pdf(review)

    st.download_button(
        label="⬇ Download Review Report",
        data=pdf,
        file_name="AI_Code_Review_Report.pdf",
        mime="application/pdf"
    )


    st.divider()

    st.subheader("💬 Chat with Your Code")

    question = st.text_input(
        "💬 Ask anything about your code..."
    )

    if st.button("Ask AI"):

        if question.strip() == "":
            st.warning("Please ask a question.")
        else:

            chat_prompt = f"""
            You are an expert Software Engineer.

            This is the user's code:

            {st.session_state.code}

            This is the AI review:

            {json.dumps(st.session_state.review, indent=2)}

            Now answer this question:

            {question}
            """

            try:
                with st.spinner("Thinking..."):
                    chat_response = client.models.generate_content(
                        model=MODEL_NAME,
                        contents=chat_prompt
                    )

                if hasattr(chat_response, "text") and chat_response.text:
                    st.write("### 🤖 AI Answer")
                    st.markdown(chat_response.text)
                else:
                    st.error("No response received from AI.")

            except Exception as e:
                error_message = str(e)

                if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
                    st.error("⚠️ Gemini API quota exceeded.")
                    st.info("Free quota khatam ho gaya hai. Thodi der baad try karein ya naya API key/project use karein.")
                else:
                    st.error(f"Error: {error_message}")

                st.stop()

    