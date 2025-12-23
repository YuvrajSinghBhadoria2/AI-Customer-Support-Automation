"""Streamlit dashboard for human-in-the-loop ticket review."""

import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="AI Support Dashboard",
    page_icon="🎫",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .ticket-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin-bottom: 1rem;
    }
    .confidence-high { color: #28a745; }
    .confidence-medium { color: #ffc107; }
    .confidence-low { color: #dc3545; }
    .urgency-critical { background-color: #dc3545; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .urgency-high { background-color: #fd7e14; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .urgency-medium { background-color: #ffc107; color: black; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
    .urgency-low { background-color: #28a745; color: white; padding: 0.25rem 0.5rem; border-radius: 0.25rem; }
</style>
""", unsafe_allow_html=True)

# Title
st.title("🎫 AI Customer Support Dashboard")

# Sidebar
with st.sidebar:
    st.header("⚙️ Controls")
    
    # Ingest button
    if st.button("📥 Fetch New Emails", type="primary"):
        with st.spinner("Fetching emails..."):
            try:
                response = requests.post(f"{API_BASE_URL}/api/tickets/ingest")
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"✅ {data['message']}")
                else:
                    st.error(f"❌ Error: {response.text}")
            except Exception as e:
                st.error(f"❌ Connection error: {str(e)}")
    
    st.divider()
    
    # Filters
    st.header("🔍 Filters")
    status_filter = st.selectbox(
        "Status",
        ["All", "pending_review", "approved", "sent", "escalated", "closed"]
    )
    
    urgency_filter = st.selectbox(
        "Urgency",
        ["All", "low", "medium", "high", "critical"]
    )
    
    intent_filter = st.selectbox(
        "Intent",
        ["All", "billing", "technical_issue", "account_access", 
         "cancellation", "feature_request", "general_inquiry"]
    )
    
    st.divider()
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (30s)")
    
    st.divider()
    
    # Stats
    st.header("📊 Quick Stats")
    try:
        response = requests.get(f"{API_BASE_URL}/api/tickets")
        if response.status_code == 200:
            all_tickets = response.json()
            st.metric("Total Tickets", len(all_tickets))
            pending = len([t for t in all_tickets if t['status'] == 'pending_review'])
            st.metric("Pending Review", pending)
            escalated = len([t for t in all_tickets if t['status'] == 'escalated'])
            st.metric("Escalated", escalated)
    except:
        pass

# Main content
def fetch_tickets():
    """Fetch tickets from API with filters."""
    params = {}
    if status_filter != "All":
        params['status'] = status_filter
    if urgency_filter != "All":
        params['urgency'] = urgency_filter
    if intent_filter != "All":
        params['intent'] = intent_filter
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/tickets", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching tickets: {response.text}")
            return []
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return []

def get_confidence_class(confidence):
    """Get CSS class for confidence score."""
    if confidence >= 0.8:
        return "confidence-high"
    elif confidence >= 0.6:
        return "confidence-medium"
    else:
        return "confidence-low"

def display_ticket(ticket):
    """Display a single ticket card."""
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.subheader(f"#{ticket['id']} - {ticket['subject']}")
        
        with col2:
            urgency_class = f"urgency-{ticket['urgency']}" if ticket['urgency'] else ""
            st.markdown(f"<span class='{urgency_class}'>{ticket['urgency'].upper() if ticket['urgency'] else 'N/A'}</span>", 
                       unsafe_allow_html=True)
        
        with col3:
            st.write(f"**Status:** {ticket['status']}")
        
        # Ticket details
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**From:**", ticket['customer_email'])
            st.write("**Intent:**", ticket['intent'] or "N/A")
            st.write("**Team:**", ticket['assigned_team'] or "N/A")
            
            if ticket['confidence_score']:
                conf_class = get_confidence_class(ticket['confidence_score'])
                st.markdown(f"**Confidence:** <span class='{conf_class}'>{ticket['confidence_score']:.1%}</span>", 
                           unsafe_allow_html=True)
        
        with col2:
            st.write("**Created:**", ticket['created_at'][:19])
            if ticket['resolved_at']:
                st.write("**Resolved:**", ticket['resolved_at'][:19])
        
        # Original message
        with st.expander("📧 Original Message"):
            st.text_area("Body", ticket['body'], height=150, key=f"body_{ticket['id']}", disabled=True)
        
        # AI Reply
        if ticket['ai_reply']:
            with st.expander("🤖 AI Generated Reply", expanded=True):
                edited_reply = st.text_area(
                    "Reply (editable)",
                    ticket['ai_reply'],
                    height=200,
                    key=f"reply_{ticket['id']}"
                )
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("✅ Approve & Send", key=f"approve_{ticket['id']}", type="primary"):
                        try:
                            response = requests.put(
                                f"{API_BASE_URL}/api/tickets/{ticket['id']}/approve",
                                json={"edited_reply": edited_reply if edited_reply != ticket['ai_reply'] else None}
                            )
                            if response.status_code == 200:
                                st.success("✅ Email sent!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Error: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                
                with col2:
                    if st.button("🚨 Escalate", key=f"escalate_{ticket['id']}"):
                        try:
                            response = requests.put(f"{API_BASE_URL}/api/tickets/{ticket['id']}/escalate")
                            if response.status_code == 200:
                                st.success("🚨 Ticket escalated!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(f"Error: {response.text}")
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        # Feedback section for sent tickets
        if ticket['status'] == 'sent':
            with st.expander("💬 Feedback"):
                if ticket['feedback']:
                    st.write(f"**Rating:** {'⭐' * ticket['feedback_rating']}")
                    st.write(f"**Comment:** {ticket['feedback']}")
                else:
                    feedback_text = st.text_area("Feedback", key=f"feedback_text_{ticket['id']}")
                    rating = st.slider("Rating", 1, 5, 3, key=f"rating_{ticket['id']}")
                    if st.button("Submit Feedback", key=f"submit_feedback_{ticket['id']}"):
                        try:
                            response = requests.post(
                                f"{API_BASE_URL}/api/tickets/{ticket['id']}/feedback",
                                json={"feedback": feedback_text, "rating": rating}
                            )
                            if response.status_code == 200:
                                st.success("✅ Feedback submitted!")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
        
        st.divider()

# Fetch and display tickets
tickets = fetch_tickets()

if not tickets:
    st.info("📭 No tickets found. Click 'Fetch New Emails' to get started!")
else:
    st.write(f"**Showing {len(tickets)} ticket(s)**")
    
    # Display tickets
    for ticket in tickets:
        display_ticket(ticket)

# Auto-refresh
if auto_refresh:
    time.sleep(30)
    st.rerun()
