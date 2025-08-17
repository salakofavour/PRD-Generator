import streamlit as st
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from models.prd_model import PRDDatabase
from utils.llm_handler import LLMHandler
from components.chat_interface import ChatInterface

# Page configuration
st.set_page_config(
    page_title="PRD Generator",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize components
@st.cache_resource
def init_components():
    db = PRDDatabase()
    llm = LLMHandler()
    return db, llm

def main():
    st.title("📋 Product Requirements Document Generator")
    st.markdown("*Generate comprehensive PRDs through natural language interaction*")
    
    # Initialize components
    try:
        db, llm = init_components()
        chat_ui = ChatInterface()
    except Exception as e:
        st.error(f"Error initializing application: {str(e)}")
        st.info("Please check your .env file and ensure all dependencies are installed.")
        return
    
    # Sidebar for PRD management
    st.sidebar.title("PRD Management")
    
    # Load existing PRDs
    prds = db.get_all_prds()
    current_prd_id = chat_ui.render_prd_management(prds)
    
    # Initialize session state
    if "current_prd" not in st.session_state:
        st.session_state.current_prd = None
    if "prd_content" not in st.session_state:
        st.session_state.prd_content = ""
    
    # Display current PRD info
    if current_prd_id:
        current_prd = db.get_prd(current_prd_id)
        if current_prd:
            st.session_state.current_prd = current_prd
            st.session_state.prd_content = current_prd['content']
            st.info(f"Working on: **{current_prd['title']}** (Version {current_prd['version']})")
    
    # Chat messages
    st.subheader("💬 Chat Interface")
    chat_ui.display_chat_messages()
    
    # Chat input (must be outside all containers including tabs)
    if user_input := chat_ui.render_chat_input("Ask about your PRD or request changes..."):
        chat_ui.add_message("user", user_input)
        
        with st.spinner("Generating response..."):
            if st.session_state.current_prd is None:
                # Generate new PRD
                response = llm.generate_prd(user_input)
                
                # Save PRD
                title = f"PRD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                prd_id = db.save_prd(title, response, user_input)
                
                # Update session state
                st.session_state.current_prd = db.get_prd(prd_id)
                st.session_state.prd_content = response
                
                chat_ui.add_message("assistant", f"Generated new PRD: {title}")
            else:
                # Chat about existing PRD
                response = llm.chat_with_prd(
                    user_input, 
                    st.session_state.prd_content,
                    chat_ui.get_chat_history()
                )
                chat_ui.add_message("assistant", response)

    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["📋 PRD Content", "📚 PRD Library", "⚙️ Settings"])
    
    with tab1:
        
        if st.session_state.prd_content:
            # Action buttons
            actions = chat_ui.render_action_buttons()
            
            if actions.get('save'):
                if st.session_state.current_prd:
                    db.save_prd(
                        st.session_state.current_prd['title'],
                        st.session_state.prd_content,
                        st.session_state.current_prd['user_input'],
                        st.session_state.current_prd['id']
                    )
                    st.success("PRD version saved!")
                    st.rerun()
            
            if actions.get('approve'):
                if st.session_state.current_prd:
                    feedback = st.text_input("Approval feedback (optional):")
                    if st.button("Confirm Approval"):
                        db.approve_prd(st.session_state.current_prd['id'], feedback)
                        st.success("PRD approved for training data!")
                        st.rerun()
            
            if actions.get('new'):
                st.session_state.current_prd = None
                st.session_state.prd_content = ""
                chat_ui.clear_chat()
                st.rerun()
            
            if actions.get('clear_chat'):
                chat_ui.clear_chat()
                st.rerun()
            
            # Display PRD content
            chat_ui.render_prd_display(
                st.session_state.prd_content,
                st.session_state.current_prd['title'] if st.session_state.current_prd else "New PRD"
            )
            
            # Version history
            if st.session_state.current_prd:
                versions = db.get_prd_versions(st.session_state.current_prd['id'])
                selected_version = chat_ui.render_version_history(versions)
                
                if selected_version:
                    version_data = next((v for v in versions if v['version'] == selected_version), None)
                    if version_data:
                        st.session_state.prd_content = version_data['content']
                        st.rerun()
        else:
            st.info("👋 Start by typing your product idea in the chat to generate a PRD!")
            
            # Quick start form
            form_data = chat_ui.render_prd_creation_form()
            if form_data:
                with st.spinner("Generating PRD..."):
                    response = llm.generate_prd(form_data['user_input'])
                    
                    title = f"PRD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    prd_id = db.save_prd(title, response, form_data['user_input'])
                    
                    st.session_state.current_prd = db.get_prd(prd_id)
                    st.session_state.prd_content = response
                    
                    chat_ui.add_message("user", form_data['user_input'])
                    chat_ui.add_message("assistant", f"Generated PRD: {title}")
                    
                    st.rerun()
    
    with tab2:
        st.subheader("📚 PRD Library")
        
        if prds:
            for prd in prds:
                with st.expander(f"📋 {prd['title']} - Version {prd['version']} ({'✅ Approved' if prd['is_approved'] else '📝 Draft'})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Created:** {prd['created_at']}")
                        st.markdown(f"**Last Updated:** {prd['updated_at']}")
                        st.markdown(f"**Status:** {prd['status']}")
                        if prd['feedback']:
                            st.markdown(f"**Feedback:** {prd['feedback']}")
                    
                    with col2:
                        if st.button(f"Load {prd['title']}", key=f"load_{prd['id']}"):
                            st.session_state.current_prd = prd
                            st.session_state.prd_content = prd['content']
                            st.success(f"Loaded {prd['title']}")
                            st.rerun()
                    
                    # Show preview
                    preview = prd['content'][:500] + "..." if len(prd['content']) > 500 else prd['content']
                    st.markdown(f"**Preview:**\n{preview}")
        else:
            st.info("No PRDs found. Create your first PRD in the Chat & Generate tab!")
    
    with tab3:
        st.subheader("⚙️ Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🤖 AI Model Settings")
            st.info("Currently using OpenAI GPT-3.5-turbo")
            
            if st.button("Test API Connection"):
                try:
                    test_response = llm.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=10
                    )
                    print("test_response", test_response)
                    st.success("✅ API connection successful!")
                except Exception as e:
                    st.error(f"❌ API connection failed: {str(e)}")
        
        with col2:
            st.markdown("### 📊 Statistics")
            approved_prds = db.get_approved_prds()
            
            st.metric("Total PRDs", len(prds))
            st.metric("Approved PRDs", len(approved_prds))
            st.metric("Draft PRDs", len(prds) - len(approved_prds))
        
        st.markdown("### 🔧 Advanced Settings")
        
        if st.button("🧠 Suggest Improvements"):
            if st.session_state.current_prd and st.session_state.prd_content:
                approved_prds = [prd['content'] for prd in db.get_approved_prds()]
                if approved_prds:
                    with st.spinner("Analyzing PRD against approved examples..."):
                        suggestions = llm.suggest_improvements(st.session_state.prd_content, approved_prds)
                        st.markdown("### 💡 Improvement Suggestions")
                        st.markdown(suggestions)
                else:
                    st.warning("No approved PRDs available for comparison.")
            else:
                st.warning("Please load a PRD first.")
        
        if st.button("🗄️ Export All PRDs"):
            if prds:
                export_data = ""
                for prd in prds:
                    export_data += f"\n{'='*50}\n"
                    export_data += f"TITLE: {prd['title']}\n"
                    export_data += f"VERSION: {prd['version']}\n"
                    export_data += f"STATUS: {prd['status']}\n"
                    export_data += f"CREATED: {prd['created_at']}\n"
                    export_data += f"{'='*50}\n\n"
                    export_data += prd['content']
                    export_data += "\n\n"
                
                st.download_button(
                    label="Download All PRDs",
                    data=export_data,
                    file_name=f"all_prds_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()