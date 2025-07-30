import sys
import os
import subprocess
import json
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QMessageBox, QMainWindow, QVBoxLayout, 
                              QHBoxLayout, QMenu, QDialog, QLineEdit, QPushButton, 
                              QWidget, QLabel, QGridLayout, QSpacerItem, QSizePolicy, 
                              QScrollArea)
from PySide6.QtCore import Qt, QSize, QEvent, Signal, QObject

# Assuming these imports exist
from manager import LoginWindow
from hash import hash_password, verify_password, save_hashed_password, load_hashed_password
from pass_changer import ChangePasswordDialog


DESKTOP_SPACING = 13

@dataclass
class FileSystemItem:
    """Base class for file system items"""
    name: str
    full_path: str
    item_type: str  # 'file' or 'folder'
    
    @property
    def display_name(self) -> str:
        """Return the display name (without prefix for folders)"""
        if self.item_type == 'folder' and self.name.startswith('-__'):
            return self.name[3:]
        return self.name
    
    @property
    def directory(self) -> str:
        """Return the directory containing this item"""
        return os.path.dirname(self.full_path)


@dataclass
class FileItem(FileSystemItem):
    """Represents a file"""
    def __post_init__(self):
        self.item_type = 'file'
    
    @property
    def password_file_path(self) -> str:
        """Return the path to the password file for this file"""
        # Use the actual directory where the file is located
        file_dir = os.path.dirname(os.path.join(self.full_path, self.name))
        return os.path.join(file_dir, "content.bin")
    
    @property
    def content_file_path(self) -> str:
        """Return the path to the content file for this file"""
        # Use the actual directory where the file is located
        file_dir = os.path.dirname(os.path.join(self.full_path, self.name))
        print("CONTENT FİLE Path : "+ os.path.join(file_dir, "content.html"))
        return os.path.join(file_dir, "content.html")


@dataclass
class FolderItem(FileSystemItem):
    """Represents a folder"""
    def __post_init__(self):
        self.item_type = 'folder'
    
    @property
    def real_folder_name(self) -> str:
        """Return the folder name without the -__ prefix"""
        if self.name.startswith('-__'):
            return self.name[3:]
        return self.name


@dataclass
class HistoryItem:
    """Represents a history item"""
    name: str
    full_path: str
    last_accessed: str
    access_count: int = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'full_path': self.full_path,
            'last_accessed': self.last_accessed,
            'access_count': self.access_count
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HistoryItem':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            full_path=data['full_path'], 
            last_accessed=data['last_accessed'],
            access_count=data.get('access_count', 1)
        )


@dataclass
class PinnedItem:
    """Represents a pinned item"""
    name: str
    full_path: str
    pinned_at: str
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'full_path': self.full_path,
            'pinned_at': self.pinned_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'PinnedItem':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            full_path=data['full_path'],
            pinned_at=data['pinned_at']
        )


class PinManager:
    """Manages pinned files"""
    
    def __init__(self, pin_file: str = "pinned.json"):
        self.pin_file = pin_file
        self.pinned_items: List[PinnedItem] = []
        self.load_pins()
    
    def load_pins(self):
        """Load pinned items from file"""
        if os.path.exists(self.pin_file):
            try:
                with open(self.pin_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.pinned_items = [PinnedItem.from_dict(item) for item in data]
                    # Sort by pinned date (most recent first)
                    self.pinned_items.sort(key=lambda x: x.pinned_at, reverse=True)
            except Exception as e:
                print(f"Error loading pins: {e}")
                self.pinned_items = []
        else:
            self.pinned_items = []
    
    def save_pins(self):
        """Save pinned items to file"""
        try:
            with open(self.pin_file, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in self.pinned_items], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving pins: {e}")
    
    def pin_file_item(self, file_item: FileItem):
        """Pin a file"""
        current_time = datetime.now().isoformat()
        
        # Check if file is already pinned
        if self.is_pinned(file_item.full_path):
            return False  # Already pinned
        
        # Add new pinned item
        pinned_item = PinnedItem(
            name=file_item.display_name,
            full_path=file_item.full_path,
            pinned_at=current_time
        )
        self.pinned_items.append(pinned_item)
        
        # Sort by pinned date (most recent first)
        self.pinned_items.sort(key=lambda x: x.pinned_at, reverse=True)
        
        # Keep only last 20 items
        self.pinned_items = self.pinned_items[:20]
        
        # Save to file
        self.save_pins()
        return True
    
    def unpin_file(self, file_path: str):
        """Unpin a file"""
        self.pinned_items = [item for item in self.pinned_items if item.full_path != file_path]
        self.save_pins()
    
    def is_pinned(self, file_path: str) -> bool:
        """Check if a file is pinned"""
        return any(item.full_path == file_path for item in self.pinned_items)
    
    def get_pinned_files(self) -> List[PinnedItem]:
        """Get all pinned files"""
        return self.pinned_items
    
    def clear_pins(self):
        """Clear all pinned items"""
        self.pinned_items = []
        self.save_pins()


class HistoryManager:
    """Manages file access history"""
    
    def __init__(self, history_file: str = "history.json"):
        self.history_file = history_file
        self.history_items: List[HistoryItem] = []
        self.load_history()
    
    def load_history(self):
        """Load history from file"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history_items = [HistoryItem.from_dict(item) for item in data]
                    # Sort by last accessed (most recent first)
                    self.history_items.sort(key=lambda x: x.last_accessed, reverse=True)
            except Exception as e:
                print(f"Error loading history: {e}")
                self.history_items = []
        else:
            self.history_items = []
    
    def save_history(self):
        """Save history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([item.to_dict() for item in self.history_items], f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def add_file_to_history(self, file_item: FileItem):
        """Add a file to history"""
        current_time = datetime.now().isoformat()
        
        # Check if file already exists in history
        existing_item = None
        for item in self.history_items:
            if item.full_path == file_item.full_path:
                existing_item = item
                break
        
        if existing_item:
            # Update existing item
            existing_item.last_accessed = current_time
            existing_item.access_count += 1
        else:
            # Add new item
            history_item = HistoryItem(
                name=file_item.display_name,
                full_path=file_item.full_path,
                last_accessed=current_time
            )
            self.history_items.append(history_item)
        
        # Sort by last accessed (most recent first)
        self.history_items.sort(key=lambda x: x.last_accessed, reverse=True)
        
        # Keep only last 50 items
        self.history_items = self.history_items[:50]
        
        # Save to file
        self.save_history()
    
    def get_recent_files(self, limit: int = 20) -> List[HistoryItem]:
        """Get recent files from history"""
        return self.history_items[:limit]
    
    def clear_history(self):
        """Clear all history"""
        self.history_items = []
        self.save_history()


class FileSystemManager:
    """Manages file system operations and item tracking"""
    
    def __init__(self):
        self.items: Dict[str, FileSystemItem] = {}
        self.current_path = "data/"
    
    def scan_directory(self, base_path: str) -> List[FileSystemItem]:
        """Scan directory and return list of FileSystemItem objects"""
        if not os.path.exists(base_path):
            return []
        
        items = []
        self.items.clear()
        
        for entry in os.scandir(base_path):
            if entry.name.startswith('-__'):
                # This is a folder
                folder = FolderItem(
                    name=entry.name,
                    full_path=entry.path,
                    item_type='folder'
                )
                items.append(folder)
                self.items[folder.display_name] = folder
            else:
                # This is a file
                file_item = FileItem(
                    name=entry.name,
                    full_path=entry.path,
                    item_type='file'
                )
                items.append(file_item)
                self.items[file_item.name] = file_item
        
        # Sort: folders first, then files, alphabetically
        items.sort(key=lambda x: (x.item_type == 'file', x.display_name.lower()))
        return items
    
    def get_item(self, name: str) -> Optional[FileSystemItem]:
        """Get item by name"""
        return self.items.get(name)
    
    def navigate_to_folder(self, folder_name: str) -> bool:
        """Navigate to a folder and update current path"""
        folder_item = self.get_item(folder_name)
        if folder_item and isinstance(folder_item, FolderItem):
            self.current_path = folder_item.full_path + "/"
            return True
        return False
    
    def go_back(self) -> bool:
        """Go back to parent directory"""
        if self.current_path != "data/":
            parent_path = os.path.dirname(self.current_path.rstrip('/'))
            if not parent_path or parent_path == "data":
                self.current_path = "data/"
            else:
                self.current_path = parent_path + "/"
            return True
        return False
    
    def can_go_back(self) -> bool:
        """Check if we can go back"""
        return self.current_path != "data/"


class PasswordManager:
    """Handles password operations for files"""
    
    @staticmethod
    def setup_password_for_item(item: FileItem, password: str = None) -> str:
        """Setup password for a file and return the password file path"""
        if password is None:
            password = item.display_name[:3]  # Default password
        
        password_file = item.password_file_path
        
        # Only create directory if it doesn't exist
        password_dir = os.path.dirname(password_file)
        if not os.path.exists(password_dir):
            print(f"DEBUG: Creating password directory: {password_dir}")
            os.makedirs(password_dir, exist_ok=True)
        else:
            print(f"DEBUG: Password directory already exists: {password_dir}")
        
        print(f"DEBUG: Setting up password file: {password_file}")
        hashed_password = hash_password(password)
        save_hashed_password(password_file, hashed_password)
        
        return password_file
    
    @staticmethod
    def load_password_hash(item: FileItem) -> Optional[bytes]:
        """Load password hash for a file"""
        password_file = item.password_file_path
        print(f"DEBUG: Loading password from: {password_file}")
        
        if os.path.exists(password_file):
            try:
                return load_hashed_password(password_file)
            except Exception as e:
                print(f"Error loading password hash: {e}")
        else:
            print(f"DEBUG: Password file does not exist: {password_file}")
        return None
    
    @staticmethod
    def change_password(item: FileItem, parent_widget=None) -> bool:
        """Open password change dialog for a file"""
        password_file = item.password_file_path
        current_hash = PasswordManager.load_password_hash(item)
        
        # Only create directory if it doesn't exist
        password_dir = os.path.dirname(password_file)
        if not os.path.exists(password_dir):
            print(f"DEBUG: Creating directory for password change: {password_dir}")
            os.makedirs(password_dir, exist_ok=True)
        
        dialog = ChangePasswordDialog(password_file, parent=parent_widget, currentHash=current_hash)
        return dialog.exec() == QDialog.Accepted
