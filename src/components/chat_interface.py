import streamlit as st
from typing import List, Dict

class ChatInterface:
    def __init__(self):
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages = []
        if "current_prd_id" not in st.session_state:
            st.session_state.current_prd_id = None
    
    def display_chat_messages(self):
        """Display chat messages in the interface"""
        for message in st.session_state.chat_messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    def add_message(self, role: str, content: str):
        """Add a message to the chat history"""
        st.session_state.chat_messages.append({
            "role": role,
            "content": content
        })
    
    def clear_chat(self):
        """Clear chat history"""
        st.session_state.chat_messages = []
    
    def get_chat_history(self) -> List[Dict]:
        """Get current chat history"""
        return st.session_state.chat_messages
    
    def render_chat_input(self, placeholder: str = "Type your message here...") -> str:
        """Render chat input and return user input"""
        return st.chat_input(placeholder)
    
    def render_prd_creation_form(self):
        """Render form for initial PRD creation"""
        st.subheader("Create New PRD")
        
        with st.form("prd_creation_form"):
            user_input = st.text_area(
                "Describe your product idea or requirements:",
                height=150,
                help="Provide as much detail as possible about your product, target users, goals, and key features."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                use_template = st.checkbox("Use PRD template")
            with col2:
                include_examples = st.checkbox("Include example sections")
            
            submitted = st.form_submit_button("Generate PRD")
            
            if submitted and user_input:
                return {
                    "user_input": user_input,
                    "use_template": use_template,
                    "include_examples": include_examples
                }
        
        return None
    
    def render_prd_display(self, prd_content: str, title: str):
        """Render PRD content with formatting"""
        st.subheader(f"PRD: {title}")
        
        # Add download button
        st.download_button(
            label="Download PRD as Text",
            data=prd_content,
            file_name=f"{title.replace(' ', '_')}_PRD.txt",
            mime="text/plain"
        )
        
        # Display content
        st.markdown(prd_content)
    
    def render_version_history(self, versions: List[Dict]):
        """Render version history sidebar"""
        st.sidebar.subheader("Version History")
        
        for version in versions:
            with st.sidebar.expander(f"Version {version['version']} - {version['created_at'][:16]}"):
                if st.button(f"Load v{version['version']}", key=f"load_v{version['version']}"):
                    return version['version']
                
                if version.get('changes_summary'):
                    st.caption(f"Changes: {version['changes_summary']}")
        
        return None
    
    def render_prd_management(self, prds: List[Dict], prd_type: str = "product"):
        """Render PRD management interface"""
        type_label = "Product-Level PRDs" if prd_type == "product" else "Epic-Level PRDs"
        st.sidebar.subheader(type_label)
        
        if not prds:
            st.sidebar.info(f"No {type_label.lower()} found. Create one using the chat interface!")
            return None
        
        selected_prd = st.sidebar.selectbox(
            f"Select {type_label}:",
            options=[""] + [f"{prd['title']} (v{prd['version']})" for prd in prds],
            format_func=lambda x: "Select a PRD..." if x == "" else x
        )
        
        if selected_prd and selected_prd != "":
            # Extract PRD ID from selection
            prd_title = selected_prd.split(" (v")[0]
            selected_prd_data = next((prd for prd in prds if prd['title'] == prd_title), None)
            
            if selected_prd_data:
                st.session_state.current_prd_id = selected_prd_data['id']
                
                # Show PRD metadata
                if prd_type == "epic" and selected_prd_data.get('jira_epic_key'):
                    st.sidebar.info(f"🎯 Jira Epic: {selected_prd_data['jira_epic_key']}")
                
                if selected_prd_data.get('parent_prd_id'):
                    st.sidebar.info(f"🔗 Linked to Product PRD")
                
                return selected_prd_data['id']
        
        return None
    
    def render_action_buttons(self, prd_type: str = "product"):
        """Render action buttons for PRD operations"""
        if prd_type == "product":
            col1, col2, col3, col4, col5 = st.columns(5)
        else:
            col1, col2, col3, col4 = st.columns(4)
        
        actions = {}
        
        with col1:
            if st.button("💾 Save Version"):
                actions['save'] = True
        
        with col2:
            if st.button("✅ Approve PRD"):
                actions['approve'] = True
        
        with col3:
            if st.button("🔄 New PRD"):
                actions['new'] = True
        
        with col4:
            if st.button("🗑️ Clear Chat"):
                actions['clear_chat'] = True
        
        if prd_type == "product":
            with col5:
                if st.button("➕ Create Epic"):
                    actions['create_epic'] = True
        
        return actions
    
    def render_jira_epic_form(self):
        """Render form for linking Jira epic"""
        st.subheader("Link Jira Epic")
        
        with st.form("jira_epic_form"):
            jira_key = st.text_input(
                "Jira Epic Key:",
                placeholder="e.g., PROJ-123",
                help="Enter the Jira epic key to link with this PRD"
            )
            
            submitted = st.form_submit_button("Link Epic")
            
            if submitted and jira_key:
                return jira_key
        
        return None