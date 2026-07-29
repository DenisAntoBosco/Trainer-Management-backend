# Mock Session Store for Development
# This stores the current logged-in user to simulate authentication

# Global variable to store current session (in production, use Redis/database)
current_session = {
    "user_id": None,
    "email": None,
    "role": None
}

def set_current_user(user_id: str, email: str, role: str):
    """Set the current logged-in user"""
    global current_session
    current_session = {
        "user_id": user_id,
        "email": email,
        "role": role
    }

def get_current_user():
    """Get the current logged-in user"""
    global current_session
    return current_session.copy()

def clear_session():
    """Clear the current session"""
    global current_session
    current_session = {
        "user_id": None,
        "email": None,
        "role": None
    }