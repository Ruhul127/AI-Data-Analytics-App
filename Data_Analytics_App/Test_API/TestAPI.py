import openai

def test_openai_api_key(api_key):
    # Set the API key
    openai.api_key = api_key

    try:
        # Make a simple API request to list models
        models = openai.Model.list()
        
        # If the request is successful, the API key is valid
        print("✅ The API key is valid!")
        return True
    except openai.error.AuthenticationError:
        # If the API key is invalid, an AuthenticationError will be raised
        print("❌ The API key is invalid.")
        return False
    except Exception as e:
        # Handle other potential errors
        print(f"❌ An error occurred: {e}")
        return False

if __name__ == "__main__":
    # Replace with your OpenAI API key
    api_key = ""

    # Test the API key
    test_openai_api_key(api_key)