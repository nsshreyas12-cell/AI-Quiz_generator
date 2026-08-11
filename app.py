import streamlit as st
import json
from groq import Groq
import os

# --- Page Configuration ---
st.set_page_config(page_title="AI Quiz Generator", page_icon="🧠", layout="centered")
st.title("🧠 AI Quiz Generator")

# --- API Key Setup ---
try:
    api_key = st.secrets["GROQ_API_KEY"]
except:
    api_key = st.sidebar.text_input("Enter your Groq API Key:", type="password")

if not api_key:
    st.warning("Please enter your Groq API Key in the sidebar or Streamlit secrets to continue.")
    st.stop()

client = Groq(api_key=api_key)

# --- Session State Management ---
# We use session state so the quiz doesn't disappear when the user clicks an answer
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None
if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

# --- Quiz Generation Logic ---
def generate_quiz(topic, difficulty, num_questions):
    prompt = f"""
    Generate a {difficulty} level multiple-choice quiz with {num_questions} questions about the following topic or text:
    "{topic}"

    You MUST return the output ONLY as a valid JSON object in the following exact format:
    {{
      "quiz": [
        {{
          "question": "Question text here",
          "options": ["Option A", "Option B", "Option C", "Option D"],
          "answer": "Correct option text exactly as it appears in options",
          "explanation": "Brief explanation of why the answer is correct"
        }}
      ]
    }}
    """
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            # Enforcing JSON mode to get structured data
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("⚙️ Quiz Settings")
    topic = st.text_area("Topic or Paste Text:", placeholder="e.g., Python Basics, World War II, etc.")
    difficulty = st.selectbox("Difficulty", ["Easy", "Medium", "Hard"])
    num_questions = st.slider("Number of Questions", min_value=1, max_value=15, value=5)
    
    if st.button("Generate Quiz", type="primary"):
        if topic.strip():
            with st.spinner("Generating your quiz..."):
                quiz_data = generate_quiz(topic, difficulty, num_questions)
                if quiz_data and "quiz" in quiz_data:
                    # Reset state for a new quiz
                    st.session_state.quiz_data = quiz_data["quiz"]
                    st.session_state.quiz_submitted = False
        else:
            st.error("Please enter a topic or text first!")

# --- Main App: Quiz UI ---
if st.session_state.quiz_data:
    st.subheader("Quiz Time! 🚀")
    
    # Display the questions iteratively
    for i, q in enumerate(st.session_state.quiz_data):
        st.markdown(f"**Q{i+1}: {q['question']}**")
        
        # Radio button for user to select an answer
        st.radio(
            "Select an option:",
            q["options"],
            key=f"q_{i}",
            index=None, # Starts with no selection
            disabled=st.session_state.quiz_submitted # Lock options after submission
        )
        st.write("---")

    # Display Submit button only if not submitted yet
    if not st.session_state.quiz_submitted:
        if st.button("Submit Quiz", type="primary"):
            st.session_state.quiz_submitted = True
            st.rerun() # Refresh app to lock inputs and calculate score

    # --- Results Calculation and UI ---
    if st.session_state.quiz_submitted:
        st.header("🎯 Quiz Results")
        score = 0
        total = len(st.session_state.quiz_data)
        
        # Compare user answers with correct answers
        for i, q in enumerate(st.session_state.quiz_data):
            user_ans = st.session_state.get(f"q_{i}")
            correct_ans = q["answer"]
            
            st.markdown(f"**Q{i+1}: {q['question']}**")
            
            if user_ans == correct_ans:
                score += 1
                st.success(f"Your Answer: {user_ans} ✅")
            else:
                if user_ans is None:
                    st.warning("You skipped this question ⚠️")
                else:
                    st.error(f"Your Answer: {user_ans} ❌")
                st.info(f"Correct Answer: {correct_ans}")
                
            st.markdown(f"*📝 **Explanation:** {q['explanation']}*")
            st.write("---")
            
        st.subheader(f"Final Score: {score} / {total}")
        
        if score == total:
            st.balloons()
