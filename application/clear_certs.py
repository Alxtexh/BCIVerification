import os
import json

def clear_certificates():
    """Clear all stored certificates"""
    try:
        # Get the absolute path to the data directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        certificates_file = os.path.join(current_dir, "data", "certificates.json")
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(certificates_file), exist_ok=True)
        
        # Clear the certificates file
        with open(certificates_file, "w") as f:
            json.dump([], f)
        print("Certificates cleared successfully!")
        return True
    except Exception as e:
        print(f"Error clearing certificates: {e}")
        return False

if __name__ == "__main__":
    clear_certificates()