import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).with_name(".env"))

from .graph import create_graph

def run_agent():
    # 1. Compile the graph once
    app = create_graph()
    
    print("--- Welcome to the AI Research Agent ---")
    print("(Type 'exit' or 'quit' to stop)")

    while True:
        # 2. Get input from the user
        user_topic = input("\nEnter the topic you want to research: ").strip()

        # 3. Check for exit command
        if user_topic.lower() in ['exit', 'quit', 'q']:
            print("Goodbye!")
            break

        if not user_topic:
            print("Please enter a valid topic.")
            continue

        # 4. Invoke the agent
        print(f"\nProcessing research for: {user_topic}...")
        try:
            result = app.invoke({"topic": user_topic})
            
            # 5. Display the results
            print("\n" + "="*50)
            print(f"RESEARCH SUMMARY FOR: {user_topic.upper()}")
            print("="*50)
            print(result["summary"])
            print("="*50)
            
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    run_agent()