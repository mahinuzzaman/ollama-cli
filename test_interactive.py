#!/usr/bin/env python3
"""Test script for interactive mode functionality."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from olla_cli.interactive_session import SessionManager, InteractiveSession, Message


def test_session_manager():
    """Test basic session manager functionality."""
    print("🧪 Testing Session Manager...")
    
    # Create session manager
    sessions_dir = Path.home() / '.olla-cli' / 'sessions'
    sessions_dir.mkdir(parents=True, exist_ok=True)
    
    manager = SessionManager()
    
    # Create a test session
    session = manager.create_session("Test Session")
    print(f"✅ Created session: {session.name} ({session.session_id[:8]})")
    
    # Add some messages
    session.add_message("user", "Hello, can you explain this code: print('hello')")
    session.add_message("assistant", "This code prints 'hello' to the console using Python's print function.")
    session.add_message("user", "Can you make it more complex?")
    session.add_message("assistant", "Sure! Here's a more complex version:\n\n```python\ndef greet(name, greeting='Hello'):\n    print(f'{greeting}, {name}!')\n\ngreet('World')\n```")
    
    print(f"✅ Added {len(session.messages)} messages to session")
    print(f"📊 Total tokens: {session.get_total_tokens()}")
    
    # Save session
    if manager.save_session(session):
        print(f"✅ Session saved successfully")
    else:
        print(f"❌ Failed to save session")
    
    # List sessions
    sessions = manager.list_sessions()
    print(f"✅ Found {len(sessions)} sessions:")
    for s in sessions:
        print(f"  {s['id'][:8]}: {s['name']} ({s['updated_str']})")
    
    # Load session
    loaded_session = manager.load_session(session.session_id)
    if loaded_session:
        print(f"✅ Loaded session: {loaded_session.name}")
        print(f"📝 Messages: {len(loaded_session.messages)}")
    else:
        print(f"❌ Failed to load session")
    
    # Search sessions
    search_results = manager.search_sessions("code")
    print(f"✅ Search results for 'code': {len(search_results)} matches")
    
    # Session stats
    stats = manager.get_session_stats(session.session_id)
    if stats:
        print(f"✅ Session stats: {stats['total_messages']} messages, {stats['total_tokens']} tokens")
    
    print("🎉 Session manager tests completed!")


def test_completions():
    """Test auto-completion functionality."""
    print("\n🧪 Testing Auto-Completion...")
    
    try:
        from olla_cli.interactive_repl import OllaCompleter
        from prompt_toolkit.document import Document
        
        completer = OllaCompleter()
        
        # Test command completion
        doc = Document("exp")
        completions = list(completer.get_completions(doc, None))
        print(f"✅ Completions for 'exp': {[c.text for c in completions]}")
        
        # Test interactive command completion
        doc = Document("/he")
        completions = list(completer.get_completions(doc, None))
        print(f"✅ Completions for '/he': {[c.text for c in completions]}")
        
        # Test option completion
        doc = Document("explain --detail-")
        completions = list(completer.get_completions(doc, None))
        print(f"✅ Completions for '--detail-': {[c.text for c in completions]}")
        
        print("🎉 Completion tests completed!")
        
    except ImportError as e:
        print(f"❌ Completion test skipped due to import error: {e}")


if __name__ == "__main__":
    test_session_manager()
    test_completions()