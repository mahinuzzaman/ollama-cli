"""Interactive session management for olla-cli."""

import json
import time
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import logging

from ..utils import TokenCounter

logger = logging.getLogger('olla-cli')


@dataclass
class Message:
    """Represents a single message in the conversation."""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: float = field(default_factory=time.time)
    token_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionContext:
    """Context information for a session."""
    current_file: Optional[Path] = None
    working_directory: Optional[Path] = None
    model: str = "codellama"
    temperature: float = 0.7
    context_length: int = 4096
    language: Optional[str] = None
    framework: Optional[str] = None
    project_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InteractiveSession:
    """Represents an interactive chat session."""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    messages: List[Message] = field(default_factory=list)
    context: SessionContext = field(default_factory=SessionContext)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Message:
        """Add a message to the session."""
        token_count = TokenCounter.estimate_tokens(content)
        message = Message(
            role=role,
            content=content,
            token_count=token_count,
            metadata=metadata or {}
        )
        self.messages.append(message)
        self.updated_at = time.time()
        return message
    
    def get_conversation_history(self, max_messages: Optional[int] = None) -> List[Message]:
        """Get conversation history, optionally limited to recent messages."""
        if max_messages is None:
            return self.messages.copy()
        return self.messages[-max_messages:]
    
    def get_total_tokens(self) -> int:
        """Calculate total tokens used in the session."""
        return sum(msg.token_count for msg in self.messages)
    
    def clear_history(self):
        """Clear conversation history."""
        self.messages.clear()
        self.updated_at = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            'session_id': self.session_id,
            'name': self.name,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'messages': [asdict(msg) for msg in self.messages],
            'context': asdict(self.context),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'InteractiveSession':
        """Create session from dictionary."""
        messages = [Message(**msg_data) for msg_data in data.get('messages', [])]
        
        # Handle Path objects in context
        context_data = data.get('context', {})
        if 'current_file' in context_data and context_data['current_file']:
            context_data['current_file'] = Path(context_data['current_file'])
        if 'working_directory' in context_data and context_data['working_directory']:
            context_data['working_directory'] = Path(context_data['working_directory'])
        
        context = SessionContext(**context_data)
        
        return cls(
            session_id=data.get('session_id', str(uuid.uuid4())),
            name=data.get('name', ''),
            created_at=data.get('created_at', time.time()),
            updated_at=data.get('updated_at', time.time()),
            messages=messages,
            context=context,
            metadata=data.get('metadata', {})
        )


class SessionManager:
    """Manages interactive sessions with persistence."""
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        """Initialize session manager.
        
        Args:
            sessions_dir: Directory to store session files. Defaults to ~/.olla-cli/sessions/
        """
        if sessions_dir is None:
            sessions_dir = Path.home() / '.olla-cli' / 'sessions'
        
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_session: Optional[InteractiveSession] = None
        self._session_cache: Dict[str, InteractiveSession] = {}
        
        # Create index file for quick session lookup
        self.index_file = self.sessions_dir / 'index.json'
        self._load_session_index()
    
    def _load_session_index(self):
        """Load session index for quick lookup."""
        if not self.index_file.exists():
            self._session_index = {}
            return
        
        try:
            with open(self.index_file, 'r') as f:
                self._session_index = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Failed to load session index: {e}")
            self._session_index = {}
    
    def _save_session_index(self):
        """Save session index."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self._session_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session index: {e}")
    
    def create_session(self, name: Optional[str] = None) -> InteractiveSession:
        """Create a new interactive session."""
        session = InteractiveSession()
        
        if name:
            session.name = name
        else:
            # Generate automatic name based on timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            session.name = f"Session {timestamp}"
        
        # Update index
        self._session_index[session.session_id] = {
            'name': session.name,
            'created_at': session.created_at,
            'updated_at': session.updated_at,
            'file_path': str(self.sessions_dir / f"{session.session_id}.json")
        }
        
        self.current_session = session
        self._session_cache[session.session_id] = session
        
        logger.info(f"Created new session: {session.name} ({session.session_id})")
        return session
    
    def save_session(self, session: Optional[InteractiveSession] = None) -> bool:
        """Save a session to disk."""
        if session is None:
            session = self.current_session
        
        if session is None:
            logger.error("No session to save")
            return False
        
        session_file = self.sessions_dir / f"{session.session_id}.json"
        
        try:
            with open(session_file, 'w') as f:
                # Custom serialization to handle Path objects
                session_dict = session.to_dict()
                
                # Convert Path objects to strings for JSON serialization
                if session_dict['context']['current_file']:
                    session_dict['context']['current_file'] = str(session_dict['context']['current_file'])
                if session_dict['context']['working_directory']:
                    session_dict['context']['working_directory'] = str(session_dict['context']['working_directory'])
                
                json.dump(session_dict, f, indent=2)
            
            # Update index
            self._session_index[session.session_id] = {
                'name': session.name,
                'created_at': session.created_at,
                'updated_at': session.updated_at,
                'file_path': str(session_file)
            }
            self._save_session_index()
            
            logger.info(f"Saved session: {session.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[InteractiveSession]:
        """Load a session from disk."""
        # Check cache first
        if session_id in self._session_cache:
            return self._session_cache[session_id]
        
        # Check if session exists in index
        if session_id not in self._session_index:
            return None
        
        session_file = Path(self._session_index[session_id]['file_path'])
        
        if not session_file.exists():
            logger.warning(f"Session file not found: {session_file}")
            # Remove from index
            del self._session_index[session_id]
            self._save_session_index()
            return None
        
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            session = InteractiveSession.from_dict(session_data)
            self._session_cache[session_id] = session
            
            logger.info(f"Loaded session: {session.name}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all available sessions."""
        sessions = []
        for session_id, info in self._session_index.items():
            sessions.append({
                'id': session_id,
                'name': info['name'],
                'created_at': info['created_at'],
                'updated_at': info['updated_at'],
                'created_str': datetime.fromtimestamp(info['created_at']).strftime("%Y-%m-%d %H:%M:%S"),
                'updated_str': datetime.fromtimestamp(info['updated_at']).strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Sort by updated time, most recent first
        sessions.sort(key=lambda x: x['updated_at'], reverse=True)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id not in self._session_index:
            return False
        
        session_file = Path(self._session_index[session_id]['file_path'])
        
        try:
            if session_file.exists():
                session_file.unlink()
            
            # Remove from index and cache
            del self._session_index[session_id]
            self._session_cache.pop(session_id, None)
            
            # Clear current session if it was deleted
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
            
            self._save_session_index()
            logger.info(f"Deleted session: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def search_sessions(self, query: str) -> List[Dict[str, Any]]:
        """Search sessions by name or content."""
        query = query.lower()
        matching_sessions = []
        
        for session_info in self.list_sessions():
            session_id = session_info['id']
            
            # Check name match
            if query in session_info['name'].lower():
                matching_sessions.append({**session_info, 'match_reason': 'name'})
                continue
            
            # Load session and check message content
            session = self.load_session(session_id)
            if session:
                for message in session.messages:
                    if query in message.content.lower():
                        matching_sessions.append({**session_info, 'match_reason': 'content'})
                        break
        
        return matching_sessions
    
    def get_session_stats(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a session."""
        session = self.load_session(session_id)
        if not session:
            return None
        
        user_messages = [msg for msg in session.messages if msg.role == 'user']
        assistant_messages = [msg for msg in session.messages if msg.role == 'assistant']
        
        return {
            'total_messages': len(session.messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_tokens': session.get_total_tokens(),
            'user_tokens': sum(msg.token_count for msg in user_messages),
            'assistant_tokens': sum(msg.token_count for msg in assistant_messages),
            'duration_minutes': (session.updated_at - session.created_at) / 60,
            'model': session.context.model,
            'context_length': session.context.context_length
        }
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """Clean up sessions older than specified days."""
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        sessions_to_delete = []
        for session_id, info in self._session_index.items():
            if info['updated_at'] < cutoff_time:
                sessions_to_delete.append(session_id)
        
        for session_id in sessions_to_delete:
            if self.delete_session(session_id):
                deleted_count += 1
        
        logger.info(f"Cleaned up {deleted_count} old sessions")
        return deleted_count