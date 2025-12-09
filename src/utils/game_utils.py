"""
Game utility functions for the Discord bot.
Handles game content, logic, and rewards.
"""

import json
import os
import asyncio
import aiofiles
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class GameUtils:
    """Utility class for game system operations."""
    
    def __init__(self, data_path: str = "src/data"):
        self.data_path = data_path
        self.game_content = self._load_game_content()
    
    def _load_game_content(self) -> Dict[str, Any]:
        """Load game content from JSON files."""
        content = {
            "quiz": self._load_quiz_questions(),
            "verse_match": self._load_verse_matches(),
            "hadith": self._load_hadith_trivia()
        }
        return content
    
    def _load_quiz_questions(self) -> List[Dict[str, Any]]:
        """Load quiz questions from file or return default if file doesn't exist."""
        quiz_file = os.path.join(self.data_path, "games", "quiz_questions.json")
        
        if os.path.exists(quiz_file):
            try:
                with open(quiz_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading quiz questions: {e}")
        
        # Return default questions if file doesn't exist
        return self._get_default_quiz_questions()
    
    def _load_verse_matches(self) -> List[Dict[str, Any]]:
        """Load verse matching game content."""
        verse_file = os.path.join(self.data_path, "games", "verse_matches.json")
        
        if os.path.exists(verse_file):
            try:
                with open(verse_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading verse matches: {e}")
        
        # Return default verse matches
        return self._get_default_verse_matches()
    
    def _load_hadith_trivia(self) -> List[Dict[str, Any]]:
        """Load hadith trivia content."""
        hadith_file = os.path.join(self.data_path, "games", "hadith_trivia.json")
        
        if os.path.exists(hadith_file):
            try:
                with open(hadith_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading hadith trivia: {e}")
        
        # Return default hadith trivia
        return self._get_default_hadith_trivia()

    def get_reciter_challenge(self) -> Dict[str, Any]:
        """Get a random reciter challenge."""
        # Using a hardcoded list of famous reciters and sample verses (Fatihah/Baqarah beginnings usually safe/available)
        # Source: EveryAyah (Public Domain/Open License)
        reciters = [
            {
                "name": "Mishary Rashid Alafasy", 
                "url": "https://everyayah.com/data/Alafasy_128kbps/001001.mp3",
                "id": "alafasy"
            },
            {
                "name": "Abdul Basit (Mujawwad)", 
                "url": "https://everyayah.com/data/Abdul_Basit_Mujawwad_128kbps/001001.mp3",
                "id": "abdulbasit"
            },
            {
                "name": "Saud Al-Shuraim", 
                "url": "https://everyayah.com/data/Saood_ash-Shuraym_128kbps/001001.mp3",
                "id": "shuraim"
            },
            {
                "name": "Maher Al-Muaiqly", 
                "url": "https://everyayah.com/data/MaherAlMuaiqly128kbps/001001.mp3",
                "id": "maher"
            }
        ]
        
        correct = random.choice(reciters)
        
        # Create options
        options = [r["name"] for r in reciters]
        random.shuffle(options)
        
        return {
            "audio_url": correct["url"],
            "correct_name": correct["name"],
            "correct_index": options.index(correct["name"]),
            "options": options,
            "difficulty": "medium",
            "points": 30
        }
    
    def _get_default_quiz_questions(self) -> List[Dict[str, Any]]:
        """Return default Islamic quiz questions."""
        return [
            {
                "question_id": "quiz_001",
                "question": "Which surah is known as the 'Heart of the Quran'?",
                "options": [
                    "Surah Al-Fatihah",
                    "Surah Al-Baqarah",
                    "Surah Yasin", 
                    "Surah Al-Ikhlas"
                ],
                "correct_answer": 2,
                "explanation": "Surah Yasin is often called the 'Heart of the Quran' due to its profound meanings and central importance.",
                "difficulty": "medium",
                "points": 25,
                "category": "quran",
                "tags": ["surah_names", "importance"]
            },
            {
                "question_id": "quiz_002",
                "question": "Who narrated the famous Hadith: 'Actions are judged by intentions'?",
                "options": [
                    "Abu Huraira",
                    "Umar ibn Al-Khattab",
                    "Aisha bint Abi Bakr",
                    "Ali ibn Abi Talib"
                ],
                "correct_answer": 1,
                "explanation": "This important Hadith about intentions was narrated by Umar ibn Al-Khattab and is found in Sahih al-Bukhari.",
                "difficulty": "easy",
                "points": 15,
                "category": "hadith",
                "tags": ["intentions", "foundational"]
            },
            {
                "question_id": "quiz_003",
                "question": "How many times do Muslims pray each day?",
                "options": [
                    "3 times",
                    "5 times", 
                    "7 times",
                    "10 times"
                ],
                "correct_answer": 1,
                "explanation": "Muslims perform 5 daily prayers: Fajr, Dhuhr, Asr, Maghrib, and Isha.",
                "difficulty": "easy",
                "points": 10,
                "category": "prayer",
                "tags": ["salah", "worship"]
            },
            {
                "question_id": "quiz_004",
                "question": "Which prophet is known for building the Kaaba?",
                "options": [
                    "Prophet Adam",
                    "Prophet Ibrahim",
                    "Prophet Musa", 
                    "Prophet Muhammad"
                ],
                "correct_answer": 1,
                "explanation": "Prophet Ibrahim (Abraham) and his son Ismail built the Kaaba in Mecca as the first house of worship for Allah.",
                "difficulty": "medium",
                "points": 20,
                "category": "prophets",
                "tags": ["kaaba", "ibrahim"]
            },
            {
                "question_id": "quiz_005", 
                "question": "What is the first month of the Islamic calendar?",
                "options": [
                    "Ramadan",
                    "Muharram",
                    "Shawwal",
                    "Dhul-Hijjah"
                ],
                "correct_answer": 1,
                "explanation": "Muharram is the first month of the Islamic Hijri calendar and is one of the four sacred months.",
                "difficulty": "easy",
                "points": 15,
                "category": "calendar",
                "tags": ["hijri", "months"]
            }
        ]
    
    def _get_default_verse_matches(self) -> List[Dict[str, Any]]:
        """Return default Quran verse matching content."""
        return [
            {
                "verse_id": "verse_001",
                "verse_text": "In the name of Allah, the Entirely Merciful, the Especially Merciful.",
                "surah_name": "Al-Fatihah",
                "surah_number": 1,
                "verse_number": 1,
                "hint": "The opening verse of the Quran",
                "points": 20,
                "difficulty": "easy"
            },
            {
                "verse_id": "verse_002",
                "verse_text": "Allah does not burden a soul beyond that it can bear...",
                "surah_name": "Al-Baqarah",
                "surah_number": 2,
                "verse_number": 286,
                "hint": "From the longest surah in the Quran",
                "points": 25,
                "difficulty": "medium"
            },
            {
                "verse_id": "verse_003", 
                "verse_text": "And We have certainly created man in the best of stature.",
                "surah_name": "At-Tin",
                "surah_number": 95,
                "verse_number": 4,
                "hint": "Surah named after a fruit",
                "points": 30,
                "difficulty": "medium"
            }
        ]
    
    def _get_default_hadith_trivia(self) -> List[Dict[str, Any]]:
        """Return default hadith trivia content."""
        return [
            {
                "hadith_id": "hadith_001",
                "question": "Complete this famous Hadith: 'Seek knowledge from...'",
                "options": [
                    "...the Quran only",
                    "...the cradle to the grave",
                    "...reliable scholars only", 
                    "...any available source"
                ],
                "correct_answer": 1,
                "explanation": "The full Hadith is: 'Seek knowledge from the cradle to the grave.'",
                "points": 20,
                "type": "completion"
            },
            {
                "hadith_id": "hadith_002",
                "question": "Which collection is known as 'The Authentic' and considered the most reliable Hadith collection?",
                "options": [
                    "Sahih al-Bukhari",
                    "Sunan Abu Dawood",
                    "Musnad Ahmad",
                    "Muwatta Malik"
                ],
                "correct_answer": 0,
                "explanation": "Sahih al-Bukhari is considered the most authentic Hadith collection after the Quran.",
                "points": 25,
                "type": "knowledge"
            },
            {
                "hadith_id": "hadith_003",
                "question": "Who is the narrator of this Hadith: 'The strong believer is better and more beloved to Allah than the weak believer...'?",
                "options": [
                    "Abu Huraira",
                    "Umar ibn Al-Khattab", 
                    "Aisha",
                    "Abu Bakr"
                ],
                "correct_answer": 0,
                "explanation": "This Hadith about strength was narrated by Abu Huraira.",
                "points": 20,
                "type": "narrator"
            }
        ]
    
    def get_quiz_question(self, category: str = None, difficulty: str = None) -> Optional[Dict[str, Any]]:
        """Get a random quiz question with optional filters."""
        questions = self.game_content["quiz"]
        
        # Filter by category if specified
        if category:
            questions = [q for q in questions if q.get("category") == category]
        
        # Filter by difficulty if specified
        if difficulty:
            questions = [q for q in questions if q.get("difficulty") == difficulty]
        
        if not questions:
            return None
        
        return random.choice(questions)
    
    def get_verse_match(self, difficulty: str = None) -> Optional[Dict[str, Any]]:
        """Get a random verse matching challenge."""
        verses = self.game_content["verse_match"]
        
        if difficulty:
            verses = [v for v in verses if v.get("difficulty") == difficulty]
        
        if not verses:
            return None
        
        verse = random.choice(verses)
        
        # Generate wrong options (other surah names)
        all_surahs = list(set([v["surah_name"] for v in self.game_content["verse_match"]]))
        wrong_surahs = [s for s in all_surahs if s != verse["surah_name"]]
        wrong_options = random.sample(wrong_surahs, min(3, len(wrong_surahs)))
        
        # Combine options and shuffle
        options = wrong_options + [verse["surah_name"]]
        random.shuffle(options)
        
        verse["options"] = options
        verse["correct_index"] = options.index(verse["surah_name"])
        
        return verse
    
    def get_hadith_trivia(self, trivia_type: str = None) -> Optional[Dict[str, Any]]:
        """Get a random hadith trivia question."""
        trivia_list = self.game_content["hadith"]
        
        if trivia_type:
            trivia_list = [t for t in trivia_list if t.get("type") == trivia_type]
        
        if not trivia_list:
            return None
        
        return random.choice(trivia_list)
    
    def calculate_game_rewards(self, game_type: str, difficulty: str = "medium", performance: float = 1.0) -> Dict[str, int]:
        """Calculate rewards for game completion."""
        base_rewards = {
            "quiz": {"coins": 25, "xp": 20},
            "verse_match": {"coins": 30, "xp": 25},
            "hadith_trivia": {"coins": 20, "xp": 15}
        }
        
        difficulty_multipliers = {
            "easy": 0.7,
            "medium": 1.0,
            "hard": 1.5
        }
        
        base = base_rewards.get(game_type, {"coins": 20, "xp": 15})
        multiplier = difficulty_multipliers.get(difficulty, 1.0) * performance
        
        return {
            "coins": int(base["coins"] * multiplier),
            "xp": int(base["xp"] * multiplier)
        }


class GameSession:
    """Class to manage active game sessions."""
    
    def __init__(self):
        self.active_sessions = {}
    
    def create_session(self, user_id: int, game_type: str, data: Dict[str, Any]) -> str:
        """Create a new game session."""
        session_id = f"{user_id}_{game_type}_{int(datetime.utcnow().timestamp())}"
        self.active_sessions[session_id] = {
            "user_id": user_id,
            "game_type": game_type,
            "data": data,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=10)
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a game session by ID."""
        session = self.active_sessions.get(session_id)
        
        if not session:
            return None
        
        # Check if session expired
        if datetime.utcnow() > session["expires_at"]:
            del self.active_sessions[session_id]
            return None
        
        return session
    
    def end_session(self, session_id: str) -> bool:
        """End a game session."""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Clean up expired game sessions."""
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self.active_sessions.items()
            if now > session["expires_at"]
        ]
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired game sessions")