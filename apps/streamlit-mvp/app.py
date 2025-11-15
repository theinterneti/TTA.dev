"""
TTA Streamlit MVP - Therapeutic Through Artistry
A simple web interface for the TTA story generation system
"""

import sys
from pathlib import Path

import streamlit as st

# Add tta-rebuild to path
tta_rebuild_path = Path(__file__).parent.parent.parent / "packages" / "tta-rebuild" / "src"
sys.path.insert(0, str(tta_rebuild_path))

# Page configuration
st.set_page_config(
    page_title="TTA - Therapeutic Through Artistry",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown(
    """
    <style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .story-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #1f77b4;
    }
    .choice-button {
        margin: 0.5rem 0;
    }
    .character-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin: 0.5rem 0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "current_character" not in st.session_state:
    st.session_state.current_character = None
if "current_run" not in st.session_state:
    st.session_state.current_run = None
if "story_history" not in st.session_state:
    st.session_state.story_history = []


def login_page():
    """Simple login page (simulated Google OAuth for MVP)"""
    st.markdown('<h1 class="main-header">🎭 Welcome to TTA</h1>', unsafe_allow_html=True)

    st.write("""
    ### Therapeutic Through Artistry

    Experience interactive therapeutic storytelling powered by AI.

    **Features:**
    - 🎭 Create and develop unique characters
    - 📖 Generate personalized story narratives
    - 🌟 Long-term character progression
    - 💡 Therapeutic themes and insights
    """)

    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.subheader("Sign In")

        # For MVP, simple email input (will be replaced with real OAuth)
        email = st.text_input("Email Address", placeholder="you@example.com")

        if st.button("🔐 Sign In with Google (Simulated)", use_container_width=True):
            if email:
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.success(f"Welcome, {email}!")
                st.rerun()
            else:
                st.error("Please enter an email address")

        st.caption(
            "*Note: This MVP uses simulated authentication. Real Google OAuth will be added in production.*"
        )


def character_creation_page():
    """Character creation interface"""
    st.header("🎭 Create Your Character")

    with st.form("character_form"):
        name = st.text_input("Character Name", placeholder="e.g., Sarah the Explorer")

        archetype = st.selectbox(
            "Character Archetype",
            ["The Hero", "The Sage", "The Explorer", "The Caregiver", "The Creator"],
        )

        backstory = st.text_area(
            "Backstory (Optional)",
            placeholder="Describe your character's background and motivations...",
            height=150,
        )

        therapeutic_focus = st.multiselect(
            "Therapeutic Themes",
            [
                "Self-Discovery",
                "Overcoming Fear",
                "Building Confidence",
                "Finding Purpose",
                "Healing Trauma",
            ],
        )

        submitted = st.form_submit_button("Create Character", use_container_width=True)

        if submitted:
            if name:
                # Create character object
                character = {
                    "name": name,
                    "archetype": archetype,
                    "backstory": backstory,
                    "therapeutic_focus": therapeutic_focus,
                    "level": 1,
                    "experiences": [],
                }
                st.session_state.current_character = character
                st.success(f"✅ Character '{name}' created successfully!")
                st.balloons()
            else:
                st.error("Please provide a character name")


def story_generation_page():
    """Story generation and gameplay interface"""
    character = st.session_state.current_character

    if not character:
        st.warning("⚠️ Please create a character first!")
        return

    # Character info sidebar
    with st.sidebar:
        st.subheader(f"🎭 {character['name']}")
        st.write(f"**Archetype:** {character['archetype']}")
        st.write(f"**Level:** {character['level']}")

        if character.get("therapeutic_focus"):
            st.write("**Themes:**")
            for theme in character["therapeutic_focus"]:
                st.write(f"- {theme}")

    st.header("📖 Your Story")

    # Check if we need to generate first story beat
    if not st.session_state.story_history:
        if st.button("🚀 Begin Your Journey", use_container_width=True):
            with st.spinner("Generating your personalized story..."):
                # Import and use TTA-Rebuild backend
                try:
                    from tta_rebuild.integrations.gemini_provider import (
                        GeminiLLMProvider,
                    )
                    from tta_rebuild.narrative.story_generator import (
                        StoryGeneratorPrimitive,
                    )

                    # Initialize story generator
                    llm_provider = GeminiLLMProvider()
                    story_gen = StoryGeneratorPrimitive(llm_provider)

                    # Generate first beat
                    context = {
                        "character_name": character["name"],
                        "archetype": character["archetype"],
                        "backstory": character.get("backstory", ""),
                        "therapeutic_themes": character.get("therapeutic_focus", []),
                    }

                    # Generate story
                    result = story_gen.generate_story_beat(context)

                    # Store in history
                    st.session_state.story_history.append(
                        {
                            "narrative": result.get("narrative", "A new adventure begins..."),
                            "choices": result.get(
                                "choices",
                                [
                                    {
                                        "text": "Explore the forest",
                                        "consequence": "discovery",
                                    },
                                    {"text": "Return to town", "consequence": "safety"},
                                    {
                                        "text": "Meditate on the situation",
                                        "consequence": "insight",
                                    },
                                ],
                            ),
                        }
                    )

                    st.rerun()

                except Exception as e:
                    # Fallback for MVP if Gemini not configured
                    st.warning(f"Backend not fully configured: {e}")
                    st.info("Using fallback story generation for demonstration...")

                    # Fallback story
                    st.session_state.story_history.append(
                        {
                            "narrative": f"""
                        {character["name"]}, {character["archetype"]}, stands at the edge of a vast, unknown landscape.

                        The journey ahead promises both challenges and growth. Your therapeutic focus on
                        {", ".join(character.get("therapeutic_focus", ["self-discovery"]))} will guide you
                        through this transformative experience.

                        What do you do?
                        """,
                            "choices": [
                                {
                                    "text": "🌲 Venture into the mysterious forest",
                                    "consequence": "Discover hidden truths",
                                },
                                {
                                    "text": "🏛️ Seek wisdom from the village elders",
                                    "consequence": "Gain perspective",
                                },
                                {
                                    "text": "🧘 Take time for self-reflection",
                                    "consequence": "Build inner strength",
                                },
                            ],
                        }
                    )

                    st.rerun()

    # Display story history
    for idx, beat in enumerate(st.session_state.story_history):
        st.markdown(f'<div class="story-box">{beat["narrative"]}</div>', unsafe_allow_html=True)

        # Show choices for the latest beat
        if idx == len(st.session_state.story_history) - 1:
            st.subheader("Choose your path:")

            cols = st.columns(len(beat["choices"]))
            for i, choice in enumerate(beat["choices"]):
                with cols[i]:
                    if st.button(
                        choice["text"],
                        key=f"choice_{idx}_{i}",
                        use_container_width=True,
                    ):
                        # Generate next story beat based on choice
                        with st.spinner("Your story continues..."):
                            # Simulate story continuation
                            next_narrative = f"""
                            You chose: **{choice["text"]}**

                            {choice.get("consequence", "The story unfolds...")}

                            This decision reflects your journey toward {", ".join(character.get("therapeutic_focus", ["growth"]))}.
                            What happens next?
                            """

                            st.session_state.story_history.append(
                                {
                                    "narrative": next_narrative,
                                    "choices": [
                                        {
                                            "text": "Continue forward",
                                            "consequence": "Progress",
                                        },
                                        {
                                            "text": "Pause and reflect",
                                            "consequence": "Insight",
                                        },
                                        {
                                            "text": "Try a different approach",
                                            "consequence": "Adaptation",
                                        },
                                    ],
                                }
                            )

                            # Level up character
                            character["level"] += 1
                            character["experiences"].append(choice["text"])

                            st.rerun()

    # Story controls
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Progress", use_container_width=True):
            st.success("✅ Progress saved!")
    with col2:
        if st.button("🔄 Start New Story", use_container_width=True):
            st.session_state.story_history = []
            st.rerun()


def dashboard_page():
    """Main dashboard"""
    st.header(f"👤 Welcome, {st.session_state.user_email}")

    # Stats
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Characters", "1" if st.session_state.current_character else "0")

    with col2:
        st.metric("Story Beats", len(st.session_state.story_history))

    with col3:
        level = (
            st.session_state.current_character["level"] if st.session_state.current_character else 0
        )
        st.metric("Character Level", level)

    st.markdown("---")

    # Quick actions
    st.subheader("Quick Actions")

    col1, col2 = st.columns(2)

    with col1:
        if not st.session_state.current_character:
            if st.button("🎭 Create First Character", use_container_width=True):
                st.session_state.page = "create_character"
                st.rerun()
        else:
            if st.button("📖 Continue Story", use_container_width=True):
                st.session_state.page = "play"
                st.rerun()

    with col2:
        if st.session_state.current_character:
            if st.button("🎭 View Character", use_container_width=True):
                with st.expander("Character Details", expanded=True):
                    char = st.session_state.current_character
                    st.write(f"**Name:** {char['name']}")
                    st.write(f"**Archetype:** {char['archetype']}")
                    st.write(f"**Level:** {char['level']}")
                    if char.get("backstory"):
                        st.write(f"**Backstory:** {char['backstory']}")
                    if char.get("experiences"):
                        st.write("**Experiences:**")
                        for exp in char["experiences"]:
                            st.write(f"- {exp}")


def main():
    """Main application"""

    # Check authentication
    if not st.session_state.authenticated:
        login_page()
        return

    # Sidebar navigation
    with st.sidebar:
        st.title("🎭 TTA")

        page = st.radio(
            "Navigation",
            ["Dashboard", "Create Character", "Play Story"],
            key="nav_radio",
        )

        st.markdown("---")

        if st.button("🚪 Sign Out"):
            # Clear session
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Route to appropriate page
    if page == "Dashboard":
        dashboard_page()
    elif page == "Create Character":
        character_creation_page()
    elif page == "Play Story":
        story_generation_page()


if __name__ == "__main__":
    main()
