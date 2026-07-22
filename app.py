# ==========================================================
# 🎮 MIRAI ASSIGNMENT 5
# MULTI-MODAL VISUAL NOVEL
# FINAL VERSION
# ==========================================================

import streamlit as st
import os
import json
import requests
import io

from urllib.parse import quote
from dotenv import load_dotenv
from google import genai
from gtts import gTTS


# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="AI Multi-Modal Visual Novel",
    page_icon="🎮",
    layout="wide"
)


# ==========================================================
# LOAD API KEY
# ==========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY was not found in the .env file.")
    st.stop()


# ==========================================================
# GEMINI CLIENT
# ==========================================================

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


try:
    client = get_gemini_client()

except Exception as error:
    st.error(f"❌ Gemini connection failed: {error}")
    st.stop()


# ==========================================================
# OPTIONS
# ==========================================================

GENRES = [
    "⚔️ Fantasy Adventure",
    "🚀 Science Fiction",
    "🕵️ Mystery",
    "👻 Horror",
    "🏴‍☠️ Pirate Adventure",
    "🦸 Superhero",
    "🏛️ Mythology"
]


ART_STYLES = [
    "Cinematic Realistic",
    "Anime",
    "Digital Fantasy Art",
    "Comic Book",
    "3D Render",
    "Watercolor",
    "Dark Gothic"
]


# ==========================================================
# SESSION STATE
# ==========================================================

if "story_history" not in st.session_state:
    st.session_state.story_history = []

if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = None

if "current_scene" not in st.session_state:
    st.session_state.current_scene = None

if "story_started" not in st.session_state:
    st.session_state.story_started = False

if "scene_number" not in st.session_state:
    st.session_state.scene_number = 0

if "active_genre" not in st.session_state:
    st.session_state.active_genre = None

if "active_art_style" not in st.session_state:
    st.session_state.active_art_style = None


# ==========================================================
# RESET STORY
# ==========================================================

def reset_story():

    st.session_state.story_history = []
    st.session_state.gemini_chat = None
    st.session_state.current_scene = None
    st.session_state.story_started = False
    st.session_state.scene_number = 0
    st.session_state.active_genre = None
    st.session_state.active_art_style = None


# ==========================================================
# CREATE GEMINI CHAT
# ==========================================================

def create_story_chat(genre, art_style):

    system_prompt = f"""
You are the director of an interactive
Choose Your Own Adventure visual novel.

GENRE:
{genre}

ART STYLE:
{art_style}

Create ONE scene at a time.

You MUST return ONLY a valid JSON object.

Do not use Markdown.
Do not use JSON code blocks.
Do not add explanations.

Use exactly these keys:

{{
    "story_text": "Narrative paragraph",
    "image_prompt": "Detailed AI image prompt",
    "options": [
        "Choice one",
        "Choice two",
        "Choice three"
    ]
}}

RULES:

1. story_text should be approximately 100-150 words.

2. Make every scene immersive.

3. Maintain story continuity.

4. image_prompt must describe the current scene.

5. Use this visual style:
{art_style}

6. Describe the characters, environment,
lighting, atmosphere and composition.

7. Generate 2 or 3 choices.

8. Each choice must create a different direction.

9. Never generate fewer than 2 choices.

10. Never generate more than 3 choices.

11. Return JSON only.
"""

    return client.chats.create(
        model="gemini-3.1-flash-lite",
        config={
            "system_instruction": system_prompt
        }
    )


# ==========================================================
# JSON PARSER
# ==========================================================

def parse_story_response(response_text):

    try:

        cleaned = response_text.strip()

        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]

        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]

        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        cleaned = cleaned.strip()

        data = json.loads(cleaned)

        # ----------------------------------------------
        # Validate dictionary
        # ----------------------------------------------

        if not isinstance(data, dict):
            raise ValueError(
                "Gemini response is not a JSON object."
            )

        # ----------------------------------------------
        # Required keys
        # ----------------------------------------------

        required_keys = [
            "story_text",
            "image_prompt",
            "options"
        ]

        for key in required_keys:

            if key not in data:
                raise ValueError(
                    f"Missing JSON key: {key}"
                )

        # ----------------------------------------------
        # Validate text
        # ----------------------------------------------

        if not isinstance(data["story_text"], str):
            raise ValueError(
                "story_text must be text."
            )

        if not isinstance(data["image_prompt"], str):
            raise ValueError(
                "image_prompt must be text."
            )

        # ----------------------------------------------
        # Validate options
        # ----------------------------------------------

        if not isinstance(data["options"], list):
            raise ValueError(
                "options must be a list."
            )

        valid_options = []

        for option in data["options"]:

            if isinstance(option, str):

                option = option.strip()

                if option:
                    valid_options.append(option)

        if len(valid_options) < 2:
            raise ValueError(
                "Gemini must provide at least 2 choices."
            )

        data["options"] = valid_options[:3]

        return data


    except Exception as error:

        st.error(
            f"❌ JSON Story Error: {error}"
        )

        with st.expander(
            "🔧 View Gemini Response"
        ):

            st.code(response_text)

        return None


# ==========================================================
# IMAGE GENERATION
# ==========================================================

def generate_scene_image(image_prompt):

    try:

        encoded_prompt = quote(
            image_prompt,
            safe=""
        )

        image_url = (
            f"https://image.pollinations.ai/prompt/"
            f"{encoded_prompt}"
            f"?width=1024"
            f"&height=576"
            f"&nologo=true"
        )

        response = requests.get(
            image_url,
            timeout=45
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type",
            ""
        )

        if "image" not in content_type.lower():
            raise ValueError(
                "Server did not return an image."
            )

        return response.content


    except Exception:

        st.toast(
            "Image server is busy, skipping visual..."
        )

        return None


# ==========================================================
# TEXT TO SPEECH
# ==========================================================

def generate_story_audio(story_text):

    try:

        tts = gTTS(
            text=story_text,
            lang="en",
            slow=False
        )

        audio_buffer = io.BytesIO()

        tts.write_to_fp(
            audio_buffer
        )

        audio_buffer.seek(0)

        return audio_buffer.getvalue()


    except Exception:

        st.toast(
            "Narration unavailable. Story will continue."
        )

        return None


# ==========================================================
# PREPARE SCENE
# ==========================================================

def prepare_scene(story_data):

    if story_data is None:
        return None

    # Generate image
    story_data["image_bytes"] = (
        generate_scene_image(
            story_data["image_prompt"]
        )
    )

    # Generate narration
    story_data["audio_bytes"] = (
        generate_story_audio(
            story_data["story_text"]
        )
    )

    return story_data


# ==========================================================
# START STORY
# ==========================================================

def start_story(genre, art_style):

    # Clear old story first
    reset_story()

    st.session_state.active_genre = genre
    st.session_state.active_art_style = art_style

    try:

        with st.spinner(
            "🌌 Creating your new adventure..."
        ):

            # ------------------------------------------
            # Create stateful Gemini chat
            # ------------------------------------------

            st.session_state.gemini_chat = (
                create_story_chat(
                    genre,
                    art_style
                )
            )

            # ------------------------------------------
            # Generate Scene 1
            # ------------------------------------------

            response = (
                st.session_state.gemini_chat.send_message(
                    """
Begin a completely new adventure.

Create an exciting opening scene.

Immediately place the player inside the story.

Introduce a mystery, danger, mission,
conflict or important objective.

End the scene at an important decision.

Return ONLY the required JSON object.
"""
                )
            )

            story_data = parse_story_response(
                response.text
            )

            if story_data:

                story_data = prepare_scene(
                    story_data
                )

                st.session_state.current_scene = (
                    story_data
                )

                st.session_state.story_history = [
                    story_data
                ]

                st.session_state.scene_number = 1

                st.session_state.story_started = True

                st.rerun()


    except Exception as error:

        st.error(
            f"❌ Gemini Story Engine Error: {error}"
        )


# ==========================================================
# CONTINUE STORY
# ==========================================================

def continue_story(player_choice):

    if st.session_state.gemini_chat is None:

        st.error(
            "❌ Story engine is unavailable."
        )

        return

    try:

        with st.spinner(
            "🎬 Your decision is changing the story..."
        ):

            response = (
                st.session_state.gemini_chat.send_message(
                    f"""
The player selected:

{player_choice}

Continue directly from the previous scene.

Show the consequences of this decision.

Maintain all established characters,
locations and story continuity.

Create the next scene.

Finish with another important decision.

Return ONLY the required JSON object.
"""
                )
            )

            new_scene = parse_story_response(
                response.text
            )

            if new_scene:

                new_scene = prepare_scene(
                    new_scene
                )

                st.session_state.current_scene = (
                    new_scene
                )

                st.session_state.story_history.append(
                    new_scene
                )

                st.session_state.scene_number += 1

                st.rerun()


    except Exception as error:

        st.error(
            f"❌ Could not continue story: {error}"
        )


# ==========================================================
# MAIN HEADER
# ==========================================================

st.title(
    "🎮 AI Multi-Modal Visual Novel"
)

st.caption(
    "Choose your world • Make decisions • Shape your adventure"
)


# ==========================================================
# IMPORTANT CONTROLS AT THE TOP
# ==========================================================

st.subheader(
    "🎬 Create / Change Your Adventure"
)

control1, control2, control3 = st.columns(
    [2, 2, 2]
)


# ----------------------------------------------------------
# GENRE
# ----------------------------------------------------------

with control1:

    selected_genre = st.selectbox(
        "📚 Story Genre",
        GENRES,
        key="top_genre"
    )


# ----------------------------------------------------------
# ART STYLE
# ----------------------------------------------------------

with control2:

    selected_art_style = st.selectbox(
        "🎨 Art Style",
        ART_STYLES,
        key="top_art_style"
    )


# ----------------------------------------------------------
# START / CHANGE BUTTON
# ----------------------------------------------------------

with control3:

    st.write("")
    st.write("")

    if st.button(
        "🚀 Start / Apply New Adventure",
        type="primary",
        use_container_width=True
    ):

        start_story(
            selected_genre,
            selected_art_style
        )


# ==========================================================
# CURRENT SETTINGS
# ==========================================================

if st.session_state.story_started:

    st.success(
        f"🎮 Current Adventure: "
        f"{st.session_state.active_genre}  |  "
        f"🎨 {st.session_state.active_art_style}"
    )


st.divider()


# ==========================================================
# SIDEBAR - ONLY SECONDARY INFORMATION
# ==========================================================

with st.sidebar:

    st.title(
        "🎮 Adventure Dashboard"
    )

    st.caption(
        "Your current adventure statistics"
    )

    st.divider()

    st.metric(
        "📖 Current Scene",
        st.session_state.scene_number
    )

    st.metric(
        "🧠 Story Memories",
        len(st.session_state.story_history)
    )

    st.divider()

    if st.session_state.story_started:

        st.success(
            "🟢 Adventure Active"
        )

        st.write(
            "**Genre:**"
        )

        st.write(
            st.session_state.active_genre
        )

        st.write(
            "**Art Style:**"
        )

        st.write(
            st.session_state.active_art_style
        )

    else:

        st.info(
            "Choose your settings at the top "
            "and start an adventure."
        )

    st.divider()

    if st.button(
        "🗑️ Clear Adventure",
        use_container_width=True
    ):

        reset_story()

        st.rerun()

    st.divider()

    st.success(
        "🧠 Gemini Connected"
    )

    st.caption(
        "MirAI Capstone Project"
    )


# ==========================================================
# WELCOME SCREEN
# ==========================================================

if not st.session_state.story_started:

    st.subheader(
        "🌌 Ready for an Adventure?"
    )

    st.info(
        """
### How to Play

1. Choose a **Story Genre** above.

2. Choose an **Art Style**.

3. Click **🚀 Start / Apply New Adventure**.

4. Read and listen to your AI-generated story.

5. Choose one of the AI-generated decisions.

6. Every choice creates a new scene, image and narration.

You can change the Genre or Art Style at any time
and click **Start / Apply New Adventure** to begin again.
"""
    )


# ==========================================================
# ACTIVE VISUAL NOVEL
# ==========================================================

else:

    scene = st.session_state.current_scene

    if scene:

        # ==================================================
        # SCENE HEADER
        # ==================================================

        st.subheader(
            f"📖 Scene {st.session_state.scene_number}"
        )


        # ==================================================
        # STORY + IMAGE
        # ==================================================

        story_col, image_col = st.columns(
            [1, 1]
        )


        # --------------------------------------------------
        # STORY
        # --------------------------------------------------

        with story_col:

            st.markdown(
                "### 📜 Story"
            )

            st.write(
                scene["story_text"]
            )


        # --------------------------------------------------
        # IMAGE
        # --------------------------------------------------

        with image_col:

            st.markdown(
                "### 🎨 Scene Visual"
            )

            if scene.get("image_bytes"):

                st.image(
                    scene["image_bytes"],
                    caption=(
                        f"Scene "
                        f"{st.session_state.scene_number}"
                    ),
                    use_container_width=True
                )

            else:

                st.info(
                    "🎨 Visual unavailable. "
                    "The story can still continue."
                )


        # ==================================================
        # IMPORTANT: CHOICES BEFORE SECONDARY DETAILS
        # ==================================================

        st.divider()

        st.subheader(
            "🧭 What Will You Do?"
        )

        st.caption(
            "Choose your next move — each decision changes the story."
        )

        options = scene["options"]


        # --------------------------------------------------
        # DISPLAY OPTIONS SIDE-BY-SIDE
        # --------------------------------------------------

        option_columns = st.columns(
            len(options)
        )


        for index, option in enumerate(options):

            with option_columns[index]:

                if st.button(
                    f"🎯 {option}",
                    key=(
                        f"scene_"
                        f"{st.session_state.scene_number}_"
                        f"choice_{index}"
                    ),
                    use_container_width=True
                ):

                    continue_story(
                        option
                    )

                    st.stop()


        # ==================================================
        # NARRATION
        # ==================================================

        st.divider()

        st.subheader(
            "🔊 Scene Narration"
        )

        if scene.get("audio_bytes"):

            st.audio(
                scene["audio_bytes"],
                format="audio/mp3"
            )

        else:

            st.info(
                "🔇 Narration is currently unavailable."
            )


        # ==================================================
        # SECONDARY DETAILS
        # ==================================================

        with st.expander(
            "🎬 View AI Image Prompt"
        ):

            st.write(
                scene["image_prompt"]
            )


        # ==================================================
        # STORY HISTORY
        # ==================================================

        with st.expander(
            f"📚 Previous Scenes "
            f"({len(st.session_state.story_history)})"
        ):

            for index, old_scene in enumerate(
                st.session_state.story_history,
                start=1
            ):

                st.markdown(
                    f"### Scene {index}"
                )

                st.write(
                    old_scene["story_text"]
                )

                if index < len(
                    st.session_state.story_history
                ):

                    st.divider()


# ==========================================================
# TECHNICAL INFORMATION - KEEP AT BOTTOM
# ==========================================================

st.divider()

with st.expander(
    "🛠️ Assignment 5 Requirements"
):

    st.markdown(
        """
### ✅ Phase 1 — Director's Cut

- `@st.cache_resource`
- Gemini Client
- Story Genre selection
- Art Style selection
- `st.session_state`
- Stateful Gemini chat

### ✅ Phase 2 — Structured JSON Engine

- Python `json` library
- `json.loads()`
- `story_text`
- `image_prompt`
- `options`
- JSON validation

### ✅ Phase 3 — Dynamic UI

- Dynamic AI-generated choices
- Python `for` loop
- Dynamic `st.button()`
- Selected choice sent back to Gemini
- Continuous story generation

### ✅ Phase 4 — Multimedia

- Pollinations image generation
- AI-generated image prompts
- Image rendering
- gTTS Text-to-Speech
- `st.audio()` narration
- Session-based story persistence

### ✅ Phase 5 — Graceful Failures

- Python `try...except`
- Image API error handling
- Network timeout handling
- `st.toast()` notification
- TTS error handling
- Gemini API error handling
"""
    )


# ==========================================================
# FOOTER
# ==========================================================

st.divider()

footer1, footer2, footer3 = st.columns(3)

with footer1:

    st.success(
        "🧠 Gemini AI"
    )

with footer2:

    st.info(
        "🎮 Visual Novel"
    )

with footer3:

    st.success(
        "🎨 AI Visuals + 🔊 TTS"
    )


st.caption(
    "❤️ Developed by Sumanth | "
    "MirAI Virtual Summer Internship 2026"
)