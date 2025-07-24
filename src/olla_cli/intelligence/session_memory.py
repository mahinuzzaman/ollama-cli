"""Session Memory System for persistent context and learning."""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger('olla-cli.intelligence.memory')


class SessionMemory:
    """Manages persistent session memory and user preferences."""
    
    def __init__(self, memory_dir: Optional[str] = None):
        if memory_dir is None:
            self.memory_dir = Path.home() / '.olla-cli' / 'memory'
        else:
            self.memory_dir = Path(memory_dir)
        
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.interactions_file = self.memory_dir / 'interactions.jsonl'
        self.preferences_file = self.memory_dir / 'preferences.json'
        self.projects_file = self.memory_dir / 'projects.json'
        
        # In-memory cache for recent interactions
        self.recent_interactions: List[Dict[str, Any]] = []
        self.max_memory_items = 1000
        
        # Load existing data
        self._load_recent_interactions()
    
    async def record_interaction(self, interaction: Dict[str, Any]) -> None:
        """Record a user interaction."""
        interaction['timestamp'] = datetime.now().isoformat()
        
        # Add to in-memory cache
        self.recent_interactions.append(interaction)
        
        # Keep memory bounded
        if len(self.recent_interactions) > self.max_memory_items:
            self.recent_interactions = self.recent_interactions[-self.max_memory_items:]
        
        # Persist to disk
        try:
            with open(self.interactions_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(interaction) + '\n')
        except Exception as e:
            logger.error(f"Error saving interaction: {e}")
    
    async def get_recent_interactions(self, limit: int = 50, 
                                    since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get recent interactions, optionally filtered by time."""
        interactions = self.recent_interactions.copy()
        
        # Filter by time if specified
        if since:
            since_iso = since.isoformat()
            interactions = [i for i in interactions 
                          if i.get('timestamp', '') >= since_iso]
        
        # Return most recent first
        interactions.reverse()
        return interactions[:limit]
    
    async def search_interactions(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search interactions by content."""
        query_lower = query.lower()
        matching = []
        
        for interaction in self.recent_interactions:
            # Search in various fields
            searchable_text = ' '.join([
                str(interaction.get('type', '')),
                str(interaction.get('input', '')),
                str(interaction.get('parameters', {})),
                str(interaction.get('result', ''))
            ]).lower()
            
            if query_lower in searchable_text:
                matching.append(interaction)
        
        # Return most recent matches first
        matching.reverse()
        return matching[:limit]
    
    async def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences."""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading preferences: {e}")
        
        return {}
    
    async def update_user_preferences(self, preferences: Dict[str, Any]) -> None:
        """Update user preferences."""
        try:
            existing = await self.get_user_preferences()
            existing.update(preferences)
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(existing, f, indent=2)
                
            logger.info("User preferences updated")
        except Exception as e:
            logger.error(f"Error saving preferences: {e}")
    
    async def learn_from_interaction(self, interaction: Dict[str, Any]) -> None:
        """Learn patterns from user interactions to improve preferences."""
        
        # Learn language preferences
        if 'parameters' in interaction and 'language' in interaction['parameters']:
            language = interaction['parameters']['language']
            await self._update_language_preference(language)
        
        # Learn framework preferences
        if 'parameters' in interaction and 'framework' in interaction['parameters']:
            framework = interaction['parameters']['framework']
            await self._update_framework_preference(framework)
        
        # Learn review focus preferences
        if interaction.get('type') == 'code_review' and 'parameters' in interaction:
            focus = interaction['parameters'].get('focus')
            if focus:
                await self._update_review_focus_preference(focus)
    
    async def _update_language_preference(self, language: str) -> None:
        """Update language usage statistics."""
        prefs = await self.get_user_preferences()
        
        if 'language_usage' not in prefs:
            prefs['language_usage'] = {}
        
        prefs['language_usage'][language] = prefs['language_usage'].get(language, 0) + 1
        
        # Set preferred language to most used
        most_used = max(prefs['language_usage'].items(), key=lambda x: x[1])
        prefs['preferred_language'] = most_used[0]
        
        await self.update_user_preferences(prefs)
    
    async def _update_framework_preference(self, framework: str) -> None:
        """Update framework usage statistics."""
        prefs = await self.get_user_preferences()
        
        if 'framework_usage' not in prefs:
            prefs['framework_usage'] = {}
        
        prefs['framework_usage'][framework] = prefs['framework_usage'].get(framework, 0) + 1
        
        # Set preferred framework to most used
        most_used = max(prefs['framework_usage'].items(), key=lambda x: x[1])
        prefs['preferred_framework'] = most_used[0]
        
        await self.update_user_preferences(prefs)
    
    async def _update_review_focus_preference(self, focus: str) -> None:
        """Update review focus preferences."""
        prefs = await self.get_user_preferences()
        
        if 'review_focus_usage' not in prefs:
            prefs['review_focus_usage'] = {}
        
        prefs['review_focus_usage'][focus] = prefs['review_focus_usage'].get(focus, 0) + 1
        
        await self.update_user_preferences(prefs)
    
    async def get_project_memory(self, project_path: str) -> Dict[str, Any]:
        """Get memory for a specific project."""
        try:
            if self.projects_file.exists():
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    projects = json.load(f)
                    return projects.get(project_path, {})
        except Exception as e:
            logger.error(f"Error loading project memory: {e}")
        
        return {}
    
    async def update_project_memory(self, project_path: str, memory: Dict[str, Any]) -> None:
        """Update memory for a specific project."""
        try:
            projects = {}
            if self.projects_file.exists():
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    projects = json.load(f)
            
            if project_path not in projects:
                projects[project_path] = {}
            
            projects[project_path].update(memory)
            projects[project_path]['last_accessed'] = datetime.now().isoformat()
            
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(projects, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving project memory: {e}")
    
    def _load_recent_interactions(self) -> None:
        """Load recent interactions from disk."""
        try:
            if not self.interactions_file.exists():
                return
            
            # Load recent interactions (last 7 days)
            cutoff = datetime.now() - timedelta(days=7)
            cutoff_iso = cutoff.isoformat()
            
            with open(self.interactions_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            interaction = json.loads(line)
                            if interaction.get('timestamp', '') >= cutoff_iso:
                                self.recent_interactions.append(interaction)
                        except json.JSONDecodeError:
                            continue
            
            # Keep only the most recent ones
            if len(self.recent_interactions) > self.max_memory_items:
                self.recent_interactions = self.recent_interactions[-self.max_memory_items:]
                
            logger.info(f"Loaded {len(self.recent_interactions)} recent interactions")
            
        except Exception as e:
            logger.error(f"Error loading interactions: {e}")
    
    async def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up old interaction data."""
        try:
            if not self.interactions_file.exists():
                return
            
            cutoff = datetime.now() - timedelta(days=days_to_keep)
            cutoff_iso = cutoff.isoformat()
            
            # Read and filter interactions
            kept_interactions = []
            with open(self.interactions_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            interaction = json.loads(line)
                            if interaction.get('timestamp', '') >= cutoff_iso:
                                kept_interactions.append(interaction)
                        except json.JSONDecodeError:
                            continue
            
            # Write back the filtered interactions
            with open(self.interactions_file, 'w', encoding='utf-8') as f:
                for interaction in kept_interactions:
                    f.write(json.dumps(interaction) + '\n')
            
            logger.info(f"Cleaned up old interactions, kept {len(kept_interactions)} items")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        stats = {
            'total_interactions': len(self.recent_interactions),
            'memory_usage_mb': self._get_memory_size_mb(),
            'oldest_interaction': None,
            'newest_interaction': None,
            'interaction_types': {}
        }
        
        if self.recent_interactions:
            timestamps = [i.get('timestamp') for i in self.recent_interactions if i.get('timestamp')]
            if timestamps:
                stats['oldest_interaction'] = min(timestamps)
                stats['newest_interaction'] = max(timestamps)
            
            # Count interaction types
            for interaction in self.recent_interactions:
                itype = interaction.get('type', 'unknown')
                stats['interaction_types'][itype] = stats['interaction_types'].get(itype, 0) + 1
        
        return stats
    
    def _get_memory_size_mb(self) -> float:
        """Get total memory usage in MB."""
        total_size = 0
        
        for file_path in [self.interactions_file, self.preferences_file, self.projects_file]:
            if file_path.exists():
                total_size += file_path.stat().st_size
        
        return total_size / (1024 * 1024)  # Convert to MB


class SessionManager:
    """Manages multiple session memories and contexts."""
    
    def __init__(self):
        self.current_session: Optional[SessionMemory] = None
        self.session_id: Optional[str] = None
        
    async def start_session(self, session_id: Optional[str] = None) -> SessionMemory:
        """Start a new session or resume existing one."""
        if session_id is None:
            from uuid import uuid4
            session_id = str(uuid4())
        
        self.session_id = session_id
        self.current_session = SessionMemory()
        
        # Record session start
        await self.current_session.record_interaction({
            'type': 'session_start',
            'session_id': session_id
        })
        
        return self.current_session
    
    async def end_session(self) -> None:
        """End the current session."""
        if self.current_session and self.session_id:
            await self.current_session.record_interaction({
                'type': 'session_end',
                'session_id': self.session_id
            })
        
        self.current_session = None
        self.session_id = None
    
    def get_current_session(self) -> Optional[SessionMemory]:
        """Get the current session memory."""
        return self.current_session