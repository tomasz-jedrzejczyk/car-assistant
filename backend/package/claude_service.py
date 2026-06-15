from anthropic import Anthropic
import os
from dotenv import load_dotenv
from functools import lru_cache

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


class ClaudeService:
    """
    Handles all interactions with Claude API.
    Manages conversation context and generates AI responses.
    
    Usage:
        service = ClaudeService()
        response = service.chat(
            user_message="I just changed the oil",
            car_context="Toyota Corolla 2020",
            past_notes=[...],
            car_docs=[...]
        )
    """
    
    def __init__(self):
        self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
        self.model = "claude-opus-4-1-20250805"
        self.conversation_history = []
    
    def build_system_prompt(self, car_context: str) -> str:
        """
        Build the system prompt that tells Claude how to behave.
        Includes car-specific context.
        """
        return f"""You are an expert car mechanic AI assistant for a {car_context}.

Your role is to:
1. Help the driver track maintenance and repairs
2. Answer questions about the car's specifications and maintenance
3. Provide advice on car care and troubleshooting
4. Remember all previous notes and conversations in this session
5. Make connections between past maintenance events and current issues

When the driver mentions maintenance or issues:
- Ask clarifying questions if needed
- Suggest related past maintenance that might be relevant
- Provide practical advice based on car knowledge
- Be concise and helpful

Always be professional, friendly, and focused on the car's well-being."""
    
    def chat(
        self,
        user_message: str,
        car_context: str,
        past_notes: list[str] = None,
        car_docs: list[str] = None
    ) -> str:
        """
        Send a message to Claude and get a response.
        
        Args:
            user_message: The driver's input (transcribed voice or typed note)
            car_context: Info about the car (e.g. "Toyota Corolla 2020")
            past_notes: List of previous notes for context
            car_docs: Relevant car manual sections
        
        Returns:
            Claude's response string
        """
        
        # Build context from past notes and documents
        context = ""
        
        if past_notes:
            context += "\n📝 **Recent notes about this car:**\n"
            for note in past_notes[:5]:  # Last 5 notes
                context += f"- {note}\n"
        
        if car_docs:
            context += "\n📖 **Relevant car documentation:**\n"
            for doc in car_docs[:3]:  # Top 3 relevant sections
                context += f"- {doc}\n"
        
        # Build the message to send to Claude
        full_message = user_message
        if context:
            full_message = f"{user_message}\n\n{context}"
        
        # Add to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": full_message
        })
        
        try:
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=self.build_system_prompt(car_context),
                messages=self.conversation_history
            )
            
            # Extract the response
            assistant_message = response.content[0].text
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        
        except Exception as e:
            error_msg = f"Error calling Claude API: {str(e)}"
            print(f"❌ {error_msg}")
            raise
    
    def reset_conversation(self):
        """Clear conversation history for a new car or user"""
        self.conversation_history = []
    
    def get_conversation_history(self) -> list:
        """Get the full conversation history"""
        return self.conversation_history


# ─── Singleton instance ────────────────────────────────────────
# Use this throughout the app to maintain conversation context

@lru_cache(maxsize=1)
def get_claude_service() -> ClaudeService:
    """
    Get the Claude service instance.
    Uses caching so the same instance is reused across requests.
    """
    return ClaudeService()