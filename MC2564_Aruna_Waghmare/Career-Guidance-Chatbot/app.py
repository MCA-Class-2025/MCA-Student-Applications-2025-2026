import streamlit as st
import requests
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from resume_analyzer import analyze_resume
from career_recommender import recommend_career
from github_api import (
    get_github_profile,
    get_github_repositories
)
from books_api import search_books
from youtube_api import search_youtube
import os
from jobs_api import search_jobs
from research_api import search_research
# ----------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------

st.set_page_config(
    page_title="IT Career Guidance Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------------------------
# CUSTOM CSS
# ----------------------------------------------------

st.markdown("""
<style>

#MainMenu{
visibility:hidden;
}

footer{
visibility:hidden;
}



/* Main background */

.stApp{
background:#F4F7FB;
}

/* Sidebar */

section[data-testid="stSidebar"]{
background:#0F172A;
}

section[data-testid="stSidebar"] *{
color:white;
}

/* Hero */

.hero{

background:linear-gradient(90deg,#2563EB,#06B6D4);

padding:35px;

border-radius:18px;

color:white;

text-align:center;

margin-bottom:25px;

}

.hero h1{

font-size:42px;

margin-bottom:10px;

}

.hero p{

font-size:18px;

}

/* Cards */

.card{

background:white;

padding:20px;

border-radius:15px;

box-shadow:0 5px 15px rgba(0,0,0,.08);

text-align:center;

height:190px;

}

/* Metric */

[data-testid="metric-container"]{

background:white;

padding:15px;

border-radius:12px;

box-shadow:0 3px 10px rgba(0,0,0,.08);

}

/* Buttons */

.stButton>button{

width:100%;

height:45px;

background:#2563EB;

color:white;

border:none;

border-radius:10px;

font-size:16px;

font-weight:bold;

}

.stButton>button:hover{

background:#1D4ED8;

}

/* Chat */

[data-testid="stChatMessage"]{

border-radius:15px;

padding:10px;

background:white;

}

</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# LOAD VECTOR DATABASE
# ----------------------------------------------------

@st.cache_resource
def load_vectorstore():

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return FAISS.load_local(
        "faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )

# ----------------------------------------------------
# LOAD OLLAMA
# ----------------------------------------------------

@st.cache_resource
def load_llm():

    return OllamaLLM(
        model="phi3",
        temperature=0.2
    )

try:

    vectorstore = load_vectorstore()
    llm = load_llm()

except Exception as e:

    st.error(e)
    st.stop()

# ----------------------------------------------------
# SIDEBAR
# ----------------------------------------------------

st.sidebar.image(
    "https://cdn-icons-png.flaticon.com/512/3135/3135715.png",
    width=110
)

st.sidebar.title("AI Career Assistant")

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "",
    [
        "🏠 Home",
        "💬 Chatbot",
        "📄 Resume Analyzer",
        "🎯 Career Recommendation",
        "👨‍💻 GitHub Analyzer",
        "📚 Career Books",
        "🎥 Learning Videos",
        "💼 Live IT Jobs",
        "🔬 Research Papers",
        "⚙️ Career Tools"
    ]
)
st.sidebar.markdown("---")

st.sidebar.success("RAG + FAISS + Ollama")

# ----------------------------------------------------
# HOME PAGE
# ----------------------------------------------------

if page == "🏠 Home":

    st.markdown("""

    <div class="hero">

    <h1>🎓 IT Career Guidance Assistant</h1>

    <p>

    Discover career paths, analyze resumes,

    identify skill gaps and get AI-powered

    recommendations using Retrieval-Augmented Generation.

    </p>

    </div>

    """, unsafe_allow_html=True)

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric("Career Records", "4274")

    with m2:
        st.metric("Job Roles", "493")

    with m3:
        st.metric("Resume Samples", "400")

    with m4:
        st.metric("AI Model", "Phi-3")

    st.write("")
    st.write("")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown("""

        <div class="card">

        <h2>💬 AI Chatbot</h2>

        <hr>

        Ask career-related questions

        <br><br>

        ✔ Job Roles

        <br>

        ✔ Skills

        <br>

        ✔ Certifications

        <br>

        ✔ Career Paths

        </div>

        """, unsafe_allow_html=True)

    with c2:

        st.markdown("""

        <div class="card">

        <h2>📄 Resume Analyzer</h2>

        <hr>

        Upload your resume

        <br><br>

        ✔ Detect Skills

        <br>

        ✔ Career Match

        <br>

        ✔ Job Suggestions

        </div>

        """, unsafe_allow_html=True)

    with c3:

        st.markdown("""

        <div class="card">

        <h2>🎯 Recommendation</h2>

        <hr>

        Personalized recommendations

        <br><br>

        ✔ Education

        <br>

        ✔ Interests

        <br>

        ✔ Experience

        </div>

        """, unsafe_allow_html=True)
        # ----------------------------------------------------
# PROMPT TEMPLATE
# ----------------------------------------------------

prompt = PromptTemplate(

    input_variables=[
        "context",
        "question"
    ],

    template="""

You are an AI Career Guidance Assistant.

Answer ONLY from the given context.

If the answer is not available in the context, reply:

"I couldn't find enough information in my knowledge base."

Keep answers clear, professional and easy to understand.

Context:
{context}

Question:
{question}

Answer:

"""
)

# ----------------------------------------------------
# CHATBOT PAGE
# ----------------------------------------------------

if page == "💬 Chatbot":

    st.title("💬 AI Career Guidance Chatbot")

    st.write(
        "Ask anything about IT careers, skills, certifications and job roles."
    )

    # Session State

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous chat

    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    # Chat Input

    question = st.chat_input(
        "Type your career question..."
    )

    if question:

        # User Message

        st.session_state.messages.append(
            {
                "role":"user",
                "content":question
            }
        )

        with st.chat_message("user"):

            st.markdown(question)

        # Retrieve Documents

        retriever = vectorstore.as_retriever(

            search_kwargs={
                "k":4
            }

        )

        docs = retriever.invoke(question)

        context = "\n\n".join(

            doc.page_content

            for doc in docs

        )

        # Prompt

        final_prompt = prompt.format(

            context=context,

            question=question

        )

        # AI Response

        with st.chat_message("assistant"):

            with st.spinner("🔍 Searching knowledge base..."):

                response = llm.invoke(final_prompt)

            st.markdown(response)

            st.markdown("### 📚 Reference Documents")

            for i, doc in enumerate(docs):

                with st.expander(f"Source {i+1}"):

                    st.write(doc.page_content)

        # Save Assistant Response

        st.session_state.messages.append(

            {

                "role":"assistant",

                "content":response

            }

        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button("🗑 Clear Chat"):

            st.session_state.messages = []

            st.rerun()

    with col2:

        st.download_button(

            label="📥 Download Chat",

            data="\n\n".join(

                [

                    f"{m['role'].upper()}:\n{m['content']}"

                    for m in st.session_state.messages

                ]

            ),

            file_name="career_chat.txt",

            mime="text/plain"

        )
        # ----------------------------------------------------
# RESUME ANALYZER
# ----------------------------------------------------

if page == "📄 Resume Analyzer":

    st.title("📄 AI Resume Analyzer")

    st.write(
        "Upload your resume and get AI-powered career recommendations."
    )

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"]
    )

    if uploaded_file:

        with st.spinner("Analyzing Resume..."):

            result = analyze_resume(uploaded_file)

        skills = result["skills"]

        resume_text = result["resume_text"]

        st.success("Resume analyzed successfully!")

        # -------------------------
        # Resume Overview
        # -------------------------

        c1, c2 = st.columns(2)

        with c1:

            st.subheader("📌 Skills Detected")

            if skills:

                for skill in skills:
                    st.success(skill)

            else:
                st.warning("No skills detected.")

        with c2:

            match_score = min(len(skills) * 8, 100)

            st.subheader("📊 Resume Match Score")

            st.progress(match_score)

            st.metric(
                "Match",
                f"{match_score}%"
            )

        st.divider()

        # -------------------------
        # Career Recommendation
        # -------------------------

        query = (
            "Suggest IT careers for these skills: "
            + ", ".join(skills)
        )

        recommendations = recommend_career(
            vectorstore,
            query
        )

        st.subheader("🎯 Recommended Careers")

        for i, career in enumerate(recommendations):

            with st.expander(f"Career {i+1}"):

                st.write(career)

        st.divider()

        # -------------------------
        # Skill Gap Analysis
        # -------------------------

        required_skills = [

            "Python",
            "SQL",
            "Machine Learning",
            "Data Analysis",
            "Git",
            "Cloud",
            "Docker"

        ]

        missing = []

        for skill in required_skills:

            if skill.lower() not in [

                s.lower()

                for s in skills

            ]:

                missing.append(skill)

        st.subheader("❌ Missing Skills")

        if missing:

            for skill in missing:

                st.error(skill)

        else:

            st.success(
                "Excellent! No major skill gaps found."
            )

        st.divider()

        # -------------------------
        # Resume Summary
        # -------------------------

        st.subheader("📄 Resume Preview")

        st.text_area(

            "Extracted Text",

            resume_text[:3000],

            height=250

        )

        st.download_button(

            "📥 Download Resume Text",

            resume_text,

            file_name="resume_text.txt",

            mime="text/plain"

        )
        # ----------------------------------------------------
# CAREER RECOMMENDATION
# ----------------------------------------------------

if page == "🎯 Career Recommendation":

    st.title("🎯 AI Career Recommendation")

    st.write(
        "Fill your profile and receive personalized career recommendations."
    )

    col1, col2 = st.columns(2)

    with col1:

        education = st.selectbox(

            "Education",

            [

                "BCA",

                "B.Sc Computer Science",

                "MCA",

                "B.Tech",

                "M.Tech"

            ]

        )

    with col2:

        experience = st.selectbox(

            "Experience",

            [

                "Fresher",

                "1-3 Years",

                "3-5 Years",

                "5+ Years"

            ]

        )

    skills = st.text_area(

        "Skills (comma separated)",

        placeholder="Python, SQL, React, Machine Learning"

    )

    interests = st.multiselect(

        "Areas of Interest",

        [

            "Artificial Intelligence",

            "Data Science",

            "Web Development",

            "Cloud Computing",

            "Cyber Security",

            "Software Development",

            "Data Analytics"

        ]

    )

    if st.button("🚀 Generate Career Recommendation"):

        profile = f"""

        Education: {education}

        Skills: {skills}

        Interests: {', '.join(interests)}

        Experience: {experience}

        """

        recommendations = recommend_career(
            vectorstore,
            profile
        )

        top_result = recommendations[0]

        skill_count = len(
            [
                s for s in skills.split(",")
                if s.strip()
            ]
        )

        match_score = min(55 + skill_count * 8, 98)

        st.success("Recommendation Generated Successfully!")

        st.subheader("⭐ Career Match")

        st.progress(match_score)

        st.metric(

            "Match Score",

            f"{match_score}%"

        )

        st.divider()

        st.subheader("🎯 Recommended Career")

        st.info(top_result[:900])

        st.divider()

        st.subheader("📚 Learning Roadmap")

        roadmap = [

            "✔ Strengthen Programming Fundamentals",

            "✔ Master Data Structures & Algorithms",

            "✔ Build 3-5 Real Projects",

            "✔ Learn Git & GitHub",

            "✔ Practice Interview Questions",

            "✔ Build an ATS-Friendly Resume"

        ]

        for step in roadmap:

            st.write(step)

        st.divider()

        st.subheader("📜 Recommended Certifications")

        certs = [

            "Google AI Essentials",

            "AWS Cloud Practitioner",

            "Microsoft Azure AI Fundamentals",

            "IBM Data Science Professional",

            "Oracle Java Certification"

        ]

        for cert in certs:

            st.success(cert)

        st.divider()

        st.subheader("💰 Estimated Salary (India)")

        salary = {

            "Fresher": "₹4 – ₹8 LPA",

            "1-3 Years": "₹8 – ₹15 LPA",

            "3-5 Years": "₹15 – ₹25 LPA",

            "5+ Years": "₹25+ LPA"

        }

        st.metric(

            "Expected Salary",

            salary[experience]

        )

        st.divider()

        st.subheader("📖 Top Matching Knowledge Base Results")

        for i, rec in enumerate(recommendations):

            with st.expander(

                f"Recommendation {i+1}"

            ):

                st.write(rec) 
# ----------------------------------------------------
# GITHUB ANALYZER
# ----------------------------------------------------

if page == "👨‍💻 GitHub Analyzer":

    st.title("👨‍💻 GitHub Profile Analyzer")

    st.write(
        "Analyze a public GitHub profile and explore repositories, "
        "programming languages and developer activity."
    )

    username = st.text_input(
        "GitHub Username",
        placeholder="Enter GitHub username"
    )

    if st.button("🔍 Analyze GitHub Profile"):

        if not username.strip():

            st.warning("Please enter a GitHub username.")

        else:

            with st.spinner("Fetching GitHub profile..."):

                profile = get_github_profile(
                    username.strip()
                )

            if not profile["success"]:

                st.error(profile["message"])

            else:

                st.success(
                    "GitHub profile loaded successfully!"
                )

                # --------------------------------
                # PROFILE
                # --------------------------------

                st.subheader("👤 Profile")

                col1, col2 = st.columns([1, 3])

                with col1:

                    if profile["avatar"]:

                        st.image(
                            profile["avatar"],
                            width=150
                        )

                with col2:

                    st.markdown(
                        f"### {profile['name'] or profile['username']}"
                    )

                    st.write(
                        f"**Username:** {profile['username']}"
                    )

                    st.write(
                        f"**Bio:** {profile['bio'] or 'No bio available'}"
                    )

                    st.write(
                        f"**Location:** "
                        f"{profile['location'] or 'Not available'}"
                    )

                    st.link_button(
                        "🔗 Open GitHub Profile",
                        profile["profile_url"]
                    )

                st.divider()

                # --------------------------------
                # METRICS
                # --------------------------------

                c1, c2, c3, c4 = st.columns(4)

                with c1:

                    st.metric(
                        "Repositories",
                        profile["repositories"]
                    )

                with c2:

                    st.metric(
                        "Followers",
                        profile["followers"]
                    )

                with c3:

                    st.metric(
                        "Following",
                        profile["following"]
                    )

                with c4:

                    st.metric(
                        "Account",
                        profile["created_at"][:10]
                    )

                st.divider()

                # --------------------------------
                # REPOSITORIES
                # --------------------------------

                st.subheader("📦 Repositories")

                with st.spinner(
                    "Loading repositories..."
                ):

                    repositories = get_github_repositories(
                        username.strip()
                    )

                if repositories:

                    for repo in repositories[:10]:

                        with st.expander(
                            f"📁 {repo['name']}"
                        ):

                            st.write(
                                repo["description"]
                                or
                                "No description available."
                            )

                            col1, col2, col3 = st.columns(3)

                            with col1:

                                st.write(
                                    f"💻 Language: "
                                    f"{repo['language'] or 'N/A'}"
                                )

                            with col2:

                                st.write(
                                    f"⭐ Stars: "
                                    f"{repo['stars']}"
                                )

                            with col3:

                                st.write(
                                    f"🍴 Forks: "
                                    f"{repo['forks']}"
                                )

                            st.link_button(
                                "View Repository",
                                repo["url"]
                            )

                else:

                    st.info(
                        "No public repositories found."
                    )
# ----------------------------------------------------
# CAREER BOOKS
# ----------------------------------------------------

if page == "📚 Career Books":

    st.title("📚 Career & Technical Books")

    st.write(
        "Search for technical books, programming books "
        "and career-related learning resources."
    )

    query = st.text_input(
        "Search Books",
        placeholder="Example: Python, Data Science, React, SQL"
    )

    if st.button("🔍 Search Books"):

        if not query.strip():

            st.warning(
                "Please enter a topic to search."
            )

        else:

            with st.spinner(
                "Searching Google Books..."
            ):

                result = search_books(
                    query.strip(),
                    max_results=10
                )

            if not result["success"]:

                st.error(
                    result["message"]
                )

            elif not result["books"]:

                st.info(
                    "No books found."
                )

            else:

                st.success(
                    f"Found {len(result['books'])} books!"
                )

                for book in result["books"]:

                    with st.container():

                        col1, col2 = st.columns(
                            [1, 3]
                        )

                        with col1:

                            if book["thumbnail"]:

                                st.image(
                                    book["thumbnail"],
                                    width=130
                                )

                            else:

                                st.write(
                                    "📚 No cover"
                                )

                        with col2:

                            st.subheader(
                                book["title"]
                            )

                            st.write(
                                "**Author:** "
                                +
                                ", ".join(
                                    book["authors"]
                                )
                            )

                            st.write(
                                "**Published:** "
                                +
                                str(
                                    book["published"]
                                )
                            )

                            if book["rating"] != "Not available":

                                st.write(
                                    "⭐ Rating: "
                                    +
                                    str(
                                        book["rating"]
                                    )
                                )

                            description = (
                                book["description"]
                            )

                            if len(description) > 400:

                                description = (
                                    description[:400]
                                    + "..."
                                )

                            st.write(
                                description
                            )

                            if book["link"]:

                                st.link_button(
                                    "📖 View Book",
                                    book["link"]
                                )

                        st.divider() 
# ----------------------------------------------------
# YOUTUBE LEARNING VIDEOS
# ----------------------------------------------------

if page == "🎥 Learning Videos":

    st.title("🎥 IT Learning Videos")

    st.write(
        "Search YouTube for programming, development, "
        "AI, data science and career learning resources."
    )

    query = st.text_input(
        "Search Learning Topic",
        placeholder="Example: Python, DSA, React, Machine Learning"
    )

    if st.button("🔍 Search Videos"):

        if not query.strip():

            st.warning(
                "Please enter a topic."
            )

        else:

            api_key = st.secrets.get(
                "YOUTUBE_API_KEY"
            )

            if not api_key:

                st.error(
                    "YouTube API key is not configured."
                )

            else:

                with st.spinner(
                    "Searching YouTube..."
                ):

                    result = search_youtube(
                        query.strip(),
                        api_key,
                        max_results=10
                    )

                if not result["success"]:

                    st.error(
                        result["message"]
                    )

                else:

                    st.success(
                        f"Found {len(result['videos'])} videos!"
                    )

                    for video in result["videos"]:

                        col1, col2 = st.columns(
                            [1, 2]
                        )

                        with col1:

                            if video["thumbnail"]:

                                st.image(
                                    video["thumbnail"]
                                )

                        with col2:

                            st.subheader(
                                video["title"]
                            )

                            st.write(
                                "📺 Channel: "
                                + video["channel"]
                            )

                            st.write(
                                video["description"][:300]
                                + "..."
                            )

                            st.link_button(
                                "▶ Watch Video",
                                video["url"]
                            )

                        st.divider() 
# ----------------------------------------------------
# LIVE IT JOBS - REMOTIVE API
# ----------------------------------------------------

if page == "💼 Live IT Jobs":

    st.markdown(
    """
    <div class="hero">
        <h1>💼 Remote IT Jobs</h1>
        <p>Find remote IT job opportunities using the Remotive API.</p>
    </div>
    """,
    unsafe_allow_html=True)

    st.write("")

    query = st.text_input(
        "🔍 Search IT Jobs",
        placeholder="Python Developer, React Developer, Data Analyst..."
    )

    if st.button("🚀 Search Jobs"):

        if not query.strip():

            st.warning("Please enter a job role.")

        else:

            with st.spinner("🔎 Searching remote jobs..."):

                result = search_jobs(
                    query=query.strip(),
                    max_results=10
                )

            if not result["success"]:

                st.error(result["message"])

            elif not result["jobs"]:

                st.info("No jobs found.")

            else:

                st.success(
                    f"Found {len(result['jobs'])} jobs!"
                )

                for job in result["jobs"]:

                    st.markdown(
                        """
                        <div style="
                            background:white;
                            padding:22px;
                            margin:15px 0;
                            border-radius:16px;
                            box-shadow:0 4px 15px rgba(0,0,0,0.08);
                            border-left:5px solid #2563EB;
                        ">
                        """,
                        unsafe_allow_html=True
                    )

                    st.subheader(
                        f"💼 {job['title']}"
                    )

                    col1, col2 = st.columns(2)

                    with col1:

                        st.write(
                            f"🏢 **Company:** {job['company']}"
                        )

                    with col2:

                        st.write(
                            f"📍 **Location:** {job['location']}"
                        )

                    st.write(
                        f"💼 **Job Type:** {job['type']}"
                    )

                    description = job["description"]

                    # Remove HTML tags
                    import re

                    description = re.sub(
                        "<.*?>",
                        " ",
                        description
                    )

                    if len(description) > 500:

                        description = (
                            description[:500] + "..."
                        )

                    st.write(description)

                    if job["apply_link"]:

                        st.link_button(
                            "🚀 View / Apply",
                            job["apply_link"]
                        )

                    st.markdown(
                        "</div>",
                        unsafe_allow_html=True
                    )
# ----------------------------------------------------
# RESEARCH PAPERS - OPENALEX API
# ----------------------------------------------------

if page == "🔬 Research Papers":

    st.title("🔬 Research Paper Search")

    st.write(
        "Search research papers related to "
        "IT skills, technologies and career fields."
    )

    st.divider()

    topic = st.text_input(
        "🔍 Search Research Topic",
        placeholder=(
            "Machine Learning, Artificial Intelligence, "
            "Cloud Computing, Cyber Security..."
        )
    )

    number = st.slider(
        "Number of papers",
        min_value=5,
        max_value=20,
        value=10
    )

    if st.button("🔎 Search Research Papers"):

        if not topic.strip():

            st.warning(
                "Please enter a research topic."
            )

        else:

            with st.spinner(
                "🔬 Searching research papers..."
            ):

                result = search_research(
                    topic.strip(),
                    number
                )

            if not result["success"]:

                st.error(
                    result["message"]
                )

            elif not result["papers"]:

                st.info(
                    "No research papers found."
                )

            else:

                st.success(
                    result["message"]
                )

                for i, paper in enumerate(
                    result["papers"]
                ):

                    with st.container():

                        st.markdown(
                            f"""
                            <div style="
                                background:white;
                                padding:20px;
                                margin:15px 0;
                                border-radius:15px;
                                box-shadow:
                                0 4px 15px
                                rgba(0,0,0,0.08);
                                border-left:
                                5px solid #7C3AED;
                            ">
                            """,
                            unsafe_allow_html=True
                        )

                        st.subheader(
                            f"📄 {paper['title']}"
                        )

                        st.write(
                            f"👨‍🔬 **Authors:** "
                            f"{paper['authors']}"
                        )

                        col1, col2 = st.columns(2)

                        with col1:

                            st.write(
                                f"📅 **Year:** "
                                f"{paper['year']}"
                            )

                        with col2:

                            st.write(
                                f"📊 **Citations:** "
                                f"{paper['citations']}"
                            )

                        with st.expander(
                            "📖 Abstract"
                        ):

                            st.write(
                                paper["abstract"]
                            )

                        if paper["url"]:

                            st.link_button(
                                "🔗 View Research Paper",
                                paper["url"]
                            )

                        st.markdown(
                            "</div>",
                            unsafe_allow_html=True
                        )
# ====================================================
# CAREER TOOLS PAGE
# ====================================================

# ====================================================
# ⚙️ CAREER TOOLS PAGE
# ====================================================

if page == "⚙️ Career Tools":

    # =================================================
    # PAGE HEADER
    # =================================================

    st.title("⚙️ Career Tools")

    st.caption(
        "Smart tools to help you plan, analyze and "
        "prepare for your IT career."
    )

    st.divider()

    # =================================================
    # EXPLORE CAREER TOOLS
    # =================================================

    st.subheader("🚀 Explore Career Tools")

    st.caption(
        "Choose a tool and take the next step "
        "in your career preparation."
    )

    st.write("")

    # =================================================
    # MODULE 1 — CAREER RECOMMENDATION
    # =================================================

    st.markdown("## 🎯 Career Recommendation")

    st.caption(
        "Find suitable IT careers based on your "
        "education, skills and interests."
    )

    education = st.selectbox(
        "🎓 Education",
        [
            "B.Sc Computer Science",
            "BCA",
            "B.Tech Computer Science",
            "MCA",
            "Other"
        ],
        key="career_education"
    )

    skills_input = st.text_input(
        "💻 Skills",
        placeholder="Python, SQL, React, JavaScript",
        key="career_skills"
    )

    interests_input = st.text_input(
        "❤️ Interests",
        placeholder="AI, Data Science, Web Development",
        key="career_interests"
    )

    if st.button(
        "🎯 Get Career Recommendations",
        key="career_tool_btn",
        use_container_width=True
    ):

        if not skills_input.strip():

            st.warning(
                "Please enter at least one skill."
            )

        elif not interests_input.strip():

            st.warning(
                "Please enter at least one interest."
            )

        else:

            skills = [
                skill.strip()
                for skill in skills_input.split(",")
                if skill.strip()
            ]

            interests = [
                interest.strip()
                for interest in interests_input.split(",")
                if interest.strip()
            ]

            payload = {
                "education": education,
                "skills": skills,
                "interests": interests
            }

            try:

                with st.spinner(
                    "🎯 Finding suitable careers..."
                ):

                    response = requests.post(
                        "http://127.0.0.1:8000/api/career-recommendation",
                        json=payload,
                        timeout=15
                    )

                if response.status_code == 200:

                    result = response.json()

                    st.success(
                        "Career recommendations generated!"
                    )

                    recommendations = result.get(
                        "recommendations",
                        []
                    )

                    st.markdown(
                        "### 🌟 Recommended Careers"
                    )

                    if recommendations:

                        for career in recommendations:

                            st.success(
                                f"💼 {career}"
                            )

                    else:

                        st.info(
                            "No career recommendations found."
                        )

                else:

                    st.error(
                        f"API Error: "
                        f"{response.status_code}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "❌ Cannot connect to FastAPI."
                )

                st.info(
                    "Make sure FastAPI is running on "
                    "http://127.0.0.1:8000"
                )

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )

    # =================================================
    # SEPARATOR
    # =================================================

    st.divider()

    # =================================================
    # MODULE 2 — SKILL GAP ANALYSIS
    # =================================================

    st.markdown("## 📊 Skill Gap Analysis")

    st.caption(
        "Discover which skills you need to learn "
        "for your target IT role."
    )

    current_skills = st.text_input(
        "💻 Current Skills",
        placeholder="Python, SQL, Git",
        key="current_skills_input"
    )

    target_role = st.selectbox(
        "🎯 Target Job Role",
        [
            "Data Scientist",
            "Frontend Developer",
            "Backend Developer",
            "Data Analyst",
            "Cloud Engineer"
        ],
        key="target_role_input"
    )

    if st.button(
        "📊 Analyze Skill Gap",
        key="skill_gap_tool_btn",
        use_container_width=True
    ):

        if not current_skills.strip():

            st.warning(
                "Please enter your current skills."
            )

        else:

            skills = [
                skill.strip()
                for skill in current_skills.split(",")
                if skill.strip()
            ]

            payload = {
                "current_skills": skills,
                "target_role": target_role
            }

            try:

                with st.spinner(
                    "📊 Analyzing your skill gap..."
                ):

                    response = requests.post(
                        "http://127.0.0.1:8000/api/skill-gap",
                        json=payload,
                        timeout=15
                    )

                if response.status_code == 200:

                    result = response.json()

                    st.success(
                        "Skill gap analysis completed!"
                    )

                    required_skills = result.get(
                        "required_skills",
                        []
                    )

                    missing_skills = result.get(
                        "missing_skills",
                        []
                    )

                    result_col1, result_col2 = st.columns(2)

                    with result_col1:

                        st.metric(
                            "Required Skills",
                            len(required_skills)
                        )

                    with result_col2:

                        st.metric(
                            "Skills to Learn",
                            len(missing_skills)
                        )

                    st.markdown(
                        "### 📚 Skills to Learn"
                    )

                    if missing_skills:

                        for skill in missing_skills:

                            st.warning(
                                f"📌 {skill}"
                            )

                    else:

                        st.success(
                            "🎉 You already have all "
                            "required skills!"
                        )

                else:

                    st.error(
                        f"API Error: "
                        f"{response.status_code}"
                    )

            except requests.exceptions.ConnectionError:

                st.error(
                    "❌ Cannot connect to FastAPI."
                )

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )

    # =================================================
    # SEPARATOR
    # =================================================

    st.divider()

    # =================================================
    # MODULE 3 — RESUME ANALYSIS
    # =================================================

    st.markdown("## 📄 Resume Analysis")

    st.caption(
        "Upload your resume and automatically "
        "identify your technical skills."
    )

    uploaded_resume = st.file_uploader(
        "📤 Upload Resume",
        type=["pdf"],
        key="career_resume_upload"
    )

    st.caption(
        "PDF files only • Maximum 200MB"
    )

    if uploaded_resume is not None:

        st.success(
            f"📄 {uploaded_resume.name} uploaded successfully."
        )

        if st.button(
            "🔍 Analyze Resume",
            key="resume_tool_btn",
            use_container_width=True
        ):

            try:

                import PyPDF2

                pdf_reader = PyPDF2.PdfReader(
                    uploaded_resume
                )

                resume_text = ""

                for pdf_page in pdf_reader.pages:

                    text = pdf_page.extract_text()

                    if text:

                        resume_text += text + "\n"

                if not resume_text.strip():

                    st.error(
                        "❌ Could not extract text "
                        "from this PDF."
                    )

                else:

                    payload = {
                        "resume_text": resume_text
                    }

                    with st.spinner(
                        "📄 Analyzing your resume..."
                    ):

                        response = requests.post(
                            "http://127.0.0.1:8000/api/resume-analysis",
                            json=payload,
                            timeout=15
                        )

                    if response.status_code == 200:

                        result = response.json()

                        skills = result.get(
                            "skills_detected",
                            []
                        )

                        st.success(
                            "✅ Resume analyzed successfully!"
                        )

                        st.metric(
                            "💻 Skills Detected",
                            len(skills)
                        )

                        st.markdown(
                            "### 🔍 Detected Skills"
                        )

                        if skills:

                            for skill in skills:

                                st.success(
                                    f"✅ {skill}"
                                )

                        else:

                            st.warning(
                                "No supported technical "
                                "skills were detected."
                            )

                    else:

                        st.error(
                            f"API Error: "
                            f"{response.status_code}"
                        )

            except requests.exceptions.ConnectionError:

                st.error(
                    "❌ Cannot connect to FastAPI."
                )

                st.info(
                    "Run:\n\n"
                    "`uvicorn api.internal_api:app --reload`"
                )

            except Exception as e:

                st.error(
                    f"Something went wrong: {e}"
                )

    # =================================================
    # SEPARATOR
    # =================================================

    st.divider()

    # =================================================
    # MODULE 4 — INTERVIEW QUESTIONS
    # =================================================

    st.markdown("## 🎤 Interview Questions")

    st.caption(
        "Practice technical questions based "
        "on your selected job role."
    )

    interview_role = st.selectbox(
        "💼 Job Role",
        [
            "Python Developer",
            "Frontend Developer",
            "Data Analyst",
            "Data Scientist",
            "Software Developer"
        ],
        key="interview_role_input"
    )

    difficulty = st.selectbox(
        "📈 Difficulty",
        [
            "Beginner",
            "Intermediate",
            "Advanced"
        ],
        key="interview_difficulty_input"
    )

    if st.button(
        "🎤 Generate Questions",
        key="interview_tool_btn",
        use_container_width=True
    ):

        payload = {
            "role": interview_role,
            "difficulty": difficulty
        }

        try:

            with st.spinner(
                "🎤 Generating interview questions..."
            ):

                response = requests.post(
                    "http://127.0.0.1:8000/api/interview-questions",
                    json=payload,
                    timeout=15
                )

            if response.status_code == 200:

                result = response.json()

                questions = result.get(
                    "questions",
                    []
                )

                st.success(
                    "Interview questions generated!"
                )

                st.markdown(
                    "### 📝 Practice Questions"
                )

                if questions:

                    for i, question in enumerate(
                        questions,
                        start=1
                    ):

                        st.markdown(
                            f"**{i}. {question}**"
                        )

                        st.write("")

                else:

                    st.info(
                        "No questions returned."
                    )

            else:

                st.error(
                    f"API Error: "
                    f"{response.status_code}"
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Cannot connect to FastAPI."
            )

            st.info(
                "Please make sure FastAPI is "
                "running on port 8000."
            )

        except Exception as e:

            st.error(
                f"Something went wrong: {e}"
            )

    # =================================================
    # SEPARATOR
    # =================================================

    st.divider()

    # =================================================
    # MODULE 5 — CAREER LEARNING ROADMAP
    # =================================================

    st.markdown("## 🗺️ Career Learning Roadmap")

    st.caption(
        "Build a structured learning path "
        "for your target career."
    )

    roadmap_role = st.selectbox(
        "🎯 Select Target Career",
        [
            "Frontend Developer",
            "Data Scientist",
            "Data Analyst",
            "Cloud Engineer",
            "Software Developer"
        ],
        key="roadmap_role_input"
    )

    if st.button(
        "🗺️ Generate Career Roadmap",
        key="roadmap_tool_btn",
        use_container_width=True
    ):

        payload = {
            "role": roadmap_role
        }

        try:

            with st.spinner(
                "🗺️ Creating your career roadmap..."
            ):

                response = requests.post(
                    "http://127.0.0.1:8000/api/career-roadmap",
                    json=payload,
                    timeout=15
                )

            if response.status_code == 200:

                result = response.json()

                roadmap = result.get(
                    "roadmap",
                    []
                )

                st.success(
                    f"Roadmap generated for "
                    f"{roadmap_role}!"
                )

                st.markdown(
                    "### 🚀 Your Learning Path"
                )

                if roadmap:

                    for i, step in enumerate(
                        roadmap,
                        start=1
                    ):

                        st.markdown(
                            f"""
                            ### {i}. {step}
                            """
                        )

                        if i < len(roadmap):

                            st.markdown(
                                "⬇️"
                            )

                else:

                    st.info(
                        "No roadmap steps returned."
                    )

            else:

                st.error(
                    f"API Error: "
                    f"{response.status_code}"
                )

        except requests.exceptions.ConnectionError:

            st.error(
                "❌ Cannot connect to FastAPI."
            )

            st.info(
                "Run:\n\n"
                "`uvicorn api.internal_api:app --reload`"
            )

        except Exception as e:

            st.error(
                f"Something went wrong: {e}"
            )