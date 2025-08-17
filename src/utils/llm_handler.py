import openai
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class LLMHandler:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for PRD generation"""
        return """You are an expert Product Requirements Document (PRD) generator. Your role is to help project managers, product owners, and stakeholders create comprehensive PRDs that serve as the single source of truth throughout the product development process.

Key guidelines for PRD generation:
1. Create detailed, comprehensive documents unless templates are specified
2. Ensure requirements are clear for development, design, and testing teams
3. Include all essential PRD sections: Overview, Goals, Features, Requirements, etc.
4. Use clear, unambiguous language
5. Structure information logically and hierarchically
6. Include acceptance criteria where appropriate
7. Consider technical feasibility and business value

PRD Structure Template:
1. **Product Overview**
   - Product vision and mission
   - Target audience and user personas
   - Problem statement and solution

2. **Goals and Objectives**
   - Business objectives
   - User goals
   - Success metrics and KPIs

3. **Features and Functionality**
   - Core features (detailed descriptions)
   - User stories and use cases
   - Feature prioritization

4. **Technical Requirements**
   - System requirements
   - Performance requirements
   - Security and compliance needs
   - Integration requirements

5. **User Experience Requirements**
   - UI/UX guidelines
   - Accessibility requirements
   - User journey mapping

6. **Constraints and Assumptions**
   - Technical constraints
   - Business constraints
   - Timeline and resource constraints

7. **Success Criteria and Metrics**
   - Definition of done
   - Testing requirements
   - Launch criteria

8. **Dependencies and Risks**
   - External dependencies
   - Risk assessment and mitigation

Always ask clarifying questions if the user input lacks sufficient detail for any section."""

    def generate_prd(self, user_input: str, context: str = "") -> str:
        """Generate a PRD based on user input"""
        messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        
        if context:
            messages.append({"role": "assistant", "content": f"Previous context: {context}"})
        
        messages.append({
            "role": "user", 
            "content": f"Please generate a comprehensive Product Requirements Document based on this input: {user_input}"
        })
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=3000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating PRD: {str(e)}"
    
    def chat_with_prd(self, user_message: str, prd_content: str, chat_history: List[Dict]) -> str:
        """Chat about an existing PRD for iterations"""
        messages = [
            {"role": "system", "content": f"""You are helping to iterate and improve a Product Requirements Document. 
            
Current PRD Content:
{prd_content}

Guidelines:
- Help users refine, expand, or modify sections of the PRD
- Suggest improvements based on best practices
- Answer questions about the PRD content
- Maintain the PRD structure and quality
- Be specific and actionable in your suggestions"""},
        ]
        
        # Add chat history
        for msg in chat_history[-10:]:  # Keep last 10 messages for context
            messages.append(msg)
        
        messages.append({"role": "user", "content": user_message})
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1500,
                temperature=0.4
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error in chat: {str(e)}"
    
    def suggest_improvements(self, prd_content: str, approved_prds: List[str]) -> str:
        """Suggest improvements based on approved PRDs"""
        if not approved_prds:
            return "No approved PRDs available for comparison."
        
        # Sample a few approved PRDs for context
        sample_prds = approved_prds[:3] if len(approved_prds) > 3 else approved_prds
        approved_context = "\n\n---\n\n".join(sample_prds)
        
        messages = [
            {"role": "system", "content": f"""Analyze the current PRD against these approved, high-quality PRDs and suggest specific improvements:

Approved PRDs for reference:
{approved_context}

Provide specific, actionable suggestions to improve the current PRD based on best practices from the approved examples."""},
            {"role": "user", "content": f"Current PRD to improve:\n{prd_content}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating suggestions: {str(e)}"