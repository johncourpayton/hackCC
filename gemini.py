import os
import google.generativeai as genai
from dotenv import load_dotenv

# Configure the Gemini API with your API key
# It's recommended to set your API key as an environment variable
# For example: export GOOGLE_API_KEY="YOUR_API_KEY"
load_dotenv() # Load environment variables from .env file

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def generate_text_with_gemini(prompt_text):
    """
    Generates text using the Gemini API based on the provided prompt.
    """
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

if __name__ == "__main__":
    print("Gemini API Test File")
    print("--------------------")

    # Example usage:
    test_prompt = "Generate a study schedule for my assignments for the week ahead. I have 3 assignments due: calc2 chapter 11.1 , ethnic studies discussion board, and a history paper on ww2. help me plan my week!"
    print(f"Prompt: {test_prompt}\n")

    generated_story = generate_text_with_gemini(test_prompt)
    print(f"Generated Story:\n{generated_story}")

    print("\n--------------------")
    print("To run this script, ensure you have the 'google-generativeai' library installed:")
    print("pip install google-generativeai")
    print("And your GOOGLE_API_KEY environment variable is set.")
