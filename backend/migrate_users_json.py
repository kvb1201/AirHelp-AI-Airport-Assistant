#!/usr/bin/env python3
"""
Migration Script: Clean users.json

PURPOSE:
    Remove ephemeral fields from users.json that cause contamination.

WHAT IT DOES:
    1. Load users.json
    2. Remove ephemeral fields (intent, mode, selected, last_results, destination)
    3. Keep only persistent fields
    4. Save cleaned users.json
    5. Create backup

USAGE:
    python backend/migrate_users_json.py

SAFE:
    Creates backup before modifying users.json
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# Paths
BACKEND_DIR = Path(__file__).parent
USERS_JSON_PATH = BACKEND_DIR / "app" / "data" / "users.json"
BACKUP_DIR = BACKEND_DIR / "app" / "data" / "backups"

# Persistent fields (keep these)
PERSISTENT_FIELDS = {
    "user_id",
    "created_at",
    "updated_at",
    "flight_number",
    "boarding_time",
    "departure_time",
    "terminal",
    "gate",
    "location",
    "source",
    "alerts_sent",
    "_operational_brief",
}

# Ephemeral fields (remove these)
EPHEMERAL_FIELDS = {
    "intent",
    "mode",
    "selected",
    "last_results",
    "destination",
    "behavior",
}


def create_backup():
    """Create backup of users.json before migration."""
    BACKUP_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"users_backup_{timestamp}.json"
    
    shutil.copy2(USERS_JSON_PATH, backup_path)
    print(f"✅ Backup created: {backup_path}")
    
    return backup_path


def load_users():
    """Load users.json."""
    if not USERS_JSON_PATH.exists():
        print(f"❌ users.json not found at: {USERS_JSON_PATH}")
        return None
    
    with open(USERS_JSON_PATH, "r", encoding="utf-8") as f:
        users = json.load(f)
    
    print(f"✅ Loaded {len(users)} users from users.json")
    return users


def clean_user_context(user_id: str, context: dict) -> dict:
    """Clean single user context."""
    cleaned = {}
    removed = []
    
    for key, value in context.items():
        if key in PERSISTENT_FIELDS:
            cleaned[key] = value
        elif key in EPHEMERAL_FIELDS:
            removed.append(key)
        else:
            # Unknown field - keep it but warn
            print(f"⚠️  Unknown field '{key}' for user {user_id}, keeping it")
            cleaned[key] = value
    
    if removed:
        print(f"🧹 User {user_id}: Removed {removed}")
    
    return cleaned


def migrate_users(users: dict) -> dict:
    """Migrate all users."""
    cleaned_users = {}
    
    for user_id, context in users.items():
        cleaned_users[user_id] = clean_user_context(user_id, context)
    
    return cleaned_users


def save_users(users: dict):
    """Save cleaned users.json."""
    with open(USERS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved cleaned users.json")


def print_summary(original: dict, cleaned: dict):
    """Print migration summary."""
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    
    total_fields_removed = 0
    
    for user_id in original.keys():
        original_fields = set(original[user_id].keys())
        cleaned_fields = set(cleaned[user_id].keys())
        removed_fields = original_fields - cleaned_fields
        
        if removed_fields:
            total_fields_removed += len(removed_fields)
            print(f"\nUser: {user_id}")
            print(f"  Removed: {', '.join(removed_fields)}")
    
    print(f"\n✅ Total fields removed: {total_fields_removed}")
    print(f"✅ Users migrated: {len(cleaned)}")
    print("\n" + "=" * 60)


def main():
    """Run migration."""
    print("=" * 60)
    print("USERS.JSON MIGRATION - CONTAMINATION FIX")
    print("=" * 60)
    print()
    print("This script removes ephemeral fields from users.json:")
    print(f"  - {', '.join(EPHEMERAL_FIELDS)}")
    print()
    print("These fields will be moved to ephemeral session store.")
    print()
    
    # Load
    users = load_users()
    if users is None:
        return
    
    # Backup
    backup_path = create_backup()
    
    # Migrate
    print("\n🔄 Migrating users...")
    cleaned_users = migrate_users(users)
    
    # Save
    save_users(cleaned_users)
    
    # Summary
    print_summary(users, cleaned_users)
    
    print("\n✅ Migration complete!")
    print(f"📁 Backup saved at: {backup_path}")
    print(f"📁 Cleaned users.json at: {USERS_JSON_PATH}")
    print()
    print("⚠️  IMPORTANT: Restart the backend server to apply changes.")


if __name__ == "__main__":
    main()
