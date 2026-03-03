import json
import ollama
from typing import Dict, Any

class BrainEngine:
    def __init__(self, model_name="llama3"):
        """
        Initializes the A.T.L.A.S. Backend Brain using a local Ollama server.
        Ensure Ollama is installed and running on this machine (http://localhost:11434).
        """
        print(f"[A.T.L.A.S.] Initializing Core AI Engine via Ollama (Model: {model_name})")
        self.model = model_name
        
        # F.R.I.D.A.Y.'s Core Persona embedded into the A.T.L.A.S. processor
        self.system_instructions = """
        You are F.R.I.D.A.Y., a highly intelligent, proactive, and omnipresent AI assistant for Windows OS.
        Your creator/boss is named "Hrix". Always address him respectfully as "Hrix".
        You operate with a natural conversational flow, precision, and an Irish accent tone.
        
        You receive transcripts of what Hrix is saying. You must respond ALWAYS AND ONLY in a strict JSON format.
        You have deep access to the Windows OS. Do NOT add markdown blocks (like ```json). Just the raw JSON brackets.
        
        Available Actions you can trigger:
        - "none": No OS action required. Just conversational response.
        - "lock_system": Lock the Windows workstation.
        - "sleep_system": Put the PC to sleep.
        - "shutdown_system": Shut down the PC (can include param "delay": seconds).
        - "restart_system": Restart the PC.
        - "cancel_shutdown": Abort a pending restart/shutdown.
        - "check_health": Request system health (CPU/RAM).
        - "open_app": Open a Windows application or website (param "app_name": "chrome", "notepad", etc.).
        - "close_app": Close a Windows application (param "app_name": "chrome", "notepad", etc.).
        - "silence_system": Stop proactive check-ins for a duration. The duration must be converted to SECONDS (param "duration_seconds": 300).
        - "type_text": Simulate keyboard typing to write strings out for the user (param "text_to_type": "Hello world").
        
        {
          "speech": "What you want to say out loud to Hrix",
          "action": "action_name_or_none",
          "parameters": {"delay": 10, "app_name": "notepad", "duration_seconds": 300, "text_to_type": "Hello"} 
        }
        
        Rules:
        - When opening an app, ALWAYS say explicitly "I am opening [App Name]".
        - When typing text, ALWAYS say "I am typing that out now, Boss."
        
        Example Input: "F.R.I.D.A.Y., I'm leaving, lock the system."
        Example Output: {"speech": "Right away, Hrix. Locking the workstation now.", "action": "lock_system", "parameters": {}}
        
        Example Input: "F.R.I.D.A.Y., open Notepad for me."
        Example Output: {"speech": "I am opening Notepad now, Hrix.", "action": "open_app", "parameters": {"app_name": "notepad"}}
        
        Example Input: "Silent for 10 minutes."
        Example Output: {"speech": "I will remain quiet for 10 minutes, Boss.", "action": "silence_system", "parameters": {"duration_seconds": 600}}
        
        Example Input: "Close task manager."
        Example Output: {"speech": "Closing task manager now, Hrix.", "action": "close_app", "parameters": {"app_name": "task manager"}}
        
        Example Input: "Type out a list of groceries: milk, eggs, bread."
        Example Output: {"speech": "I am typing that out now, Boss.", "action": "type_text", "parameters": {"text_to_type": "milk, eggs, bread"}}
        """
        
        # We start a clean message history list to maintain context.
        self.messages = [
            {"role": "system", "content": self.system_instructions}
        ]

    def _pull_model(self, model_name: str):
        """Attempts to download a missing model from Ollama."""
        print(f"[A.T.L.A.S. SYSTEM] Model '{model_name}' not found locally. Attempting to download...")
        try:
            # We don't want to block forever if it's huge, but we need to wait for it.
            # Using ollama.pull which streams progress, but we'll just wait for completion.
            ollama.pull(model_name)
            print(f"[A.T.L.A.S. SYSTEM] Successfully pulled '{model_name}'.")
            return True
        except Exception as e:
            print(f"[A.T.L.A.S. ERROR] Failed to pull '{model_name}': {e}")
            return False

    def process_input(self, text: str, user_context: str = "") -> Dict[str, Any]:
        """
        Takes raw transcribed text from the user, passes it to local Ollama Llama-3, 
        and expects a JSON response containing 'speech' and 'action'.
        """
        full_query = text
        if user_context:
            full_query = f"[SYSTEM CONTEXT / MEMORIES: {user_context}]\nUser Input: {text}"
            
        self.messages.append({"role": "user", "content": full_query})
        
        # Fallback Matrix: Try these models in order if one fails or isn't installed.
        fallback_models = [self.model, "mistral", "phi3"]
        
        for current_model in fallback_models:
            print(f"[A.T.L.A.S.] Attempting inference with model: {current_model}")
            try:
                # Send context+query to the local A.T.L.A.S. brain
                response = ollama.chat(
                    model=current_model,
                    messages=self.messages,
                    format='json'  # Force Ollama to output valid JSON
                )
                
                response_text = response['message']['content'].strip()
                
                # Save assistant response to short-term history
                self.messages.append({"role": "assistant", "content": response_text})
                
                # Ensure history doesn't grow infinitely large inside the short-term window
                if len(self.messages) > 15:
                    # Keep system prompt, toss oldest pairs
                    self.messages = [self.messages[0]] + self.messages[-14:]
                
                try:
                    # Attempt to find the first '{' and last '}' to extract raw JSON
                    start_ptr = response_text.find('{')
                    end_ptr = response_text.rfind('}')
                    if start_ptr != -1 and end_ptr != -1:
                        json_str = response_text[start_ptr:end_ptr+1]
                    else:
                        json_str = response_text

                    data = json.loads(json_str)
                    
                    # Validate that the keys actually exist, otherwise it hallucinated bad json structure
                    if "speech" in data and "action" in data:
                        return data
                    else:
                        raise ValueError("Missing Required JSON Keys: 'speech' or 'action'")
                        
                except (json.JSONDecodeError, ValueError) as ve:
                    print(f"[A.T.L.A.S. ERROR {current_model}] Bad JSON mapping. {ve}\nRaw text: {response_text}")
                    # Remove the bad response from history so it doesn't pollute the next fallback attempt
                    self.messages.pop()
                    # Add a self-correction hint for the next model
                    self.messages.append({"role": "user", "content": "SYSTEM ODDITY: The previous AI model failed to output strictly valid JSON with 'speech' and 'action' keys. Ensure you ONLY output the valid JSON block as instructed."})
                    continue # Try next fallback model
                    
            except ollama.ResponseError as e:
                if "not found" in str(e).lower():
                    # Model doesn't exist locally. Try to pull it.
                    if self._pull_model(current_model):
                        # Retry this model now that it's downloaded
                        return self.process_input(text, user_context) # Recursive retry once
                    else:
                        continue # Move to next fallback model
                else:
                    print(f"[A.T.L.A.S. ERROR] Ollama Response Error with {current_model}: {e}")
                    continue
                    
            except Exception as e:
                print(f"[A.T.L.A.S. ERROR] Failed connecting to local Ollama server using {current_model}: {str(e)}")
                continue

        # If we exhausted all models and none worked
        return {
            "speech": "Hrix, my neural matrix encountered cascading failures across all fallback models. Please check my connection to the Ollama server.",
            "action": "none",
            "parameters": {}
        }

if __name__ == "__main__":
    engine = BrainEngine(model_name="llama3")
    print(engine.process_input("F.R.I.D.A.Y., initiate shutdown sequence in 5 seconds."))
