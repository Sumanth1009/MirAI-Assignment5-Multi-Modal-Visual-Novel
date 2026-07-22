# 🎮 AI Multi-Modal Visual Novel

A **Choose Your Own Adventure Visual Novel** developed as the Capstone Mini-Project for the **MirAI School of Technology – Virtual Summer Internship 2026, AI Builder Track**.

The application combines stateful AI storytelling, AI-generated images, dynamic choices, and text-to-speech narration to create an interactive visual novel experience.

---

## 🚀 Features

- 🎭 Multiple Story Genres
- 🎨 Multiple Art Styles
- 🧠 Stateful Story Generation using Gemini AI
- 📦 Structured JSON Response Parsing
- 🎯 Dynamically Generated Story Choices
- 🖼️ AI Image Generation using Pollinations
- 🔊 Text-to-Speech Narration using gTTS
- 💾 Story History using Streamlit Session State
- 🔄 Start / Change Adventure System
- ⚠️ Graceful API Failure Handling
- 🎮 Interactive Choose-Your-Own-Adventure Experience

---

## 🧠 How It Works

1. The user selects a **Story Genre**.
2. The user selects an **Art Style**.
3. Gemini generates a structured JSON response containing:
   - `story_text`
   - `image_prompt`
   - `options`
4. The JSON response is parsed using Python's `json` library.
5. Pollinations generates an image using the AI-generated image prompt.
6. gTTS converts the story into audio narration.
7. Streamlit dynamically creates buttons for the available choices.
8. The user's selected choice is sent back to Gemini.
9. The story continues while maintaining previous context.

---

## 🛠️ Technologies Used

- Python
- Streamlit
- Google Gemini API
- Pollinations AI
- gTTS
- Requests
- python-dotenv
- JSON
- Streamlit Session State

---

## 📂 Project Structure

```text
MirAI_Assignment5/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
└── .env