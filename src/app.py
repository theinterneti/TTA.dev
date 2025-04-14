#!/usr/bin/env python3
"""
Streamlit application for TTA.dev Framework

This module provides a simple web interface for interacting with the TTA.dev framework components.
"""

import os
import streamlit as st
import json

# Try to import dotenv, but continue if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    st.warning("python-dotenv not installed, skipping .env loading")

# Import framework components
try:
    from agents import BaseAgent
    from models import get_llm_client
    from database import get_neo4j_manager
    components_loaded = True
except ImportError as e:
    st.error(f"Error importing framework components: {e}")
    components_loaded = False

# Set page config
st.set_page_config(
    page_title="TTA.dev Framework",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main title
st.title("TTA.dev Framework")
st.write("Welcome to the TTA.dev framework web interface!")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Home", "LLM Client", "Database", "Agent Builder"]
)

# Home page
if page == "Home":
    st.header("TTA.dev Framework Overview")
    st.write("""
    The TTA.dev framework provides reusable components for working with AI, agents,
    agentic RAG, database integrations, and building a local LLM coding agent network.

    Use the sidebar to navigate to different components of the framework.
    """)

    # Display component status
    st.subheader("Component Status")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**LLM Client**")
        try:
            if components_loaded:
                client = get_llm_client()
                st.success("✅ Available")
            else:
                st.error("❌ Not available")
        except Exception as e:
            st.error(f"❌ Error: {e}")

    with col2:
        st.write("**Database**")
        try:
            if components_loaded:
                db = get_neo4j_manager()
                if not db._using_mock_db:
                    st.success("✅ Connected")
                else:
                    st.warning("⚠️ Using mock database")
            else:
                st.error("❌ Not available")
        except Exception as e:
            st.error(f"❌ Error: {e}")

    with col3:
        st.write("**Agent Components**")
        if components_loaded:
            st.success("✅ Available")
        else:
            st.error("❌ Not available")

# LLM Client page
elif page == "LLM Client":
    st.header("LLM Client")
    st.write("Test the LLM client with different prompts and models.")

    if not components_loaded:
        st.error("LLM Client components not available.")
    else:
        # Model selection
        model = st.selectbox(
            "Select a model:",
            ["default", "gemma-2b", "gemma-7b", "llama-3-8b", "mistral-7b", "custom"]
        )

        if model == "custom":
            model = st.text_input("Enter custom model name:")
        elif model == "default":
            model = None

        # Generation parameters
        col1, col2 = st.columns(2)
        with col1:
            temperature = st.slider("Temperature:", 0.0, 1.0, 0.7, 0.1)
        with col2:
            max_tokens = st.slider("Max tokens:", 10, 4096, 1024, 10)

        # System prompt
        system_prompt = st.text_area("System prompt (optional):")

        # User prompt
        prompt = st.text_area("Enter your prompt:")

        # JSON output option
        expect_json = st.checkbox("Expect JSON output")

        # Generate button
        if st.button("Generate"):
            if prompt:
                with st.spinner("Generating response..."):
                    try:
                        client = get_llm_client()
                        response = client.generate(
                            prompt=prompt,
                            system_prompt=system_prompt if system_prompt else None,
                            model=model,
                            temperature=temperature,
                            max_tokens=max_tokens,
                            expect_json=expect_json
                        )

                        st.subheader("Response:")
                        if expect_json:
                            try:
                                # Display as JSON
                                json_data = json.loads(response)
                                st.json(json_data)
                            except json.JSONDecodeError:
                                # Display as text if not valid JSON
                                st.text(response)
                        else:
                            st.write(response)
                    except Exception as e:
                        st.error(f"Error generating response: {e}")
            else:
                st.warning("Please enter a prompt.")

# Database page
elif page == "Database":
    st.header("Database Integration")
    st.write("Test the Neo4j database integration.")

    if not components_loaded:
        st.error("Database components not available.")
    else:
        # Connection status
        try:
            db = get_neo4j_manager()
            if not db._using_mock_db:
                st.success("✅ Connected to Neo4j database")
            else:
                st.warning("⚠️ Using mock database (Neo4j not available)")
        except Exception as e:
            st.error(f"❌ Error connecting to database: {e}")

        # Custom query
        st.subheader("Execute Cypher Query")
        query = st.text_area("Enter Cypher query:", "MATCH (n) RETURN count(n) AS count")

        if st.button("Execute Query"):
            if query:
                with st.spinner("Executing query..."):
                    try:
                        result = db.query(query)
                        st.subheader("Results:")
                        if result:
                            # Convert to list of dicts for display
                            result_dicts = [dict(record) for record in result]
                            st.json(result_dicts)
                        else:
                            st.info("Query executed successfully, but no results returned.")
                    except Exception as e:
                        st.error(f"Error executing query: {e}")
            else:
                st.warning("Please enter a query.")

        # Node creation form
        st.subheader("Create Node")
        col1, col2 = st.columns(2)
        with col1:
            label = st.text_input("Node label:", "Person")
        with col2:
            properties_str = st.text_area("Properties (JSON):", '{"name": "John Doe", "age": 30}')

        if st.button("Create Node"):
            try:
                properties = json.loads(properties_str)
                result = db.create_node(label, properties)
                if result:
                    st.success("Node created successfully!")
                    st.json(result)
                else:
                    st.warning("Node creation returned no result.")
            except json.JSONDecodeError:
                st.error("Invalid JSON for properties.")
            except Exception as e:
                st.error(f"Error creating node: {e}")

# Agent Builder page
elif page == "Agent Builder":
    st.header("Agent Builder")
    st.write("Create and configure agents using the TTA.dev framework.")

    if not components_loaded:
        st.error("Agent components not available.")
    else:
        # Agent configuration
        col1, col2 = st.columns(2)
        with col1:
            agent_name = st.text_input("Agent name:", "MyAgent")
        with col2:
            agent_description = st.text_input("Agent description:", "A custom agent built with TTA.dev framework")

        system_prompt = st.text_area("System prompt:", "You are a helpful AI assistant.")

        # Create agent button
        if st.button("Create Agent"):
            try:
                agent = BaseAgent(
                    name=agent_name,
                    description=agent_description,
                    system_prompt=system_prompt
                )

                st.success(f"Agent '{agent_name}' created successfully!")

                # Display agent info
                st.subheader("Agent Information:")
                st.json(agent.get_info())

                # Store agent in session state for later use
                st.session_state.agent = agent
            except Exception as e:
                st.error(f"Error creating agent: {e}")

        # If agent exists in session state, show interaction panel
        if hasattr(st.session_state, 'agent'):
            st.subheader("Agent Interaction")
            st.write(f"Interact with agent: {st.session_state.agent.name}")

            # This would be expanded in a real implementation to allow for agent interaction
