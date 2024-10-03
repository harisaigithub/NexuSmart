import os
import csv
from gradientai import Gradient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set Gradient environment variables
access_token = os.getenv('GRADIENT_ACCESS_TOKEN')
workspace_id = os.getenv('GRADIENT_WORKSPACE_ID')

# Define the path to your CSV file
career_dataset_path = "main_app/truncated_career_recommender_dataset.csv"

def initialize_model():
    # Initialize Gradient
    gradient = Gradient(access_token=access_token, workspace_id=workspace_id)

    # Load the dataset
    print("Loading and formatting data...")
    formatted_data = []
    with open(career_dataset_path, encoding="utf-8-sig") as f:
        dataset_data = csv.DictReader(f, delimiter=",")
        for row in dataset_data:
            # Construct the prompt from the user's data
            user_data = f"Interests: {row['Interests']}, Skills: {row['Skills']}, Degree: {row['Undergraduate Course']}, Working: {row['Employment Status']}"
            # The response is the career path
            career_response = row['Career Path']

            # Format the data for fine-tuning
            formatted_entry = {
                "inputs": f"### User Data:\n{user_data}\n\n### Suggested Career Path:",
                "response": career_response
            }
            formatted_data.append(formatted_entry)

    # Get the base model from Gradient
    base = gradient.get_base_model(base_model_slug="nous-hermes2")

    # Create a model adapter for fine-tuning
    new_model_adapter = base.create_model_adapter(name="ai_career_chatbot")

    # Fine-tune the model adapter in chunks to prevent memory issues
    print("Fine-tuning model adapter...")
    chunk_lines = 20
    total_chunks = [formatted_data[x:x+chunk_lines] for x in range(0, len(formatted_data), chunk_lines)]
    for i, chunk in enumerate(total_chunks):
        try:
            print(f"Fine-tuning chunk {i+1} of {len(total_chunks)}")
            new_model_adapter.fine_tune(samples=chunk)
        except Exception as error:
            print(f"Error in fine-tuning chunk {i+1}: {error}")

    return new_model_adapter

def get_career_path(user_query):
    model = initialize_model()
    formatted_query = f"### User Data:\n{user_query}\n\n### Suggested Career Path:"
    response = model.complete(query=formatted_query, max_generated_token_count=50)
    return response.generated_output
