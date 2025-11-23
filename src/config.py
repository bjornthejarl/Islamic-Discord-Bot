"""
Configuration module for Discord Verify Bot.
Loads environment variables and provides centralized configuration.
"""

import os
from typing import Optional


class Config:
    """Bot configuration loaded from environment variables."""
    
    # Required environment variables
    DISCORD_TOKEN: Optional[str] = os.getenv("DISCORD_TOKEN")
    
    # Role IDs for verifiers (users who can run the commands)
    FEMALE_VERIFIER_ROLE_ID: int = 1438678339786244096
    MALE_VERIFIER_ROLE_ID: int = 1438678549358706781
    
    # Role IDs to assign to verified users
    FEMALE_ROLE_ID: int = 1438734916929196054
    MALE_ROLE_ID: int = 1438734872670769323
    
    # Role IDs to remove when verified
    FEMALE_REMOVE_ROLE_ID: int = 1438758944322355200
    MALE_REMOVE_ROLE_ID: int = 1438734829192740955
    
    @classmethod
    def validate(cls) -> bool:
        """Validate that all required configuration is present."""
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN environment variable is required")
        
        # Validate role IDs are positive integers
        role_ids = [
            cls.FEMALE_VERIFIER_ROLE_ID,
            cls.MALE_VERIFIER_ROLE_ID,
            cls.FEMALE_ROLE_ID,
            cls.MALE_ROLE_ID,
            cls.FEMALE_REMOVE_ROLE_ID,
            cls.MALE_REMOVE_ROLE_ID
        ]
        
        for role_id in role_ids:
            if not isinstance(role_id, int) or role_id <= 0:
                raise ValueError(f"Invalid role ID: {role_id}")
        
        return True