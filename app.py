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
    
    # PRD Type Selection
    prd_type = st.sidebar.selectbox(
        "PRD Type", 
        ["Product-Level PRD", "Epic-Level PRD"],
        help="Choose between Product-Level (master reference) or Epic-Level (specific Jira epic) PRD"
    )
    
    # Load existing PRDs based on type
    if prd_type == "Product-Level PRD":
        prds = db.get_product_level_prds()
        current_prd_id = chat_ui.render_prd_management(prds, prd_type="product")
    else:
        # For Epic-Level PRDs, first show Product-Level PRDs to select parent
        product_prds = db.get_product_level_prds()
        if product_prds:
            selected_product = st.sidebar.selectbox(
                "Select Parent Product PRD",
                options=[""] + [f"{prd['title']} (ID: {prd['id'][:8]})" for prd in product_prds],
                help="Epic-Level PRDs inherit from a Product-Level PRD"
            )
            
            if selected_product:
                parent_id = selected_product.split("ID: ")[1].split(")")[0]
                # Find the full parent ID
                parent_prd = next((prd for prd in product_prds if prd['id'].startswith(parent_id)), None)
                if parent_prd:
                    st.session_state.parent_prd = parent_prd
                    epic_prds = db.get_epic_prds_by_parent(parent_prd['id'])
                    current_prd_id = chat_ui.render_prd_management(epic_prds, prd_type="epic")
                else:
                    current_prd_id = None
            else:
                current_prd_id = None
        else:
            st.sidebar.warning("Create a Product-Level PRD first!")
            current_prd_id = None
    
    # Initialize session state
    if "current_prd" not in st.session_state:
        st.session_state.current_prd = None
    if "prd_content" not in st.session_state:
        st.session_state.prd_content = ""
    if "current_prd_type" not in st.session_state:
        st.session_state.current_prd_type = "product"
    if "parent_prd" not in st.session_state:
        st.session_state.parent_prd = None
    
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
                # Generate new PRD based on type
                if prd_type == "Product-Level PRD":
                    response = llm.generate_product_level_prd(user_input)
                    title = f"Product_PRD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    prd_id = db.save_prd(title, response, user_input, prd_type="product")
                else:
                    # Epic-Level PRD
                    if hasattr(st.session_state, 'parent_prd') and st.session_state.parent_prd:
                        response = llm.generate_epic_level_prd(user_input, st.session_state.parent_prd['content'])
                        title = f"Epic_PRD_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                        prd_id = db.create_epic_prd(title, response, user_input, st.session_state.parent_prd['id'])
                    else:
                        st.error("Please select a Parent Product PRD first!")
                        return
                
                # Update session state
                st.session_state.current_prd = db.get_prd(prd_id)
                st.session_state.prd_content = response
                st.session_state.current_prd_type = "product" if prd_type == "Product-Level PRD" else "epic"
                
                chat_ui.add_message("assistant", f"Generated new {prd_type}: {title}")
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
            current_type = st.session_state.current_prd.get('prd_type', 'product') if st.session_state.current_prd else 'product'
            actions = chat_ui.render_action_buttons(current_type)
            
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
            
            if actions.get('create_epic'):
                if st.session_state.current_prd and st.session_state.current_prd.get('prd_type') == 'product':
                    st.session_state.show_epic_creation = True
                    st.rerun()
            
            # Handle Epic Creation
            if st.session_state.get('show_epic_creation'):
                st.subheader("Create New Epic PRD")
                
                with st.form("epic_creation_form"):
                    epic_title = st.text_input("Epic Title:")
                    epic_description = st.text_area("Epic Description:", height=100)
                    jira_key = st.text_input("Jira Epic Key (optional):", placeholder="e.g., PROJ-123")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        create_epic = st.form_submit_button("Create Epic PRD")
                    with col2:
                        cancel_epic = st.form_submit_button("Cancel")
                    
                    if create_epic and epic_title and epic_description:
                        with st.spinner("Creating Epic PRD..."):
                            epic_response = llm.generate_epic_level_prd(
                                f"Epic Title: {epic_title}\n\nDescription: {epic_description}",
                                st.session_state.current_prd['content'],
                                jira_key
                            )
                            
                            epic_prd_id = db.create_epic_prd(
                                epic_title, 
                                epic_response, 
                                epic_description, 
                                st.session_state.current_prd['id'],
                                jira_key if jira_key else None
                            )
                            
                            st.success(f"Created Epic PRD: {epic_title}")
                            st.session_state.show_epic_creation = False
                            st.rerun()
                    
                    if cancel_epic:
                        st.session_state.show_epic_creation = False
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
        
        # Show Product-Level PRDs
        product_prds = db.get_product_level_prds()
        
        if product_prds:
            st.markdown("### 🏭 Product-Level PRDs")
            for prd in product_prds:
                prd_type_badge = "🏭 Product" 
                approval_badge = "✅ Approved" if prd['is_approved'] else "📝 Draft"
                
                with st.expander(f"{prd_type_badge} {prd['title']} - Version {prd['version']} ({approval_badge})"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Type:** Product-Level PRD")
                        st.markdown(f"**Created:** {prd['created_at']}")
                        st.markdown(f"**Last Updated:** {prd['updated_at']}")
                        st.markdown(f"**Status:** {prd['status']}")
                        if prd.get('technical_stack'):
                            st.markdown(f"**Tech Stack:** {prd['technical_stack'][:100]}...")
                        if prd['feedback']:
                            st.markdown(f"**Feedback:** {prd['feedback']}")
                    
                    with col2:
                        if st.button(f"Load", key=f"load_prod_{prd['id']}"):
                            st.session_state.current_prd = prd
                            st.session_state.prd_content = prd['content']
                            st.success(f"Loaded {prd['title']}")
                            st.rerun()
                    
                    # Show Epic PRDs for this Product PRD
                    epic_prds = db.get_epic_prds_by_parent(prd['id'])
                    if epic_prds:
                        st.markdown(f"**📎 Linked Epic PRDs ({len(epic_prds)}):**")
                        for epic in epic_prds:
                            epic_badge = "🎯 Epic"
                            jira_info = f" | Jira: {epic['jira_epic_key']}" if epic.get('jira_epic_key') else ""
                            st.markdown(f"  - {epic_badge} {epic['title']}{jira_info}")
                    
                    # Show preview
                    preview = prd['content'][:300] + "..." if len(prd['content']) > 300 else prd['content']
                    st.markdown(f"**Preview:**\n{preview}")
            
            # Show all Epic PRDs grouped by parent
            st.markdown("### 🎯 Epic-Level PRDs")
            all_epics = []
            for product_prd in product_prds:
                epics = db.get_epic_prds_by_parent(product_prd['id'])
                for epic in epics:
                    epic['parent_title'] = product_prd['title']
                    all_epics.append(epic)
            
            if all_epics:
                for epic in all_epics:
                    epic_badge = "🎯 Epic"
                    approval_badge = "✅ Approved" if epic['is_approved'] else "📝 Draft"
                    jira_info = f" | Jira: {epic['jira_epic_key']}" if epic.get('jira_epic_key') else ""
                    
                    with st.expander(f"{epic_badge} {epic['title']} - Version {epic['version']} ({approval_badge}){jira_info}"):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**Type:** Epic-Level PRD")
                            st.markdown(f"**Parent PRD:** {epic['parent_title']}")
                            st.markdown(f"**Created:** {epic['created_at']}")
                            st.markdown(f"**Last Updated:** {epic['updated_at']}")
                            st.markdown(f"**Status:** {epic['status']}")
                            if epic.get('jira_epic_key'):
                                st.markdown(f"**Jira Epic:** {epic['jira_epic_key']}")
                        
                        with col2:
                            if st.button(f"Load", key=f"load_epic_{epic['id']}"):
                                st.session_state.current_prd = epic
                                st.session_state.prd_content = epic['content']
                                st.success(f"Loaded {epic['title']}")
                                st.rerun()
                        
                        # Show preview
                        preview = epic['content'][:300] + "..." if len(epic['content']) > 300 else epic['content']
                        st.markdown(f"**Preview:**\n{preview}")
            else:
                st.info("No Epic PRDs found. Create Epic PRDs from Product-Level PRDs!")
        else:
            st.info("No PRDs found. Create your first Product-Level PRD in the Chat interface!")
    
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
            all_prds = db.get_all_prds()
            product_prds = db.get_product_level_prds()
            approved_prds = db.get_approved_prds()
            
            # Calculate epic PRDs count
            epic_count = 0
            for product_prd in product_prds:
                epic_count += len(db.get_epic_prds_by_parent(product_prd['id']))
            
            st.metric("Total PRDs", len(all_prds))
            st.metric("Product-Level PRDs", len(product_prds))
            st.metric("Epic-Level PRDs", epic_count)
            st.metric("Approved PRDs", len(approved_prds))
            st.metric("Draft PRDs", len(all_prds) - len(approved_prds))
        
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