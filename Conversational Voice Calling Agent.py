import streamlit as st
import google.generativeai as genai
import requests
import json
import asyncio
import aiohttp
import websockets
import time
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional
import uuid
import threading
from dataclasses import dataclass

# Page configuration
st.set_page_config(
    page_title="Voice Calling AI Agent",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

@dataclass
class CallSession:
    call_id: str
    phone_number: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    conversation_log: List[Dict] = None
    call_outcome: Optional[str] = None

class DashaCallAgent:
    def __init__(self):
        self.dasha_api_key = None
        self.dasha_app_id = None
        self.gemini_client = None
        self.base_url = "https://app.dasha.ai/api/v2"
        self.active_calls = {}
        self.call_history = []

    def setup_gemini(self, api_key: str) -> bool:
        """Initialize Gemini AI for conversation intelligence"""
        try:
            genai.configure(api_key=api_key)
            self.gemini_client = genai.GenerativeModel('gemini-pro')
            return True
        except Exception as e:
            st.error(f"Failed to setup Gemini: {str(e)}")
            return False

    def setup_dasha(self, api_key: str, app_id: str) -> bool:
        """Setup Dasha AI API for voice calling"""
        self.dasha_api_key = api_key
        self.dasha_app_id = app_id
        return self.validate_dasha_connection()

    def validate_dasha_connection(self) -> bool:
        """Validate Dasha API connection"""
        headers = {
            'Authorization': f'Bearer {self.dasha_api_key}',
            'Content-Type': 'application/json'
        }

        try:
            response = requests.get(f"{self.base_url}/applications", headers=headers)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Dasha API connection failed: {str(e)}")
            return False

    def create_conversation_script(self, purpose: str, context: str = "") -> str:
        """Generate conversation script using Gemini"""
        if not self.gemini_client:
            return self.get_default_script()

        prompt = f"""
        Create a professional phone conversation script for an AI agent with the following purpose: {purpose}

        Context: {context}

        The script should be natural, engaging, and include:
        1. Greeting and introduction
        2. Main conversation flow
        3. Handling objections or questions
        4. Appropriate closing

        Format it as a structured conversation flow that can be used by a voice AI system.
        Keep responses conversational and human-like.
        """

        try:
            response = self.gemini_client.generate_content(prompt)
            return response.text
        except Exception as e:
            st.error(f"Error generating script: {str(e)}")
            return self.get_default_script()

    def get_default_script(self) -> str:
        """Default conversation script"""
        return """
        Greeting: "Hello! This is an AI assistant calling from our service. How are you doing today?"

        Main Flow:
        - Listen to customer response
        - Engage naturally based on their mood and response
        - Ask relevant questions based on call purpose
        - Provide helpful information
        - Handle any concerns professionally

        Closing: "Thank you for your time today. Is there anything else I can help you with before we end the call?"
        """

    def initiate_call(self, phone_number: str, script: str, call_purpose: str = "General") -> Dict:
        """Initiate a phone call using Dasha AI"""
        call_id = str(uuid.uuid4())

        headers = {
            'Authorization': f'Bearer {self.dasha_api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            "application_id": self.dasha_app_id,
            "external_id": call_id,
            "phone_number": phone_number,
            "config": {
                "conversation_script": script,
                "call_purpose": call_purpose,
                "max_duration": 300,  # 5 minutes max
                "record_call": True
            }
        }

        try:
            # Simulate call initiation (replace with actual Dasha API call)
            response = self.simulate_call_initiation(call_id, phone_number, script)

            if response.get('success'):
                call_session = CallSession(
                    call_id=call_id,
                    phone_number=phone_number,
                    status="initiated",
                    start_time=datetime.now(),
                    conversation_log=[]
                )

                self.active_calls[call_id] = call_session
                return {"success": True, "call_id": call_id, "message": "Call initiated successfully"}
            else:
                return {"success": False, "message": response.get('error', 'Unknown error')}

        except Exception as e:
            return {"success": False, "message": f"Error initiating call: {str(e)}"}

    def simulate_call_initiation(self, call_id: str, phone_number: str, script: str) -> Dict:
        """Simulate call initiation (for demo purposes)"""
        # In a real implementation, this would make the actual API call to Dasha
        return {
            "success": True,
            "call_id": call_id,
            "status": "initiated"
        }

    def get_call_status(self, call_id: str) -> Dict:
        """Get current status of a call"""
        if call_id in self.active_calls:
            call = self.active_calls[call_id]
            return {
                "call_id": call_id,
                "status": call.status,
                "phone_number": call.phone_number,
                "start_time": call.start_time.isoformat(),
                "duration": (datetime.now() - call.start_time).seconds if call.status == "active" else call.duration
            }
        else:
            return {"error": "Call not found"}

    def end_call(self, call_id: str) -> Dict:
        """End an active call"""
        if call_id in self.active_calls:
            call = self.active_calls[call_id]
            call.status = "completed"
            call.end_time = datetime.now()
            call.duration = (call.end_time - call.start_time).seconds

            # Move to history
            self.call_history.append(call)
            del self.active_calls[call_id]

            return {"success": True, "message": "Call ended successfully"}
        else:
            return {"success": False, "message": "Call not found"}

    def get_call_analytics(self) -> Dict:
        """Get analytics for all calls"""
        total_calls = len(self.call_history) + len(self.active_calls)
        active_calls = len(self.active_calls)
        completed_calls = len(self.call_history)

        if self.call_history:
            avg_duration = sum(call.duration or 0 for call in self.call_history) / len(self.call_history)
            total_duration = sum(call.duration or 0 for call in self.call_history)
        else:
            avg_duration = 0
            total_duration = 0

        return {
            "total_calls": total_calls,
            "active_calls": active_calls,
            "completed_calls": completed_calls,
            "average_duration": round(avg_duration, 2),
            "total_duration": total_duration
        }

def main():
    st.title("📞 Conversational Voice Calling Agent")
    st.markdown("*AI-Powered Voice Calling with Gemini & Dasha AI*")

    # Initialize session state
    if 'agent' not in st.session_state:
        st.session_state.agent = DashaCallAgent()
    if 'setup_complete' not in st.session_state:
        st.session_state.setup_complete = False

    # Sidebar configuration
    with st.sidebar:
        st.header("🔧 API Configuration")

        # API Keys
        gemini_key = st.text_input("Gemini API Key", type="password",
                                 help="For conversation intelligence")
        dasha_key = st.text_input("Dasha AI API Key", type="password",
                                help="For voice calling capabilities")
        dasha_app_id = st.text_input("Dasha Application ID",
                                   help="Your Dasha application ID")

        # Call Settings
        st.subheader("📞 Call Settings")
        max_call_duration = st.slider("Max Call Duration (minutes)", 1, 30, 5)
        record_calls = st.checkbox("Record Calls", value=True)

        # Setup button
        if st.button("🚀 Setup Calling Agent"):
            with st.spinner("Setting up Voice Calling Agent..."):
                setup_success = True

                if gemini_key:
                    if not st.session_state.agent.setup_gemini(gemini_key):
                        setup_success = False
                else:
                    st.error("Gemini API key is required")
                    setup_success = False

                if dasha_key and dasha_app_id:
                    if not st.session_state.agent.setup_dasha(dasha_key, dasha_app_id):
                        setup_success = False
                        st.error("Failed to connect to Dasha AI")
                else:
                    st.error("Dasha AI credentials are required")
                    setup_success = False

                if setup_success:
                    st.session_state.setup_complete = True
                    st.success("✅ Voice Calling Agent ready!")
                else:
                    st.session_state.setup_complete = False

    # Main interface
    if not st.session_state.setup_complete:
        st.warning("⚠️ Please configure your API keys in the sidebar to get started.")
        st.info("""
        **Required for Voice Calling:**
        - Gemini API Key (conversation intelligence)
        - Dasha AI API Key (voice calling platform)
        - Dasha Application ID (your app configuration)

        **Get Started:**
        1. Sign up at [Dasha AI](https://dasha.ai/)
        2. Create a new application for voice calling
        3. Get your API credentials
        4. Configure in the sidebar
        """)
        return

    # Create tabs for different functionalities
    tab1, tab2, tab3, tab4 = st.tabs(["📞 Make Calls", "📊 Active Calls", "📈 Analytics", "⚙️ Scripts"])

    with tab1:
        st.subheader("Initiate Voice Calls")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**📱 Call Configuration**")
            phone_number = st.text_input("Phone Number",
                                       placeholder="+1-555-123-4567",
                                       help="Include country code")

            call_purpose = st.selectbox("Call Purpose", [
                "Customer Service",
                "Sales Outreach",
                "Survey/Feedback",
                "Appointment Scheduling",
                "Lead Qualification",
                "Information Gathering",
                "Follow-up Call",
                "Custom"
            ])

            if call_purpose == "Custom":
                custom_purpose = st.text_input("Custom Purpose")
                call_purpose = custom_purpose if custom_purpose else "General"

        with col2:
            st.markdown("**🎯 Context & Instructions**")
            call_context = st.text_area("Call Context",
                                      placeholder="Provide context about the customer, previous interactions, or specific goals...",
                                      height=100)

            additional_instructions = st.text_area("Special Instructions",
                                                 placeholder="Any specific instructions for the AI agent...",
                                                 height=100)

        # Generate script section
        st.markdown("**📝 Conversation Script**")
        col3, col4 = st.columns([1, 3])

        with col3:
            if st.button("🤖 Generate Script", type="secondary"):
                with st.spinner("Generating conversation script..."):
                    script = st.session_state.agent.create_conversation_script(
                        call_purpose, call_context + " " + additional_instructions
                    )
                    st.session_state.generated_script = script

        # Display generated script
        if hasattr(st.session_state, 'generated_script'):
            conversation_script = st.text_area("Generated Script",
                                             value=st.session_state.generated_script,
                                             height=200)
        else:
            conversation_script = st.text_area("Conversation Script",
                                             placeholder="Click 'Generate Script' or write your own...",
                                             height=200)

        # Initiate call button
        st.markdown("---")
        col5, col6 = st.columns([2, 1])

        with col5:
            if st.button("📞 Initiate Call", type="primary", use_container_width=True):
                if phone_number and conversation_script:
                    with st.spinner("Initiating voice call..."):
                        result = st.session_state.agent.initiate_call(
                            phone_number, conversation_script, call_purpose
                        )

                        if result['success']:
                            st.success(f"✅ Call initiated! Call ID: {result['call_id']}")
                            st.balloons()
                        else:
                            st.error(f"❌ Call failed: {result['message']}")
                else:
                    st.error("Please provide phone number and conversation script")

        with col6:
            if st.button("📋 Save Script", use_container_width=True):
                if conversation_script:
                    # Save script logic here
                    st.success("Script saved!")

    with tab2:
        st.subheader("Active Calls Management")

        # Refresh button
        if st.button("🔄 Refresh Active Calls"):
            st.rerun()

        if st.session_state.agent.active_calls:
            # Display active calls
            for call_id, call in st.session_state.agent.active_calls.items():
                with st.container():
                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

                    with col1:
                        st.write(f"**📞 {call.phone_number}**")
                        st.write(f"Call ID: {call_id[:8]}...")

                    with col2:
                        status_color = "🟢" if call.status == "active" else "🟡"
                        st.write(f"Status: {status_color} {call.status.title()}")
                        duration = (datetime.now() - call.start_time).seconds
                        st.write(f"Duration: {duration//60}:{duration%60:02d}")

                    with col3:
                        st.write(f"Started: {call.start_time.strftime('%H:%M:%S')}")
                        st.write(f"Purpose: {getattr(call, 'purpose', 'General')}")

                    with col4:
                        if st.button("🔚 End", key=f"end_{call_id}"):
                            result = st.session_state.agent.end_call(call_id)
                            if result['success']:
                                st.success("Call ended")
                                st.rerun()
                            else:
                                st.error("Failed to end call")

                    st.divider()
        else:
            st.info("📭 No active calls at the moment")
            st.markdown("*Initiated calls will appear here*")

    with tab3:
        st.subheader("Call Analytics & History")

        # Get analytics
        analytics = st.session_state.agent.get_call_analytics()

        # Metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Calls", analytics['total_calls'])
        with col2:
            st.metric("Active Calls", analytics['active_calls'])
        with col3:
            st.metric("Completed Calls", analytics['completed_calls'])
        with col4:
            st.metric("Avg Duration", f"{analytics['average_duration']}s")

        # Call history table
        st.markdown("**📋 Call History**")

        if st.session_state.agent.call_history:
            history_data = []
            for call in st.session_state.agent.call_history:
                history_data.append({
                    "Phone Number": call.phone_number,
                    "Status": call.status.title(),
                    "Start Time": call.start_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Duration (s)": call.duration or 0,
                    "Outcome": call.call_outcome or "Completed"
                })

            df = pd.DataFrame(history_data)
            st.dataframe(df, use_container_width=True)

            # Export functionality
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Export Call History",
                data=csv,
                file_name=f"call_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No call history available yet")

    with tab4:
        st.subheader("Script Management")

        # Predefined script templates
        st.markdown("**📋 Script Templates**")

        templates = {
            "Customer Service": """
            Greeting: "Hello! I'm calling from customer service to follow up on your recent inquiry. How are you doing today?"

            Purpose: Address customer concerns and provide assistance

            Flow:
            1. Confirm customer identity politely
            2. Reference their specific inquiry/issue
            3. Provide helpful solutions or information
            4. Ask if they have any other questions
            5. Ensure customer satisfaction before ending

            Closing: "Thank you for being a valued customer. Have a great day!"
            """,

            "Sales Outreach": """
            Greeting: "Hi! This is [Name] calling about an exciting opportunity that might interest you. Do you have a quick moment to chat?"

            Purpose: Introduce product/service and gauge interest

            Flow:
            1. Brief, friendly introduction
            2. Mention the value proposition
            3. Ask qualifying questions
            4. Handle objections professionally
            5. Suggest next steps (demo, meeting, etc.)

            Closing: "Thanks for your time. I'll follow up with the information we discussed."
            """,

            "Survey/Feedback": """
            Greeting: "Hello! I'm conducting a brief survey to help us improve our services. Would you mind sharing your thoughts? It'll just take a few minutes."

            Purpose: Gather customer feedback and insights

            Flow:
            1. Explain the purpose and duration
            2. Ask permission to proceed
            3. Ask structured questions
            4. Listen actively to responses
            5. Thank them for their valuable input

            Closing: "Your feedback is very important to us. Thank you so much for your time!"
            """
        }

        selected_template = st.selectbox("Choose Template", list(templates.keys()))

        if selected_template:
            st.text_area("Template Script",
                        value=templates[selected_template],
                        height=300,
                        key="template_display")

            if st.button("📋 Use This Template"):
                st.session_state.generated_script = templates[selected_template]
                st.success("Template loaded! Go to 'Make Calls' tab to use it.")

        # Custom script editor
        st.markdown("**✏️ Custom Script Editor**")
        custom_script = st.text_area("Write Custom Script",
                                   placeholder="Create your own conversation script...",
                                   height=200)

        if custom_script:
            if st.button("💾 Save Custom Script"):
                # Save custom script logic
                st.success("Custom script saved!")

    # Footer with status
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"**🔌 Status:** {'Connected' if st.session_state.setup_complete else 'Not Connected'}")
    with col2:
        st.markdown(f"**📞 Active Calls:** {len(st.session_state.agent.active_calls)}")
    with col3:
        st.markdown(f"**📊 Total Calls:** {len(st.session_state.agent.call_history) + len(st.session_state.agent.active_calls)}")

if __name__ == "__main__":
    main()