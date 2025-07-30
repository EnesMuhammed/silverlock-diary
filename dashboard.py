import sys
import os
import subprocess
import json
import shutil
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (QApplication, QMessageBox, QMainWindow, QVBoxLayout, 
                              QHBoxLayout, QMenu, QDialog, QLineEdit, QPushButton, 
                              QWidget, QLabel, QGridLayout, QSpacerItem, QSizePolicy, 
                              QScrollArea, QButtonGroup, QRadioButton, QDialogButtonBox,
                              QComboBox, QFileDialog, QTreeView, QFileSystemModel)
from PySide6.QtCore import Qt, QSize, QEvent, Signal, QObject, QDir, QTimer
from PySide6.QtGui import QFont, QFontMetrics

# Assuming these imports exist
from manager import LoginWindow
from hash import hash_password, verify_password, save_hashed_password, load_hashed_password
from pass_changer import ChangePasswordDialog

# ====================== STYLE CONFIGURATION VARIABLES ======================
# [Previous configuration variables remain unchanged]
DESKTOP_SPACING = 13
WIDGETS_PER_ROW = 7
HISTORY_WIDGETS_PER_ROW = 1

# Border Radius Settings
MAIN_BORDER_RADIUS = 6
WIDGET_BORDER_RADIUS = 6
BUTTON_BORDER_RADIUS = 6
DIALOG_BORDER_RADIUS = 6
INPUT_BORDER_RADIUS = 6

# Margins and Padding
MAIN_WINDOW_MARGINS = (10, 15, 15, 15)
SECTION_MARGINS = (20, 20, 20, 20)
DIALOG_MARGINS = (20, 20, 20, 20)
INPUT_PADDING = 0
BUTTON_PADDING = (5, 5)
WIDGET_CONTENT_PADDING = (12, 12, 12, 12)

# Spacing
MAIN_LAYOUT_SPACING = 15
SECTION_SPACING = 15
GRID_SPACING = 10
DIALOG_SPACING = 20
BUTTON_SPACING = 10

# Colors - Main Theme
PRIMARY_COLOR = "#3498DB"
PRIMARY_HOVER_COLOR = "#2980B9"
PRIMARY_PRESSED_COLOR = "#1F6F97"
SECONDARY_COLOR = "#27AE60"
ACCENT_COLOR = "#F39C12"
DANGER_COLOR = "#E74C3C"
WARNING_COLOR = "#F39C12"
SUCCESS_COLOR = "#27AE60"

# Colors - Background
MAIN_BACKGROUND = "#1e1e1e"
SECTION_BACKGROUND = "#2a2a2a"
WIDGET_BACKGROUND = "#414141"
HOVER_BACKGROUND = "#4a4a4a"
PRESSED_BACKGROUND = "#333333"
TRANSPARENT_BACKGROUND = "rgba(255,255,255,20)"
TRANSPARENT_HOVER = "rgba(255,255,255,100)"

# Colors - Text
PRIMARY_TEXT = "#FFFFFF"
SECONDARY_TEXT = "#CCCCCC"
MUTED_TEXT = "#888888"
PLACEHOLDER_TEXT = "#999999"

# Colors - Borders
PRIMARY_BORDER = "#555555"
FOCUS_BORDER = "#3498DB"
ACCENT_BORDER = "#F39C12"
SUCCESS_BORDER = "#27AE60"

# File and Folder Widget Colors
FILE_WIDGET_BACKGROUND = "rgba(255,255,255,30)"
FILE_WIDGET_HOVER = "#4a4a4a"
FILE_WIDGET_PRESSED = "#333333"
FOLDER_WIDGET_BACKGROUND = "rgba(52, 152, 219, 100)"
FOLDER_WIDGET_HOVER = "#4a80a8"
FOLDER_WIDGET_PRESSED = "#2c5982"
ADD_WIDGET_BACKGROUND = "#3498DB"
ADD_WIDGET_HOVER = "#2980B9"
ADD_WIDGET_PRESSED = "#1F6F97"

# History and Quick Access Widget Colors
HISTORY_WIDGET_BACKGROUND = "#414141"
HISTORY_WIDGET_HOVER = "#4a4a4a"
HISTORY_BORDER_COLOR = "#27AE60"
PINNED_WIDGET_BACKGROUND = "#414141"
PINNED_WIDGET_HOVER = "#4a4a4a"
PINNED_BORDER_COLOR = "#F39C12"

# Font Settings
MAIN_FONT_SIZE = 14
WIDGET_FONT_SIZE = 14
BUTTON_FONT_SIZE = 14
TITLE_FONT_SIZE = 18
SMALL_FONT_SIZE = 10
LARGE_FONT_SIZE = 40

# Sidebar Settings
SIDEBAR_WIDTH = 55
SIDEBAR_BACKGROUND = "#4a4a4a"
SIDEBAR_BORDER_COLOR = "#3498DB"
SIDEBAR_BORDER_WIDTH = 3



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
        print("CONTENT FILE Path : "+ os.path.join(file_dir, "content.html"))
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
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'name': self.name,
            'full_path': self.full_path,
            'last_accessed': self.last_accessed
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'HistoryItem':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            full_path=data['full_path'], 
            last_accessed=data['last_accessed']
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
    
    def update_path(self, old_path: str, new_path: str):
        """Update path for pinned items when moved/renamed"""
        for item in self.pinned_items:
            if item.full_path == old_path:
                item.full_path = new_path
                # Update name if it's a direct match
                if item.name == os.path.basename(old_path):
                    item.name = os.path.basename(new_path)
        self.save_pins()


class BaseWidget(QWidget):
    """Base class for all custom widgets"""
    
    def __init__(self, fixed_size: QSize, parent=None):
        super().__init__(parent)
        self.setFixedSize(fixed_size)
        self.setup_ui()
        self.setup_style()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the UI components - override in subclasses"""
        raise NotImplementedError("Subclasses must implement setup_ui()")
    
    def setup_style(self):
        """Setup the widget styling - override in subclasses"""
        raise NotImplementedError("Subclasses must implement setup_style()")
    
    def connect_signals(self):
        """Connect signals and slots - override in subclasses"""
        raise NotImplementedError("Subclasses must implement connect_signals()")


class FolderWidget(BaseWidget):
    """Widget representing a folder"""
    
    clicked = Signal(str)  # Emits folder name when clicked
    context_menu_requested = Signal(str, object)  # Emits folder name and position
    
    def __init__(self, folder_item: FolderItem, fixed_size: QSize, parent=None):
        self.folder_item = folder_item
        super().__init__(fixed_size, parent)
    
    def setup_ui(self):
        layout = LayoutFactory.create_zero_vertical_layout(5, WIDGET_CONTENT_PADDING)
        self.setLayout(layout)
        
        # Folder icon and name container
        content_layout = LayoutFactory.create_zero_vertical_layout(8)
        
        # Folder icon
        icon_label = QLabel("📁")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            color: {ACCENT_COLOR};
            font-size: 24px;
            background-color: transparent;
        """)
        
        # Folder name button with text truncation
        self.button = QPushButton()
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Truncate text to fit button
        font = QFont()
        font.setPointSize(WIDGET_FONT_SIZE)
        font.setBold(True)
        font_metrics = QFontMetrics(font)
        
        # Calculate available width (button width minus padding)
        available_width = self.size().width() - WIDGET_CONTENT_PADDING[0] - WIDGET_CONTENT_PADDING[2] - 16
        truncated_text = truncate_text(self.folder_item.display_name, available_width, font_metrics)
        self.button.setText(truncated_text)
        self.button.setToolTip(self.folder_item.display_name)  # Show full name on hover
        
        content_layout.addWidget(icon_label)
        content_layout.addWidget(self.button, 1)
        
        layout.addLayout(content_layout)
    
    def setup_style(self):
        self.setStyleSheet(f"""
            FolderWidget {{
                border-radius: {WIDGET_BORDER_RADIUS}px;
                background-color: {FOLDER_WIDGET_BACKGROUND};
                border: 2px solid transparent;
            }}
            FolderWidget:hover {{
                background-color: {FOLDER_WIDGET_HOVER};
                border: 2px solid {ACCENT_COLOR};
            }}
        """)
        
        self.button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: transparent;
                border: none;
                color: {PRIMARY_TEXT};
                font-size: {WIDGET_FONT_SIZE}px;
                font-weight: bold;
                text-align: center;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: {FOLDER_WIDGET_PRESSED};
            }}
        """)
    
    def connect_signals(self):
        self.button.clicked.connect(lambda: self.clicked.emit(self.folder_item.display_name))
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: self.context_menu_requested.emit(self.folder_item.display_name, pos)
        )


class HistoryWidget(BaseWidget):
    """Widget for history items"""
    
    clicked = Signal(str)  # Emits full path when clicked
    context_menu_requested = Signal(str, object)  # Emits full path and position
    
    def __init__(self, history_item: HistoryItem, fixed_size: QSize, parent=None):
        self.history_item = history_item
        super().__init__(fixed_size, parent)
    
    def setup_ui(self):
        layout = LayoutFactory.create_zero_vertical_layout(8, (12, 12, 12, 12))
        self.setLayout(layout)
        
        # Top section with file icon and name
        top_layout = LayoutFactory.create_zero_margin_layout(8)
        
        # File icon
        icon_label = QLabel("📄")
        icon_label.setFixedSize(24, 24)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            color: {SECONDARY_COLOR};
            font-size: 18px;
            background-color: transparent;
        """)
        
        # File name button with text truncation
        self.button = QPushButton()
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Truncate text to fit button
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        font_metrics = QFontMetrics(font)
        
        # Calculate available width
        available_width = self.size().width() - 50  # Account for icon and margins
        truncated_text = truncate_text(self.history_item.name, available_width, font_metrics)
        self.button.setText(truncated_text)
        self.button.setToolTip(self.history_item.name)  # Show full name on hover
        
        top_layout.addWidget(icon_label)
        top_layout.addWidget(self.button, 1)
        
        layout.addLayout(top_layout)
        
        # Bottom section with time info
        bottom_layout = LayoutFactory.create_zero_margin_layout()
        
        # Format last accessed time
        try:
            dt = datetime.fromisoformat(self.history_item.last_accessed)
            date_str = dt.strftime("%m/%d/%Y")
            time_str = dt.strftime("%H:%M")
        except:
            date_str = "--/--/----"
            time_str = "--:--"
        
        time_info = QLabel(f"📅 {date_str} • 🕐 {time_str}")
        time_info.setStyleSheet(f"""
            color: {MUTED_TEXT};
            font-size: {SMALL_FONT_SIZE}px;
            background-color: transparent;
            padding: 2px;
        """)
        time_info.setAlignment(Qt.AlignLeft)
        
        bottom_layout.addWidget(time_info)
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)
    
    def setup_style(self):
        self.setStyleSheet(f"""
            HistoryWidget {{
                background-color: {HISTORY_WIDGET_BACKGROUND};
                border-radius: {WIDGET_BORDER_RADIUS}px;
                border-left: 4px solid {HISTORY_BORDER_COLOR};
            }}
            HistoryWidget:hover {{
                background-color: {HISTORY_WIDGET_HOVER};
                border-left: 4px solid {SUCCESS_COLOR};
            }}
        """)
        
        self.button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: transparent;
                border: none;
                color: {PRIMARY_TEXT};
                font-size: 13px;
                text-align: left;
                padding: 4px 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
    
    def connect_signals(self):
        self.button.clicked.connect(lambda: self.clicked.emit(self.history_item.full_path))
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: self.context_menu_requested.emit(self.history_item.full_path, pos)
        )


class PinnedWidget(BaseWidget):
    """Widget for pinned items"""
    
    clicked = Signal(str)  # Emits full path when clicked
    context_menu_requested = Signal(str, object)  # Emits full path and position
    
    def __init__(self, pinned_item: PinnedItem, fixed_size: QSize, parent=None):
        self.pinned_item = pinned_item
        super().__init__(fixed_size, parent)
    
    def setup_ui(self):
        layout = LayoutFactory.create_zero_vertical_layout(8, (12, 12, 12, 12))
        self.setLayout(layout)
        
        # Top section with pin icon and file name
        top_layout = LayoutFactory.create_zero_margin_layout(8)
        
        # Pin icon
        pin_icon = QLabel("📌")
        pin_icon.setFixedSize(24, 24)
        pin_icon.setAlignment(Qt.AlignCenter)
        pin_icon.setStyleSheet(f"""
            color: {ACCENT_COLOR};
            font-size: 18px;
            background-color: transparent;
        """)
        
        # File name button with text truncation
        self.button = QPushButton()
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Truncate text to fit button
        font = QFont()
        font.setPointSize(13)
        font.setBold(True)
        font_metrics = QFontMetrics(font)
        
        # Calculate available width
        available_width = self.size().width() - 50  # Account for icon and margins
        truncated_text = truncate_text(self.pinned_item.name, available_width, font_metrics)
        self.button.setText(truncated_text)
        self.button.setToolTip(self.pinned_item.name)  # Show full name on hover
        
        top_layout.addWidget(pin_icon)
        top_layout.addWidget(self.button, 1)
        
        layout.addLayout(top_layout)
        
        # Bottom section with pinned date
        bottom_layout = LayoutFactory.create_zero_margin_layout()
        
        # Format pinned date
        try:
            dt = datetime.fromisoformat(self.pinned_item.pinned_at)
            date_str = dt.strftime("%m/%d/%Y")
            time_str = dt.strftime("%H:%M")
        except:
            date_str = "--/--/----"
            time_str = "--:--"
        
        pin_info = QLabel(f"🔗 {date_str} • {time_str}")
        pin_info.setStyleSheet(f"""
            color: {ACCENT_COLOR};
            font-size: {SMALL_FONT_SIZE}px;
            background-color: transparent;
            padding: 2px;
            font-weight: bold;
        """)
        pin_info.setAlignment(Qt.AlignLeft)
        
        bottom_layout.addWidget(pin_info)
        bottom_layout.addStretch()
        
        layout.addLayout(bottom_layout)
    
    def setup_style(self):
        self.setStyleSheet(f"""
            PinnedWidget {{
                background-color: {PINNED_WIDGET_BACKGROUND};
                border-radius: {WIDGET_BORDER_RADIUS}px;
                border-left: 4px solid {PINNED_BORDER_COLOR};
            }}
            PinnedWidget:hover {{
                background-color: {PINNED_WIDGET_HOVER};
                border-left: 4px solid {WARNING_COLOR};
            }}
        """)
        
        self.button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: transparent;
                border: none;
                color: {PRIMARY_TEXT};
                font-size: 13px;
                text-align: left;
                padding: 4px 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
    
    def connect_signals(self):
        self.button.clicked.connect(lambda: self.clicked.emit(self.pinned_item.full_path))
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: self.context_menu_requested.emit(self.pinned_item.full_path, pos)
        )



class AddFolderWidget(BaseWidget):
    """Widget for adding new folders and files"""
    
    clicked = Signal()
    
    def __init__(self, fixed_size: QSize, parent=None):
        super().__init__(fixed_size, parent)
    
    def setup_ui(self):
        layout = LayoutFactory.create_zero_vertical_layout(5, WIDGET_CONTENT_PADDING)
        self.setLayout(layout)
        
        # Add icon and text container
        content_layout = LayoutFactory.create_zero_vertical_layout(8)
        
        # Add icon
        icon_label = QLabel("➕")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            color: {PRIMARY_TEXT};
            font-size: 24px;
            background-color: transparent;
        """)
        
        # Add button
        self.button = QPushButton("New")
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        content_layout.addWidget(icon_label)
        content_layout.addWidget(self.button, 1)
        
        layout.addLayout(content_layout)
    
    def setup_style(self):
        self.setStyleSheet(f"""
            AddFolderWidget {{
                border-radius: {WIDGET_BORDER_RADIUS}px;
                background-color: {ADD_WIDGET_BACKGROUND};
                border: 2px solid transparent;
            }}
            AddFolderWidget:hover {{
                background-color: {ADD_WIDGET_HOVER};
                border: 2px solid {SUCCESS_COLOR};
            }}
        """)
        
        self.button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: transparent;
                border: none;
                color: {PRIMARY_TEXT};
                font-size: {WIDGET_FONT_SIZE}px;
                font-weight: bold;
                text-align: center;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: {ADD_WIDGET_PRESSED};
            }}
        """)
    
    def connect_signals(self):
        self.button.clicked.connect(self.clicked.emit)


class QuickAccessManager:
    """Manages quick access functionality with pinned files"""
    
    def __init__(self, parent_widget: QWidget, grid_layout: QGridLayout, pin_manager: PinManager):
        self.parent_widget = parent_widget
        self.grid_layout = grid_layout
        self.pin_manager = pin_manager
    
    def clear_grid(self):
        """Clear the grid layout"""
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
            self.grid_layout.removeItem(item)
    
    def calculate_widget_size(self) -> QSize:
        """Calculate widget size for quick access items"""
        quick_area_height = self.parent_widget.height()
        quick_area_width = self.parent_widget.width()
        
        margins = sum(SECTION_MARGINS[:2])  # top + bottom margins
        
        # Get pinned files count to calculate rows needed
        pinned_files = self.pin_manager.get_pinned_files()
        items_count = len(pinned_files) if pinned_files else 1  # At least 1 for "no pins" message
        
        # Calculate optimal height to fit all items without cutoff
        available_height = quick_area_height - margins
        total_vertical_spacing = GRID_SPACING * max(0, items_count - 1)
        
        # Calculate widget height to fit perfectly
        calculated_height = max(80, (available_height - total_vertical_spacing) // max(1, items_count))
        calculated_width = max(150, quick_area_width - margins)
        
        # Limit maximum height to prevent oversized widgets when few items
        calculated_height = min(calculated_height, 120)
        
        return QSize(calculated_width, calculated_height)

    def populate_quick_access(self):
        """Populate quick access area with pinned files"""
        self.clear_grid()
        
        pinned_files = self.pin_manager.get_pinned_files()
        if not pinned_files:
            # Show "No pins" message
            no_pins_label = QLabel("No files pinned yet")
            no_pins_label.setStyleSheet(f"""
                color: {MUTED_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                text-align: center;
                background-color: transparent;
                padding: 20px;
            """)
            no_pins_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_pins_label, 0, 0)
            return
        
        widget_size = self.calculate_widget_size()
        
        for i, pinned_item in enumerate(pinned_files):
            # Check if file still exists
            if not os.path.exists(pinned_item.full_path):
                continue
                
            widget = PinnedWidget(pinned_item, widget_size, self.parent_widget)
            self.grid_layout.addWidget(widget, i, 0)
        
        # Add vertical spacer
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
            len(pinned_files), 0
        )


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
    
    def remove_item(self, file_path: str):
        """Remove specific item from history"""
        self.history_items = [item for item in self.history_items if item.full_path != file_path]
        self.save_history()
    
    def update_path(self, old_path: str, new_path: str):
        """Update path for history items when moved/renamed"""
        for item in self.history_items:
            if item.full_path == old_path:
                item.full_path = new_path
                # Update name if it's a direct match
                if item.name == os.path.basename(old_path):
                    item.name = os.path.basename(new_path)
        self.save_history()


class SidebarWidget(QWidget):
    """Sidebar with buttons"""
    
    master_password_clicked = Signal()
    settings_clicked = Signal() 
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SidebarWidget")

        self.setFixedWidth(SIDEBAR_WIDTH)
        self.setup_ui()
        self.setup_style()
        self.connect_signals()
    
    def setup_ui(self):
        layout = LayoutFactory.create_zero_vertical_layout(15, (0, 0, 0, 0))
        self.setLayout(layout)
        
        # Master password button
        self.master_password_button = QPushButton("🔐")
        self.master_password_button.setFixedSize(45, 45)
        self.master_password_button.setToolTip("Change Master Password")
        
        # Settings button - YENİ
        self.settings_button = QPushButton("⚙️")
        self.settings_button.setFixedSize(45, 45)
        self.settings_button.setToolTip("Settings")
        
        layout.addWidget(self.master_password_button)
        layout.addWidget(self.settings_button)  # YENİ
        layout.addStretch()
    
    def setup_style(self):
        self.setStyleSheet(f"""
            QWidget#SidebarWidget {{
                background-color: red;
                border-radius: 6px;
                border-left: 3px solid {SIDEBAR_BORDER_COLOR};
            }}
        """)
        
        self.master_password_button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                font-size: 20px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
        """)
        self.settings_button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                font-size: 20px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
        """)

    def connect_signals(self):
        self.master_password_button.clicked.connect(self.master_password_clicked.emit)
        self.settings_button.clicked.connect(self.settings_clicked.emit)  # YENİ



class HistoryGridManager:
    """Manages the history grid layout and widget creation"""
    
    def __init__(self, grid_layout: QGridLayout, parent_widget: QWidget, history_manager: HistoryManager):
        self.grid_layout = grid_layout
        self.parent_widget = parent_widget
        self.history_manager = history_manager
    
    def clear_grid(self):
        """Clear all widgets from the grid"""
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
            self.grid_layout.removeItem(item)
    
    def calculate_widget_size(self) -> QSize:
        """Calculate widget size for history items"""
        history_area_height = self.parent_widget.height()
        history_area_width = self.parent_widget.width()
        
        margins = sum(SECTION_MARGINS[:2])  # top + bottom margins
        
        # Get recent files count to calculate rows needed
        recent_files = self.history_manager.get_recent_files()
        items_count = len(recent_files) if recent_files else 1  # At least 1 for "no files" message
        
        # Calculate optimal height to fit all items without cutoff
        available_height = history_area_height - margins
        total_vertical_spacing = GRID_SPACING * max(0, items_count - 1)
        
        # Calculate widget height to fit perfectly
        calculated_height = max(70, (available_height - total_vertical_spacing) // max(1, items_count))
        calculated_width = max(150, history_area_width - margins)
        
        # Limit maximum height to prevent oversized widgets when few items
        calculated_height = min(calculated_height, 100)
        
        return QSize(calculated_width, calculated_height)


    def populate_history(self):
        """Populate history area with recent files"""
        self.clear_grid()
        
        recent_files = self.history_manager.get_recent_files()
        if not recent_files:
            # Show "No history" message
            no_history_label = QLabel("No files opened yet")
            no_history_label.setStyleSheet(f"""
                color: {MUTED_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                text-align: center;
                background-color: transparent;
                padding: 20px;
            """)
            no_history_label.setAlignment(Qt.AlignCenter)
            self.grid_layout.addWidget(no_history_label, 0, 0)
            return
        
        widget_size = self.calculate_widget_size()
        
        for i, history_item in enumerate(recent_files):
            # Check if file still exists
            if not os.path.exists(history_item.full_path):
                continue
                
            widget = HistoryWidget(history_item, widget_size, self.parent_widget)
            self.grid_layout.addWidget(widget, i, 0)
        
        # Add vertical spacer
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
            len(recent_files), 0
        )



class NavigationBar(QWidget):
    """Navigation bar with back button and path display"""
    
    back_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        self.connect_signals()
    
    def setup_ui(self):
        layout = LayoutFactory.create_zero_margin_layout(spacing=12)
        self.setLayout(layout)
        
        self.back_button = QPushButton("←")
        self.back_button.setFixedSize(45, 45)
        self.path_label = QLabel()
        
        layout.addWidget(self.back_button)
        layout.addWidget(self.path_label, 1)  # Stretch to fill available space
    
    def setup_style(self):
        self.setStyleSheet(f"background-color: {TRANSPARENT_BACKGROUND}; border-radius: {WIDGET_BORDER_RADIUS}px;")
        self.back_button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: {TRANSPARENT_BACKGROUND};
                color: {PRIMARY_TEXT};
                font-size: 20px;
                border: none;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
            QPushButton:disabled {{
                background-color: {TRANSPARENT_BACKGROUND};
                color: {MUTED_TEXT};
            }}
        """)
        
        self.path_label.setStyleSheet(f"""
            color: {SECONDARY_TEXT};
            font-size: {MAIN_FONT_SIZE + 2}px;
            font-weight: bold;
            background-color: {TRANSPARENT_BACKGROUND};
            border-radius: {BUTTON_BORDER_RADIUS}px;
            padding: 12px 16px;
        """)
    
    def connect_signals(self):
        self.back_button.clicked.connect(self.back_clicked.emit)
    
    def update_path(self, path: str, can_go_back: bool):
        """Update the displayed path and back button state"""
        display_path = path.replace("data", "root")
        if not display_path:
            display_path = "root"
        self.path_label.setText(f"📁 {display_path}")
        self.back_button.setEnabled(can_go_back)

class SettingsDialog(QDialog):
    """Dialog for application settings"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings_file = "settings.json"
        self.current_settings = self.load_settings()
        self.setup_ui()
        self.setup_style()
        self.load_current_values()

    def setup_ui(self):
        self.setWindowTitle("Settings")
        self.setFixedSize(400, 250)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Title
        title_label = QLabel("Application Settings")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        layout.addWidget(title_label)

        # Display settings section (only one)
        self.create_display_settings(layout)

        layout.addStretch()

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        self.reset_button = QPushButton("Reset to Default")
        self.cancel_button = QPushButton("Cancel")
        self.apply_button = QPushButton("Apply")

        self.reset_button.setMinimumSize(120, 35)
        self.cancel_button.setMinimumSize(100, 35)
        self.apply_button.setMinimumSize(100, 35)

        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.apply_button)

        layout.addLayout(button_layout)

        # Connect signals
        self.reset_button.clicked.connect(self.reset_to_default)
        self.cancel_button.clicked.connect(self.reject)
        self.apply_button.clicked.connect(self.apply_settings)

    def create_display_settings(self, parent_layout):
        """Create display settings section"""
        display_group = QWidget()
        display_group.setObjectName("settingsGroup")
        display_layout = QVBoxLayout(display_group)
        display_layout.setContentsMargins(15, 15, 15, 15)
        display_layout.setSpacing(15)

        display_title = QLabel("Display Settings")
        display_title.setObjectName("sectionTitle")
        display_layout.addWidget(display_title)

        widgets_row_container = QWidget()
        widgets_row_layout = QHBoxLayout(widgets_row_container)
        widgets_row_layout.setContentsMargins(0, 0, 0, 0)
        widgets_row_layout.setSpacing(10)

        widgets_row_label = QLabel("Widgets per Row:")
        widgets_row_label.setMinimumWidth(150)

        self.widgets_per_row_spin = QComboBox()
        self.widgets_per_row_spin.addItems(["3", "4", "5", "6", "7", "8", "9", "10"])
        self.widgets_per_row_spin.setMinimumWidth(100)

        widgets_row_layout.addWidget(widgets_row_label)
        widgets_row_layout.addWidget(self.widgets_per_row_spin)
        widgets_row_layout.addStretch()

        display_layout.addWidget(widgets_row_container)

        parent_layout.addWidget(display_group)

    def setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SECTION_BACKGROUND};
                color: {PRIMARY_TEXT};
                border-radius: {DIALOG_BORDER_RADIUS}px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                font-weight: bold;
            }}
            QLabel[objectName="title"] {{
                font-size: {TITLE_FONT_SIZE}px;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                margin-bottom: 10px;
            }}
            QLabel[objectName="sectionTitle"] {{
                font-size: 16px;
                color: {ACCENT_COLOR};
                font-weight: bold;
                border-bottom: 2px solid {PRIMARY_COLOR};
                padding-bottom: 5px;
                margin-bottom: 10px;
            }}
            QWidget[objectName="settingsGroup"] {{
                background-color: {WIDGET_BACKGROUND};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {WIDGET_BORDER_RADIUS}px;
                margin: 5px 0;
            }}
            QComboBox {{
                background-color: {WIDGET_BACKGROUND};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {INPUT_BORDER_RADIUS}px;
                padding: 5px 10px;
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                min-height: 25px;
            }}
            QComboBox:focus {{
                border-color: {FOCUS_BORDER};
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                border: none;
                padding: 8px 16px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                font-size: {BUTTON_FONT_SIZE}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
            QPushButton[objectName="cancel"] {{
                background-color: {DANGER_COLOR};
            }}
            QPushButton[objectName="cancel"]:hover {{
                background-color: #C0392B;
            }}
            QPushButton[objectName="reset"] {{
                background-color: {WARNING_COLOR};
            }}
            QPushButton[objectName="reset"]:hover {{
                background-color: #E67E22;
            }}
        """)
        self.cancel_button.setObjectName("cancel")
        self.reset_button.setObjectName("reset")

    def load_settings(self):
        """Load settings from file"""
        default_settings = {
            "widgets_per_row": 6
        }

        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    default_settings.update(loaded_settings)
                    return default_settings
            except Exception as e:
                print(f"Error loading settings: {e}")
        return default_settings

    def save_settings(self, settings):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_current_values(self):
        """Load current values into UI elements"""
        self.widgets_per_row_spin.setCurrentText(str(self.current_settings["widgets_per_row"]))

    def get_current_ui_values(self):
        """Get current values from UI elements"""
        return {
            "widgets_per_row": int(self.widgets_per_row_spin.currentText())
        }

    def reset_to_default(self):
        """Reset to default values"""
        reply = QMessageBox.question(
            self,
            "Reset Settings",
            "Are you sure you want to reset settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.widgets_per_row_spin.setCurrentText("6")

    def apply_settings(self):
        """Apply current settings"""
        new_settings = self.get_current_ui_values()
        self.save_settings(new_settings)

        global WIDGETS_PER_ROW
        WIDGETS_PER_ROW = new_settings["widgets_per_row"]

        QMessageBox.information(
            self,
            "Settings Applied",
            "Widgets per row setting has been applied.\nSome changes may require restarting the application."
        )

        self.accept()


class FileGridManager:
    """Manages the file grid layout and widget creation"""
    def __init__(self, grid_layout: QGridLayout, parent_widget: QWidget):
        self.grid_layout = grid_layout
        self.parent_widget = parent_widget
        self.load_widgets_per_row()  # YENİ


    def calculate_widget_size(self, item_count: int) -> QSize:
        """Calculate optimal widget size based on available space"""
        files_widget_width = self.parent_widget.width()
        files_widget_height = self.parent_widget.height()
        
        # Calculate width
        horizontal_margins = 40
        total_horizontal_spacing = GRID_SPACING * (self.widgets_per_row - 1)
        effective_width = files_widget_width - horizontal_margins - total_horizontal_spacing
        calculated_width = max(120, effective_width // self.widgets_per_row)
        
        # Calculate height - IMPROVED
        nav_header_height = 10  # Navigation bar height
        vertical_margins = 0
        
        # Calculate how many rows we need
        total_items = item_count + 1  # +1 for add widget
        rows_needed = (total_items + self.widgets_per_row - 1) // self.widgets_per_row
        
        # Calculate available height for widgets
        available_height = files_widget_height - nav_header_height - vertical_margins
        total_vertical_spacing = GRID_SPACING * max(0, rows_needed - 1)
        
        # Calculate widget height to fit perfectly
        if rows_needed > 0:
            calculated_height = max(100, (available_height - total_vertical_spacing) // rows_needed)
            print(calculated_height)
        else:
            calculated_height = 120
            print(120)
        
        return QSize(calculated_width, calculated_height)

    def load_widgets_per_row(self):  # YENİ METOD
        """Load widgets per row from settings"""
        settings_file = "settings.json"
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.widgets_per_row = settings.get("widgets_per_row", WIDGETS_PER_ROW)
            except:
                self.widgets_per_row = WIDGETS_PER_ROW
        else:
            self.widgets_per_row = WIDGETS_PER_ROW

    def clear_grid(self):
        """Clear all widgets from the grid"""
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item is None:
                continue
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                for j in reversed(range(item.layout().count())):
                    sub_item = item.layout().itemAt(j)
                    if sub_item and sub_item.widget():
                        sub_item.widget().deleteLater()
                item.layout().deleteLater()
            self.grid_layout.removeItem(item)
    
    def calculate_widget_size(self, item_count: int) -> QSize:
        """Calculate optimal widget size based on available space"""
        files_widget_width = self.parent_widget.width()
        files_widget_height = self.parent_widget.height()
        
        # Calculate width
        horizontal_margins = 40  # Approximate margins
        total_horizontal_spacing = GRID_SPACING * (self.widgets_per_row - 1)
        effective_width = files_widget_width - horizontal_margins - total_horizontal_spacing
        calculated_width = max(120, effective_width // self.widgets_per_row)
        
        # Calculate height
        nav_header_height = 80
        vertical_margins = 40
        estimated_rows = max(1, (item_count + self.widgets_per_row) // self.widgets_per_row)
        total_vertical_spacing = GRID_SPACING * (estimated_rows - 1)
        effective_height = files_widget_height - nav_header_height - vertical_margins - total_vertical_spacing
        calculated_height = max(100, effective_height // 5)
        
        return QSize(calculated_width, calculated_height)
    
    def populate_grid(self, items: List[FileSystemItem], widget_size: QSize):
        """Populate the grid with items"""
        self.clear_grid()
        
        row, col = 0, 0
        
        # Reset column stretches
        for i in range(self.widgets_per_row):
            self.grid_layout.setColumnStretch(i, 0)
        
        # Add "+" widget
        add_widget = AddFolderWidget(widget_size, self.parent_widget)
        self.grid_layout.addWidget(add_widget, row, col)
        col += 1
        
        # Add items
        for item in items:
            if isinstance(item, FolderItem):
                widget = FolderWidget(item, widget_size, self.parent_widget)
            elif isinstance(item, FileItem):
                widget = FileWidget(item, widget_size, self.parent_widget)
            else:
                continue
            
            self.grid_layout.addWidget(widget, row, col)
            col += 1
            
            if col >= self.widgets_per_row:
                col = 0
                row += 1
        
        # Add spacers for remaining columns
        if col > 0:
            for i in range(col, self.widgets_per_row):
                self.grid_layout.addItem(
                    QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum),
                    row, i
                )
        
        # Add vertical spacer
        self.grid_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding),
            row + 1, 0, 1, self.widgets_per_row
        )


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
    
    def rename_item(self, item: FileSystemItem, new_name: str) -> Tuple[bool, str]:
        """Rename a file or folder"""
        try:
            if isinstance(item, FolderItem):
                # For folders, add -__ prefix
                new_folder_name = f"-__{new_name}"
                new_path = os.path.join(os.path.dirname(item.full_path), new_folder_name)
            else:
                # For files, use name as is
                new_path = os.path.join(os.path.dirname(item.full_path), new_name)
            
            print(f"DEBUG RENAME FS: Old path: {item.full_path}")
            print(f"DEBUG RENAME FS: New path: {new_path}")
            
            # Check if target already exists
            if os.path.exists(new_path):
                return False, "An item with this name already exists!"
            
            # Rename the item
            os.rename(item.full_path, new_path)
            
            print(f"DEBUG RENAME FS: Rename successful")
            return True, new_path
            
        except Exception as e:
            print(f"DEBUG RENAME FS: Error: {str(e)}")
            return False, f"Rename error: {str(e)}"
    
    def move_item(self, item: FileSystemItem, target_path: str) -> Tuple[bool, str]:
        """Move a file or folder to target location"""
        try:
            # Create target path
            new_path = os.path.join(target_path, os.path.basename(item.full_path))
            
            print(f"DEBUG MOVE FS: Old path: {item.full_path}")
            print(f"DEBUG MOVE FS: Target path: {target_path}")
            print(f"DEBUG MOVE FS: New path: {new_path}")
            
            # Check if target already exists
            if os.path.exists(new_path):
                return False, "An item with the same name exists at destination!"
            
            # Move the item
            shutil.move(item.full_path, new_path)
            
            print(f"DEBUG MOVE FS: Move successful")
            return True, new_path
            
        except Exception as e:
            print(f"DEBUG MOVE FS: Error: {str(e)}")
            return False, f"Move error: {str(e)}"
    
    def delete_item(self, item: FileSystemItem) -> Tuple[bool, str]:
        """Delete a file or folder"""
        try:
            if isinstance(item, FolderItem):
                # Delete folder and all contents
                shutil.rmtree(item.full_path)
            else:
                # Delete file directory
                shutil.rmtree(item.full_path)
            
            return True, "Success"
            
        except Exception as e:
            return False, f"Delete error: {str(e)}"

class RenameDialog(QDialog):
    """Dialog for renaming files and folders"""
    def __init__(self, current_name: str, item_type: str, parent=None):
        super().__init__(parent)
        self.current_name = current_name
        self.item_type = item_type
        self.new_name = None
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle(f"Rename {self.item_type.title()}")
        self.setFixedSize(500, 280)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Title
        title_label = QLabel(f"Rename {self.item_type.title()}")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # New name input
        new_container = QWidget()
        new_layout = QVBoxLayout(new_container)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(8)
        
        new_label = QLabel("New Name:")
        self.name_input = QLineEdit()
        self.name_input.setText(self.current_name)
        self.name_input.selectAll()
        self.name_input.setPlaceholderText("Enter new name...")
        self.name_input.setMinimumHeight(40)
        
        new_layout.addWidget(new_label)
        new_layout.addWidget(self.name_input)
        layout.addWidget(new_container)
        
        # Add stretch to push buttons to bottom
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(BUTTON_SPACING)
        
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("OK")
        
        self.cancel_button.setMinimumSize(100, 35)
        self.ok_button.setMinimumSize(100, 35)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept_dialog)
        self.name_input.returnPressed.connect(self.accept_dialog)

    def setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SECTION_BACKGROUND};
                color: {PRIMARY_TEXT};
                border-radius: {DIALOG_BORDER_RADIUS}px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                font-weight: bold;
            }}
            QLabel[objectName="title"] {{
                font-size: {TITLE_FONT_SIZE}px;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                margin-bottom: 10px;
            }}
            QLineEdit {{
                background-color: {WIDGET_BACKGROUND};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {INPUT_BORDER_RADIUS}px;
                padding: 5px 10px;
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                selection-background-color: {PRIMARY_COLOR};
                min-height: 28px; /* 40px - padding - border */
            }}
            QLineEdit:focus {{
                border-color: {FOCUS_BORDER};
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                border: none;
                padding: 5px 15px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                font-size: {BUTTON_FONT_SIZE}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
            QPushButton[objectName="cancel"] {{
                background-color: {DANGER_COLOR};
            }}
            QPushButton[objectName="cancel"]:hover {{
                background-color: #C0392B;
            }}
        """)
        self.cancel_button.setObjectName("cancel")
        
    def accept_dialog(self):
        # ... (accept_dialog logic remains the same)
        new_name = self.name_input.text().strip()
        if not new_name:
            QMessageBox.warning(self, "Error", "Please enter a name!")
            return
        if new_name == self.current_name:
            QMessageBox.information(self, "Info", "Name unchanged!")
            return
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in new_name for char in invalid_chars):
            QMessageBox.warning(self, "Error", "Name contains invalid characters!")
            return
        self.new_name = new_name
        self.accept()

# --- REFACTORED DIALOGS ---
# Yeni şifre belirleme dialogu (AddItemDialog'dan sonra eklenecek)

class SetPasswordDialog(QDialog):
    """Dialog for setting password for new files"""
    def __init__(self, file_name: str, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.password = None
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle("Set Password")
        self.setFixedSize(500, 320)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Title
        title_label = QLabel(f"Set Password for '{self.file_name}'")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # Password input
        password_container = QWidget()
        password_layout = QVBoxLayout(password_container)
        password_layout.setContentsMargins(0, 0, 0, 0)
        password_layout.setSpacing(8)
        
        password_label = QLabel("Password:")
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter password...")
        self.password_input.setMinimumHeight(40)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addWidget(password_container)
        
        # Confirm password input
        confirm_container = QWidget()
        confirm_layout = QVBoxLayout(confirm_container)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(8)
        
        confirm_label = QLabel("Confirm Password:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Re-enter password...")
        self.confirm_input.setMinimumHeight(40)
        
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        layout.addWidget(confirm_container)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(BUTTON_SPACING)
        
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Set Password")
        
        self.cancel_button.setMinimumSize(100, 35)
        self.ok_button.setMinimumSize(120, 35)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept_dialog)
        self.confirm_input.returnPressed.connect(self.accept_dialog)

    def setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SECTION_BACKGROUND};
                color: {PRIMARY_TEXT};
                border-radius: {DIALOG_BORDER_RADIUS}px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                font-weight: bold;
            }}
            QLabel[objectName="title"] {{
                font-size: {TITLE_FONT_SIZE}px;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                margin-bottom: 10px;
            }}
            QLineEdit {{
                background-color: {WIDGET_BACKGROUND};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {INPUT_BORDER_RADIUS}px;
                padding: 5px 10px;
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                selection-background-color: {PRIMARY_COLOR};
                min-height: 28px;
            }}
            QLineEdit:focus {{
                border-color: {FOCUS_BORDER};
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                border: none;
                padding: 5px 15px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                font-size: {BUTTON_FONT_SIZE}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
            QPushButton[objectName="cancel"] {{
                background-color: {DANGER_COLOR};
            }}
            QPushButton[objectName="cancel"]:hover {{
                background-color: #C0392B;
            }}
        """)
        self.cancel_button.setObjectName("cancel")
        
    def accept_dialog(self):
        """Validate and accept password"""
        password = self.password_input.text().strip()
        confirm = self.confirm_input.text().strip()
        
        if not password:
            QMessageBox.warning(self, "Error", "Please enter a password!")
            return
        
        if len(password) < 3:
            QMessageBox.warning(self, "Error", "Password must be at least 3 characters!")
            return
            
        if password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match!")
            return
        
        self.password = password
        self.accept()


# AddItemDialog'daki create_item metodunu değiştir:

class MoveDialog(QDialog):
    """Dialog for moving files and folders to another location"""
    def __init__(self, current_path: str, item_name: str, item_type: str, parent=None):
        super().__init__(parent)
        self.current_path = current_path
        self.item_name = item_name
        self.item_type = item_type
        self.selected_path = None
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle(f"Move {self.item_type.title()}")
        self.setFixedSize(500, 500) # Adjusted size for consistency
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Title
        title_label = QLabel(f"Moving '{self.item_name}'")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # Tree view for folder selection
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0,0,0,0)
        tree_layout.setSpacing(8)

        info_label = QLabel("Select destination folder:")
        self.tree_view = QTreeView()
        self.file_model = QFileSystemModel()
        self.file_model.setRootPath("data")
        self.file_model.setFilter(QDir.Filter.Dirs | QDir.Filter.NoDotAndDotDot)
        
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index("data"))
        self.tree_view.hideColumn(1)
        self.tree_view.hideColumn(2)
        self.tree_view.hideColumn(3)

        tree_layout.addWidget(info_label)
        tree_layout.addWidget(self.tree_view)
        layout.addWidget(tree_container)
        
        # Selected path display
        self.path_label = QLabel("Selected: data/")
        self.path_label.setObjectName("pathLabel") # For potential specific styling
        layout.addWidget(self.path_label)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(BUTTON_SPACING)
        
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Move")
        
        self.cancel_button.setMinimumSize(100, 35)
        self.ok_button.setMinimumSize(100, 35)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept_dialog)
        self.tree_view.selectionModel().selectionChanged.connect(self.on_selection_changed)

    def setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SECTION_BACKGROUND};
                color: {PRIMARY_TEXT};
                border-radius: {DIALOG_BORDER_RADIUS}px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                font-weight: bold;
            }}
            QLabel#pathLabel {{
                font-size: 12px;
                font-weight: normal;
                color: #BDC3C7;
            }}
            QLabel[objectName="title"] {{
                font-size: {TITLE_FONT_SIZE}px;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                margin-bottom: 10px;
            }}
            QTreeView {{
                background-color: {WIDGET_BACKGROUND};
                color: {PRIMARY_TEXT};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {INPUT_BORDER_RADIUS}px;
                alternate-background-color: {HOVER_BACKGROUND};
                selection-background-color: {PRIMARY_COLOR};
                padding: 5px;
            }}
            QTreeView::item {{
                padding: 5px;
                border-radius: 3px;
            }}
            QTreeView::item:selected {{
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
            }}
            QHeaderView::section {{
                background-color: {WIDGET_BACKGROUND};
                color: {PRIMARY_TEXT};
                padding: 4px;
                border: 1px solid {PRIMARY_BORDER};
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                border: none;
                padding: 5px 15px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                font-size: {BUTTON_FONT_SIZE}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
            QPushButton[objectName="cancel"] {{
                background-color: {DANGER_COLOR};
            }}
            QPushButton[objectName="cancel"]:hover {{
                background-color: #C0392B;
            }}
        """)
        self.cancel_button.setObjectName("cancel")

    def on_selection_changed(self):
        # ... (on_selection_changed logic remains the same)
        indexes = self.tree_view.selectionModel().selectedIndexes()
        if indexes:
            index = indexes[0]
            path = self.file_model.filePath(index)
            display_path = path.replace("data", "root") if path != "data" else "root"
            self.path_label.setText(f"Selected: {display_path}/")
            self.selected_path = path
    
    def accept_dialog(self):
        # ... (accept_dialog logic remains the same)
        if not self.selected_path:
            self.selected_path = "data"
        if self.selected_path == os.path.dirname(self.current_path):
            QMessageBox.information(self, "Info", "Cannot move to the same location!")
            return
        if self.item_type == 'folder':
            if self.selected_path.startswith(self.current_path):
                QMessageBox.warning(self, "Error", "Cannot move a folder to its own subdirectory!")
                return
        self.accept()

class AddItemDialog(QDialog):
    """Dialog for adding new files and folders"""
    def __init__(self, current_path: str, parent=None):
        super().__init__(parent)
        self.current_path = current_path
        self.item_type = None
        self.item_name = None
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle("Add New Item")
        self.setFixedSize(500, 320) # Adjusted size
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Title
        title_label = QLabel("Add New Item")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # Type selection
        type_container = QWidget()
        type_layout = QVBoxLayout(type_container)
        type_layout.setContentsMargins(0, 0, 0, 0)
        type_layout.setSpacing(8)
        
        type_label = QLabel("Select Type:")
        type_layout.addWidget(type_label)
        
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(20)
        self.button_group = QButtonGroup()
        
        self.file_radio = QRadioButton("📄 File")
        self.folder_radio = QRadioButton("📁 Folder")
        
        self.button_group.addButton(self.file_radio, 0)
        self.button_group.addButton(self.folder_radio, 1)
        
        radio_layout.addWidget(self.file_radio)
        radio_layout.addWidget(self.folder_radio)
        radio_layout.addStretch()
        
        type_layout.addLayout(radio_layout)
        layout.addWidget(type_container)
        
        # Name input
        name_container = QWidget()
        name_layout = QVBoxLayout(name_container)
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(8)
        
        name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter item name...")
        self.name_input.setMinimumHeight(40)
        
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)
        layout.addWidget(name_container)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(BUTTON_SPACING)
        
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Create")
        
        self.cancel_button.setMinimumSize(100, 35)
        self.ok_button.setMinimumSize(100, 35)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Set default selection
        self.file_radio.setChecked(True)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept_dialog)
        self.name_input.returnPressed.connect(self.accept_dialog)

    def setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SECTION_BACKGROUND};
                color: {PRIMARY_TEXT};
                border-radius: {DIALOG_BORDER_RADIUS}px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                font-weight: bold;
            }}
            QLabel[objectName="title"] {{
                font-size: {TITLE_FONT_SIZE}px;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                margin-bottom: 10px;
            }}
            QLineEdit {{
                background-color: {WIDGET_BACKGROUND};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {INPUT_BORDER_RADIUS}px;
                padding: 5px 10px;
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                selection-background-color: {PRIMARY_COLOR};
                min-height: 28px; /* 40px - padding - border */
            }}
            QLineEdit:focus {{
                border-color: {FOCUS_BORDER};
            }}
            QRadioButton {{
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                font-weight: normal;
                spacing: 10px;
            }}
            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
            }}
            QRadioButton::indicator:unchecked {{
                border: 2px solid {PRIMARY_BORDER};
                background-color: {WIDGET_BACKGROUND};
                border-radius: 11px;
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {PRIMARY_COLOR};
                background-color: {PRIMARY_COLOR};
                border-radius: 11px;
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                border: none;
                padding: 5px 15px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                font-size: {BUTTON_FONT_SIZE}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
            QPushButton[objectName="cancel"] {{
                background-color: {DANGER_COLOR};
            }}
            QPushButton[objectName="cancel"]:hover {{
                background-color: #C0392B;
            }}
        """)
        self.cancel_button.setObjectName("cancel")
        
    def accept_dialog(self):
        """Validate input and create the item"""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name!")
            return
        
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in name for char in invalid_chars):
            QMessageBox.warning(self, "Error", "Name contains invalid characters!")
            return
        
        self.item_type = "file" if self.file_radio.isChecked() else "folder"
        self.item_name = name
        
        if self.create_item():
            self.accept()

    def create_item(self):
        """Create the actual file or folder"""
        try:
            if self.item_type == "folder":
                # For folders, add -__ prefix
                folder_name = f"-__{self.item_name}"
                folder_path = os.path.join(self.current_path, folder_name)
                
                # Check if folder already exists
                if os.path.exists(folder_path):
                    QMessageBox.warning(self, "Error", f"A folder named '{self.item_name}' already exists!")
                    return False
                
                # Create the folder
                os.makedirs(folder_path, exist_ok=True)
                print(f"DEBUG: Created folder: {folder_path}")
                
            else:  # file
                # For files, create a directory with the file name
                file_dir = os.path.join(self.current_path, self.item_name)
                
                # Check if file directory already exists
                if os.path.exists(file_dir):
                    QMessageBox.warning(self, "Error", f"A file named '{self.item_name}' already exists!")
                    return False
                
                # Create the file directory
                os.makedirs(file_dir, exist_ok=True)
                print(f"DEBUG: Created file directory: {file_dir}")
                
                # Create the content.html file
                content_file = os.path.join(file_dir, "content.html")
                with open(content_file, 'w', encoding='utf-8') as f:
                    f.write("")  # Empty content initially
                print(f"DEBUG: Created content file: {content_file}")
                
                # Open password dialog for new files
                password_dialog = SetPasswordDialog(self.item_name, self)
                if password_dialog.exec() != QDialog.Accepted:
                    # User cancelled password dialog, remove created directory
                    import shutil
                    shutil.rmtree(file_dir)
                    return False
                
                # Create password file with user-defined password
                password_file = os.path.join(file_dir, "content.bin")
                user_password = password_dialog.password
                
                # Import password functions
                from hash import hash_password, save_hashed_password
                hashed_password = hash_password(user_password)
                save_hashed_password(password_file, hashed_password)
                print(f"DEBUG: Created password file: {password_file} with user password")
            
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to create item: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to create {self.item_type}: {str(e)}")
            return False

class MasterPasswordDialog(QDialog):
    """Dialog for changing master password"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()
        
    def setup_ui(self):
        self.setWindowTitle("Change Master Password")
        self.setFixedSize(500, 420)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Title
        title_label = QLabel("Change Master Password")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setObjectName("title")
        layout.addWidget(title_label)
        
        # Current password
        current_container = QWidget()
        current_layout = QVBoxLayout(current_container)
        current_layout.setContentsMargins(0, 0, 0, 0)
        current_layout.setSpacing(8)
        current_label = QLabel("Current Password:")
        self.current_input = QLineEdit()
        self.current_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_input.setPlaceholderText("Enter current password...")
        self.current_input.setMinimumHeight(40)
        current_layout.addWidget(current_label)
        current_layout.addWidget(self.current_input)
        layout.addWidget(current_container)
        
        # New password
        new_container = QWidget()
        new_layout = QVBoxLayout(new_container)
        new_layout.setContentsMargins(0, 0, 0, 0)
        new_layout.setSpacing(8)
        new_label = QLabel("New Password:")
        self.new_input = QLineEdit()
        self.new_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_input.setPlaceholderText("Enter new password...")
        self.new_input.setMinimumHeight(40)
        new_layout.addWidget(new_label)
        new_layout.addWidget(self.new_input)
        layout.addWidget(new_container)
        
        # Confirm password
        confirm_container = QWidget()
        confirm_layout = QVBoxLayout(confirm_container)
        confirm_layout.setContentsMargins(0, 0, 0, 0)
        confirm_layout.setSpacing(8)
        confirm_label = QLabel("Confirm Password:")
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_input.setPlaceholderText("Re-enter new password...")
        self.confirm_input.setMinimumHeight(40)
        confirm_layout.addWidget(confirm_label)
        confirm_layout.addWidget(self.confirm_input)
        layout.addWidget(confirm_container)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(BUTTON_SPACING)
        
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("Change")
        
        self.cancel_button.setMinimumSize(100, 35)
        self.ok_button.setMinimumSize(100, 35)
        
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept_dialog)
        self.confirm_input.returnPressed.connect(self.accept_dialog)

    def setup_style(self):
        # This style is now identical to RenameDialog's
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {SECTION_BACKGROUND};
                color: {PRIMARY_TEXT};
                border-radius: {DIALOG_BORDER_RADIUS}px;
            }}
            QLabel {{
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                font-weight: bold;
            }}
            QLabel[objectName="title"] {{
                font-size: {TITLE_FONT_SIZE}px;
                color: {PRIMARY_COLOR};
                font-weight: bold;
                margin-bottom: 10px;
            }}
            QLineEdit {{
                background-color: {WIDGET_BACKGROUND};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {INPUT_BORDER_RADIUS}px;
                padding: 5px 10px;
                color: {PRIMARY_TEXT};
                font-size: {MAIN_FONT_SIZE}px;
                selection-background-color: {PRIMARY_COLOR};
                min-height: 28px; /* 40px - padding - border */
            }}
            QLineEdit:focus {{
                border-color: {FOCUS_BORDER};
            }}
            QPushButton {{
                background-color: {PRIMARY_COLOR};
                color: {PRIMARY_TEXT};
                border: none;
                padding: 5px 15px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                font-size: {BUTTON_FONT_SIZE}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {PRIMARY_HOVER_COLOR};
            }}
            QPushButton:pressed {{
                background-color: {PRIMARY_PRESSED_COLOR};
            }}
            QPushButton[objectName="cancel"] {{
                background-color: {DANGER_COLOR};
            }}
            QPushButton[objectName="cancel"]:hover {{
                background-color: #C0392B;
            }}
        """)
        self.cancel_button.setObjectName("cancel")

    def accept_dialog(self):
        # ... (accept_dialog logic remains the same)
        current = self.current_input.text().strip()
        new = self.new_input.text().strip()
        confirm = self.confirm_input.text().strip()
        if not current:
            QMessageBox.warning(self, "Error", "Please enter your current password!")
            return
        if not new:
            QMessageBox.warning(self, "Error", "Please enter your new password!")
            return
        if new != confirm:
            QMessageBox.warning(self, "Error", "New passwords do not match!")
            return
        if len(new) < 3:
            QMessageBox.warning(self, "Error", "Password must be at least 3 characters!")
            return
        # Password verification/saving logic follows...
        self.accept()
# [PinManager, HistoryManager, FileSystemManager classes remain unchanged]
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
    
    def update_path(self, old_path: str, new_path: str):
        """Update path for pinned items when moved/renamed"""
        for item in self.pinned_items:
            if item.full_path == old_path:
                item.full_path = new_path
                # Update name if it's a direct match
                if item.name == os.path.basename(old_path):
                    item.name = os.path.basename(new_path)
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
    
    def remove_item(self, file_path: str):
        """Remove specific item from history"""
        self.history_items = [item for item in self.history_items if item.full_path != file_path]
        self.save_history()
    
    def update_path(self, old_path: str, new_path: str):
        """Update path for history items when moved/renamed"""
        for item in self.history_items:
            if item.full_path == old_path:
                item.full_path = new_path
                # Update name if it's a direct match
                if item.name == os.path.basename(old_path):
                    item.name = os.path.basename(new_path)
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
    
    def rename_item(self, item: FileSystemItem, new_name: str) -> Tuple[bool, str]:
        """Rename a file or folder"""
        try:
            if isinstance(item, FolderItem):
                # For folders, add -__ prefix
                new_folder_name = f"-__{new_name}"
                new_path = os.path.join(os.path.dirname(item.full_path), new_folder_name)
            else:
                # For files, use name as is
                new_path = os.path.join(os.path.dirname(item.full_path), new_name)
            
            print(f"DEBUG RENAME FS: Old path: {item.full_path}")
            print(f"DEBUG RENAME FS: New path: {new_path}")
            
            # Check if target already exists
            if os.path.exists(new_path):
                return False, "An item with this name already exists!"
            
            # Rename the item
            os.rename(item.full_path, new_path)
            
            print(f"DEBUG RENAME FS: Rename successful")
            return True, new_path
            
        except Exception as e:
            print(f"DEBUG RENAME FS: Error: {str(e)}")
            return False, f"Rename error: {str(e)}"
    
    def move_item(self, item: FileSystemItem, target_path: str) -> Tuple[bool, str]:
        """Move a file or folder to target location"""
        try:
            # Create target path
            new_path = os.path.join(target_path, os.path.basename(item.full_path))
            
            print(f"DEBUG MOVE FS: Old path: {item.full_path}")
            print(f"DEBUG MOVE FS: Target path: {target_path}")
            print(f"DEBUG MOVE FS: New path: {new_path}")
            
            # Check if target already exists
            if os.path.exists(new_path):
                return False, "An item with the same name exists at destination!"
            
            # Move the item
            shutil.move(item.full_path, new_path)
            
            print(f"DEBUG MOVE FS: Move successful")
            return True, new_path
            
        except Exception as e:
            print(f"DEBUG MOVE FS: Error: {str(e)}")
            return False, f"Move error: {str(e)}"
    
    def delete_item(self, item: FileSystemItem) -> Tuple[bool, str]:
        """Delete a file or folder"""
        try:
            if isinstance(item, FolderItem):
                # Delete folder and all contents
                shutil.rmtree(item.full_path)
            else:
                # Delete file directory
                shutil.rmtree(item.full_path)
            
            return True, "Success"
            
        except Exception as e:
            return False, f"Delete error: {str(e)}"

# FIXED: Enhanced PasswordManager with better error handling
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
        
        # FIXED: Better handling of password dialog
        try:
            dialog = ChangePasswordDialog(password_file, parent=parent_widget, currentHash=current_hash)
            result = dialog.exec()
            return result == QDialog.Accepted
        except Exception as e:
            print(f"Error opening password change dialog: {e}")
            if parent_widget:
                QMessageBox.critical(
                    parent_widget, 
                    "Error", 
                    f"Failed to open password change dialog: {str(e)}"
                )
            return False


# [LayoutFactory, BaseWidget, truncate_text function, and widget classes remain unchanged]
class LayoutFactory:
    """Factory for creating consistent layouts"""
    
    @staticmethod
    def create_zero_margin_layout(spacing=0, margins=(0, 0, 0, 0)) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout
    
    @staticmethod
    def create_zero_vertical_layout(spacing=0, margins=(0, 0, 0, 0)) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setContentsMargins(*margins)
        layout.setSpacing(spacing)
        return layout


class BaseWidget(QWidget):
    """Base class for all custom widgets"""
    
    def __init__(self, fixed_size: QSize, parent=None):
        super().__init__(parent)
        self.setFixedSize(fixed_size)
        self.setup_ui()
        self.setup_style()
        self.connect_signals()
    
    def setup_ui(self):
        """Setup the UI components - override in subclasses"""
        raise NotImplementedError("Subclasses must implement setup_ui()")
    
    def setup_style(self):
        """Setup the widget styling - override in subclasses"""
        raise NotImplementedError("Subclasses must implement setup_style()")
    
    def connect_signals(self):
        """Connect signals and slots - override in subclasses"""
        raise NotImplementedError("Subclasses must implement connect_signals()")


def truncate_text(text: str, max_width: int, font_metrics: QFontMetrics) -> str:
    """Truncate text to fit within max_width using font metrics"""
    if font_metrics.horizontalAdvance(text) <= max_width:
        return text
    
    ellipsis = "..."
    ellipsis_width = font_metrics.horizontalAdvance(ellipsis)
    
    # If even ellipsis doesn't fit, return empty
    if ellipsis_width >= max_width:
        return ""
    
    # Binary search for the right length
    left, right = 0, len(text)
    result = ""
    
    while left <= right:
        mid = (left + right) // 2
        truncated = text[:mid] + ellipsis
        
        if font_metrics.horizontalAdvance(truncated) <= max_width:
            result = truncated
            left = mid + 1
        else:
            right = mid - 1
    
    return result


class FileWidget(BaseWidget):
    """Widget representing a file"""
    
    clicked = Signal(str)  # Emits file name when clicked
    context_menu_requested = Signal(str, object)  # Emits file name and position
    
    def __init__(self, file_item: FileItem, fixed_size: QSize, parent=None):
        self.file_item = file_item
        super().__init__(fixed_size, parent)
    
    def setup_ui(self):
        layout = LayoutFactory.create_zero_vertical_layout(5, WIDGET_CONTENT_PADDING)
        self.setLayout(layout)
        
        # File icon and name container
        content_layout = LayoutFactory.create_zero_vertical_layout(8)
        
        # File icon
        icon_label = QLabel("📄")
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(f"""
            color: {PRIMARY_COLOR};
            font-size: 24px;
            background-color: transparent;
        """)
        
        # File name button with text truncation
        self.button = QPushButton()
        self.button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Truncate text to fit button
        font = QFont()
        font.setPointSize(WIDGET_FONT_SIZE)
        font.setBold(True)
        font_metrics = QFontMetrics(font)
        
        # Calculate available width (button width minus padding)
        available_width = self.size().width() - WIDGET_CONTENT_PADDING[0] - WIDGET_CONTENT_PADDING[2] - 16
        truncated_text = truncate_text(self.file_item.display_name, available_width, font_metrics)
        self.button.setText(truncated_text)
        self.button.setToolTip(self.file_item.display_name)  # Show full name on hover
        
        content_layout.addWidget(icon_label)
        content_layout.addWidget(self.button, 1)
        
        layout.addLayout(content_layout)
    
    def setup_style(self):
        self.setStyleSheet(f"""
            FileWidget {{
                border-radius: {WIDGET_BORDER_RADIUS}px;
                background-color: {FILE_WIDGET_BACKGROUND};
                border: 2px solid transparent;
            }}
            FileWidget:hover {{
                background-color: {FILE_WIDGET_HOVER};
                border: 2px solid {PRIMARY_COLOR};
            }}
        """)
        
        self.button.setStyleSheet(f"""
            QPushButton {{
                border-radius: {BUTTON_BORDER_RADIUS}px;
                background-color: transparent;
                border: none;
                color: {PRIMARY_TEXT};
                font-size: {WIDGET_FONT_SIZE}px;
                font-weight: bold;
                text-align: center;
                padding: 8px;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QPushButton:pressed {{
                background-color: {FILE_WIDGET_PRESSED};
            }}
        """)
    
    def connect_signals(self):
        self.button.clicked.connect(lambda: self.clicked.emit(self.file_item.name))
        self.button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.button.customContextMenuRequested.connect(
            lambda pos: self.context_menu_requested.emit(self.file_item.name, pos)
        )


# [FolderWidget, AddFolderWidget, HistoryWidget, PinnedWidget classes remain unchanged - skipping for brevity]
# ... (All widget classes remain the same) ...

# [NavigationBar, SidebarWidget, FileGridManager, etc. classes remain unchanged]
# ... (All other classes remain the same until MainWindow) ...


class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.fs_manager = FileSystemManager()
        self.password_manager = PasswordManager()
        self.history_manager = HistoryManager()
        self.pin_manager = PinManager()
        self.login_window = None
        
        self.setWindowTitle("Modular File Manager")
        self.setWindowState(Qt.WindowState.WindowMaximized)
        
        self.setup_ui()
        self.setup_style()
        self.setup_connections()
        
    # [All setup methods remain unchanged until context menu methods]
    
    def setup_ui(self):
        """Setup the main UI"""
        # Main layout
        main_layout = LayoutFactory.create_zero_margin_layout(MAIN_LAYOUT_SPACING, MAIN_WINDOW_MARGINS)
        
        # Sidebar
        self.sidebar = SidebarWidget()
        
        # Right layout
        right_layout = LayoutFactory.create_zero_margin_layout(MAIN_LAYOUT_SPACING)
        
        # Middle section
        self.setup_middle_section()
        
        # History section
        self.setup_history_section()
        
        right_layout.addWidget(self.mid_widget, stretch=10)
        right_layout.addWidget(self.history_widget, stretch=3)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addLayout(right_layout)
        
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
    
    def setup_style(self):
        """Setup main window styling"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {MAIN_BACKGROUND};
            }}
        """)
    
    def setup_middle_section(self):
        """Setup the middle section with files and quick access"""
        self.mid_widget = QWidget()
        self.mid_widget.setStyleSheet(f"background-color: transparent; border-radius: {MAIN_BORDER_RADIUS}px;")
        mid_layout = LayoutFactory.create_zero_vertical_layout(SECTION_SPACING)
        self.mid_widget.setLayout(mid_layout)
        
        # Files section
        self.setup_files_section()
        
        # Quick access section
        self.setup_quick_access_section()
        
        mid_layout.addWidget(self.files_widget, stretch=5)
        mid_layout.addWidget(self.quick_widget, stretch=3)

    def open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self)
        dialog.exec()

    def setup_files_section(self):
        """Setup the files section"""
        self.files_widget = QWidget()
        self.files_widget.setStyleSheet(f"""
            background-color: {SECTION_BACKGROUND};
            border-radius: {MAIN_BORDER_RADIUS}px;
        """)
        
        files_layout = LayoutFactory.create_zero_vertical_layout(SECTION_SPACING, SECTION_MARGINS)
        self.files_widget.setLayout(files_layout)
        
        # Navigation bar
        self.nav_bar = NavigationBar()
        files_layout.addWidget(self.nav_bar)
        
        # Scroll area for files
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(f"background-color: transparent; border: none; border-radius: {WIDGET_BORDER_RADIUS}px;")
        
        self.files_grid_content = QWidget()
        self.files_grid_content.setStyleSheet(f"background-color: transparent; border-radius: {WIDGET_BORDER_RADIUS}px;")
        
        self.files_grid_layout = QGridLayout()
        self.files_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.files_grid_layout.setSpacing(GRID_SPACING)
        self.files_grid_content.setLayout(self.files_grid_layout)
        
        self.scroll_area.setWidget(self.files_grid_content)
        files_layout.addWidget(self.scroll_area)
        
        # Setup grid manager
        self.grid_manager = FileGridManager(self.files_grid_layout, self.files_widget)
    
    def setup_quick_access_section(self):
        """Setup the quick access section with pinned files"""
        self.quick_widget = QWidget()
        self.quick_widget.setStyleSheet(f"""
            background-color: {SECTION_BACKGROUND};
            border-radius: {MAIN_BORDER_RADIUS}px;
        """)
        
        quick_layout = LayoutFactory.create_zero_vertical_layout(GRID_SPACING, SECTION_MARGINS)
        self.quick_widget.setLayout(quick_layout)
        
        # Scroll area for quick access
        self.quick_scroll_area = QScrollArea()
        self.quick_scroll_area.setWidgetResizable(True)
        self.quick_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.quick_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.quick_scroll_area.setStyleSheet(f"background-color: transparent; border: none; border-radius: {WIDGET_BORDER_RADIUS}px;")
        
        # Content widget
        self.quick_grid_content = QWidget()
        self.quick_grid_content.setStyleSheet(f"background-color: transparent; border-radius: {WIDGET_BORDER_RADIUS}px;")
        
        self.quick_grid_layout = QGridLayout()
        self.quick_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.quick_grid_layout.setSpacing(GRID_SPACING)
        self.quick_grid_content.setLayout(self.quick_grid_layout)
        
        self.quick_scroll_area.setWidget(self.quick_grid_content)
        quick_layout.addWidget(self.quick_scroll_area)
        
        # Setup quick access manager
        self.quick_access_manager = QuickAccessManager(
            self.quick_widget, 
            self.quick_grid_layout, 
            self.pin_manager
        )
        
    def setup_history_section(self):
        """Setup the history section with full functionality"""
        self.history_widget = QWidget()
        self.history_widget.setStyleSheet(f"""
            background-color: {SECTION_BACKGROUND};
            border-radius: {MAIN_BORDER_RADIUS}px;
        """)
        
        history_layout = LayoutFactory.create_zero_vertical_layout(GRID_SPACING, SECTION_MARGINS)
        self.history_widget.setLayout(history_layout)
        
        # Scroll area for history
        self.history_scroll_area = QScrollArea()
        self.history_scroll_area.setWidgetResizable(True)
        self.history_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.history_scroll_area.setStyleSheet(f"background-color: transparent; border: none; border-radius: {WIDGET_BORDER_RADIUS}px;")
        
        # Content widget
        self.history_grid_content = QWidget()
        self.history_grid_content.setStyleSheet(f"background-color: transparent; border-radius: {WIDGET_BORDER_RADIUS}px;")
        
        self.history_grid_layout = QGridLayout()
        self.history_grid_layout.setContentsMargins(0, 0, 0, 0)
        self.history_grid_layout.setSpacing(GRID_SPACING)
        self.history_grid_content.setLayout(self.history_grid_layout)
        
        self.history_scroll_area.setWidget(self.history_grid_content)
        history_layout.addWidget(self.history_scroll_area)
        
        # Setup grid manager
        self.history_grid_manager = HistoryGridManager(
            self.history_grid_layout, 
            self.history_widget, 
            self.history_manager
        )
    
    def setup_connections(self):
        """Setup signal connections"""
        self.nav_bar.back_clicked.connect(self.go_back)
        self.sidebar.master_password_clicked.connect(self.change_master_password)
        self.sidebar.settings_clicked.connect(self.open_settings)  # YENİ

    def populate_files(self):
        """Populate the files grid with current directory contents"""
        items = self.fs_manager.scan_directory(self.fs_manager.current_path)
        widget_size = self.grid_manager.calculate_widget_size(len(items))
        self.grid_manager.populate_grid(items, widget_size)
        self.update_navigation()
        
        # Connect widget signals
        for i in range(self.files_grid_layout.count()):
            item = self.files_grid_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, FileWidget):
                    widget.clicked.connect(self.on_file_clicked)
                    widget.context_menu_requested.connect(self.on_file_context_menu)
                elif isinstance(widget, FolderWidget):
                    widget.clicked.connect(self.on_folder_clicked)
                    widget.context_menu_requested.connect(self.on_folder_context_menu)
                elif isinstance(widget, AddFolderWidget):
                    widget.clicked.connect(self.on_add_item_clicked)
    
    def populate_history(self):
        """Populate history area with recent files"""
        self.history_grid_manager.populate_history()
        
        # Connect history widget signals
        for i in range(self.history_grid_layout.count()):
            item = self.history_grid_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), HistoryWidget):
                widget = item.widget()
                widget.clicked.connect(self.on_history_file_clicked)
                widget.context_menu_requested.connect(self.on_history_context_menu)
    
    def populate_quick_access(self):
        """Populate quick access area with pinned files"""
        self.quick_access_manager.populate_quick_access()
        
        # Connect pinned widget signals
        for i in range(self.quick_grid_layout.count()):
            item = self.quick_grid_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), PinnedWidget):
                widget = item.widget()
                widget.clicked.connect(self.on_pinned_file_clicked)
                widget.context_menu_requested.connect(self.on_pinned_context_menu)
    
    # [Navigation and file handling methods remain unchanged]
    def update_navigation(self):
        """Update navigation bar with current path"""
        current_path = self.fs_manager.current_path.replace("-__", "")
        can_go_back = self.fs_manager.can_go_back()
        self.nav_bar.update_path(current_path, can_go_back)
    
    def go_back(self):
        """Navigate back to parent directory"""
        if self.fs_manager.go_back():
            self.populate_files()
    
    def change_master_password(self):
        """Open master password change dialog"""
        dialog = MasterPasswordDialog(self)
        dialog.exec()
    
    def on_add_item_clicked(self):
        """Handle + button click to add new items"""
        dialog = AddItemDialog(self.fs_manager.current_path, self)
        if dialog.exec() == QDialog.Accepted:
            # Refresh the files display
            self.populate_files()
    
    def on_folder_clicked(self, folder_name: str):
        """Handle folder click"""
        if self.fs_manager.navigate_to_folder(folder_name):
            self.populate_files()
    
    def on_file_clicked(self, file_name: str):
        """Handle file click"""
        file_item = self.fs_manager.get_item(file_name)
        if not file_item or not isinstance(file_item, FileItem):
            return
        
        self._open_file_with_password_check(file_item)
    
    def on_history_file_clicked(self, file_path: str):
        """Handle history file click"""
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self, "File Not Found", 
                f"This file no longer exists:\n{file_path}"
            )
            return
        
        # Create a FileItem from the path
        file_item = FileItem(
            name=os.path.basename(file_path),
            full_path=file_path,
            item_type='file'
        )
        
        self._open_file_with_password_check(file_item)
    
    def on_pinned_file_clicked(self, file_path: str):
        """Handle pinned file click"""
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self, "File Not Found", 
                f"This file no longer exists:\n{file_path}"
            )
            return
        
        # Create a FileItem from the path
        file_item = FileItem(
            name=os.path.basename(file_path),
            full_path=file_path,
            item_type='file'
        )
        
        self._open_file_with_password_check(file_item)
    
    def _open_file_with_password_check(self, file_item: FileItem):
        """Open file with password check (common logic)"""
        # Check if password file exists
        password_hash = self.password_manager.load_password_hash(file_item)
        if password_hash is None:
            # If no password file exists, open directly without password check
            self.history_manager.add_file_to_history(file_item)
            self.populate_history()
            self.open_file_content(file_item)
            return
        
        # Open login window for password-protected files
        def on_login_success():
            if self.login_window:
                self.login_window.close()
                self.login_window.deleteLater()
                self.login_window = None
            
            # Add to history (only files, not folders)
            self.history_manager.add_file_to_history(file_item)
            self.populate_history()  # Refresh history display
            
            self.open_file_content(file_item)
        
        self.login_window = LoginWindow(
            expected_password_hash=password_hash,
            on_success=on_login_success
        )
        self.login_window.show()
    
    def open_file_content(self, file_item: FileItem):
        """Open the content file in notepad"""
        content_file = file_item.content_file_path
        
        print(f"DEBUG: Opening content file: {content_file}")
        print(f"DEBUG: File item full path: {file_item.full_path}")
        print(f"DEBUG: File item directory: {os.path.dirname(file_item.full_path)}")
        
        # Create content file if it doesn't exist
        if not os.path.exists(content_file):
            content_dir = os.path.dirname(content_file)
            print(f"DEBUG: Content file doesn't exist, creating in: {content_dir}")
            
            # Only create directory if it doesn't exist
            if not os.path.exists(content_dir):
                os.makedirs(content_dir, exist_ok=True)
                print(f"DEBUG: Created directory: {content_dir}")
            
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write("\n")
            print(f"DEBUG: Created content file: {content_file}")
        
        # Open in notepad
        try:
            subprocess.run([sys.executable, "notepad.py", content_file], check=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open notepad: {e}")
    
    def on_file_context_menu(self, file_name: str, pos):
        """Handle file context menu"""
        file_item = self.fs_manager.get_item(file_name)
        if not file_item:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {WIDGET_BACKGROUND};
                color: {PRIMARY_TEXT};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {BUTTON_BORDER_RADIUS}px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 12px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {PRIMARY_COLOR};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {PRIMARY_BORDER};
                margin: 5px 0;
            }}
        """)
        
        # Pin/Unpin action
        is_pinned = self.pin_manager.is_pinned(file_item.full_path)
        if is_pinned:
            pin_action = menu.addAction("📌 Unpin")
            pin_action.triggered.connect(lambda: self.unpin_file(file_item))
        else:
            pin_action = menu.addAction("📌 Pin")
            pin_action.triggered.connect(lambda: self.pin_file(file_item))
        
        menu.addSeparator()
        
        # Rename action
        rename_action = menu.addAction("✏️ Rename")
        rename_action.triggered.connect(lambda: self.rename_item(file_item))
        
        # Move action
        move_action = menu.addAction("📂 Move")
        move_action.triggered.connect(lambda: self.move_item(file_item))
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self.delete_item(file_item))
        
        menu.addSeparator()
        
        # FIXED: Change password action
        change_password_action = menu.addAction("🔒 Change Password")
        change_password_action.triggered.connect(
            lambda: self.change_item_password(file_item)
        )
        
        # Convert local position to global
        global_pos = self.sender().mapToGlobal(pos)
        menu.exec(global_pos)
    
    # [Other context menu methods remain unchanged]
    def on_folder_context_menu(self, folder_name: str, pos):
        """Handle folder context menu"""
        folder_item = self.fs_manager.get_item(folder_name)
        if not folder_item:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {WIDGET_BACKGROUND};
                color: {PRIMARY_TEXT};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {BUTTON_BORDER_RADIUS}px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 12px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {PRIMARY_COLOR};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {PRIMARY_BORDER};
                margin: 5px 0;
            }}
        """)
        
        # Rename action
        rename_action = menu.addAction("✏️ Rename")
        rename_action.triggered.connect(lambda: self.rename_item(folder_item))
        
        # Move action
        move_action = menu.addAction("📂 Move")
        move_action.triggered.connect(lambda: self.move_item(folder_item))
        
        # Delete action
        delete_action = menu.addAction("🗑️ Delete")
        delete_action.triggered.connect(lambda: self.delete_item(folder_item))
        
        # Convert local position to global
        global_pos = self.sender().mapToGlobal(pos)
        menu.exec(global_pos)
    
    def on_history_context_menu(self, file_path: str, pos):
        """Handle history context menu"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {WIDGET_BACKGROUND};
                color: {PRIMARY_TEXT};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {BUTTON_BORDER_RADIUS}px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 12px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {PRIMARY_COLOR};
            }}
            QMenu::separator {{
                height: 1px;
                background-color: {PRIMARY_BORDER};
                margin: 5px 0;
            }}
        """)
        
        # Pin/Unpin action
        is_pinned = self.pin_manager.is_pinned(file_path)
        if is_pinned:
            pin_action = menu.addAction("📌 Unpin")
            pin_action.triggered.connect(lambda: self.unpin_file_by_path(file_path))
        else:
            pin_action = menu.addAction("📌 Pin")
            pin_action.triggered.connect(lambda: self.pin_file_by_path(file_path))
        
        menu.addSeparator()
        
        # Remove from history action
        remove_action = menu.addAction("🗑️ Remove from History")
        remove_action.triggered.connect(
            lambda: self.remove_from_history(file_path)
        )
        
        # Convert local position to global
        global_pos = self.sender().mapToGlobal(pos)
        menu.exec(global_pos)
    
    def on_pinned_context_menu(self, file_path: str, pos):
        """Handle pinned file context menu"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background-color: {WIDGET_BACKGROUND};
                color: {PRIMARY_TEXT};
                border: 2px solid {PRIMARY_BORDER};
                border-radius: {BUTTON_BORDER_RADIUS}px;
                padding: 5px;
            }}
            QMenu::item {{
                padding: 8px 12px;
                border-radius: {BUTTON_BORDER_RADIUS}px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background-color: {PRIMARY_COLOR};
            }}
        """)
        
        # Unpin action
        unpin_action = menu.addAction("📌 Unpin")
        unpin_action.triggered.connect(lambda: self.unpin_file_by_path(file_path))
        
        # Convert local position to global
        global_pos = self.sender().mapToGlobal(pos)
        menu.exec(global_pos)
    
    # [File operation methods remain unchanged until change_item_password]
    def rename_item(self, item: FileSystemItem):
        """Rename a file or folder"""
        dialog = RenameDialog(item.display_name, item.item_type, self)
        if dialog.exec() == QDialog.Accepted and dialog.new_name:
            old_path = item.full_path
            success, new_path_or_error = self.fs_manager.rename_item(item, dialog.new_name)
            
            if success:
                # Update history and pins with new path
                self.history_manager.update_path(old_path, new_path_or_error)
                if isinstance(item, FileItem):
                    self.pin_manager.update_path(old_path, new_path_or_error)
                
                # Refresh displays
                self.populate_files()
                self.populate_history()
                self.populate_quick_access()
                
            else:
                QMessageBox.critical(self, "Error", new_path_or_error)
    
    def move_item(self, item: FileSystemItem):
        """Move a file or folder"""
        dialog = MoveDialog(item.full_path, item.display_name, item.item_type, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_path:
            old_path = item.full_path
            success, new_path_or_error = self.fs_manager.move_item(item, dialog.selected_path)
            
            if success:
                # Update history and pins with new path
                self.history_manager.update_path(old_path, new_path_or_error)
                if isinstance(item, FileItem):
                    self.pin_manager.update_path(old_path, new_path_or_error)
                
                # Refresh displays
                self.populate_files()
                self.populate_history()
                self.populate_quick_access()
            else:
                QMessageBox.critical(self, "Error", new_path_or_error)
    
    def delete_item(self, item: FileSystemItem):
        """Delete a file or folder"""
        # Confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Delete Confirmation",
            f"Are you sure you want to delete '{item.display_name}' {item.item_type}?\n\nThis action cannot be undone!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, message = self.fs_manager.delete_item(item)
            
            if success:
                # Remove from history and pins
                self.history_manager.remove_item(item.full_path)
                if isinstance(item, FileItem):
                    self.pin_manager.unpin_file(item.full_path)
                
                # Refresh displays
                self.populate_files()
                self.populate_history()
                self.populate_quick_access()
            else:
                QMessageBox.critical(self, "Error", message)
    
    def pin_file(self, file_item: FileItem):
        """Pin a file"""
        if self.pin_manager.pin_file_item(file_item):
            self.populate_quick_access()
        else:
            QMessageBox.information(
                self, "Already Pinned", 
                f"'{file_item.display_name}' is already pinned!"
            )
    
    def pin_file_by_path(self, file_path: str):
        """Pin a file by path"""
        if not os.path.exists(file_path):
            return
        
        file_item = FileItem(
            name=os.path.basename(file_path),
            full_path=file_path,
            item_type='file'
        )
        self.pin_file(file_item)
    
    def unpin_file(self, file_item: FileItem):
        """Unpin a file"""
        self.pin_manager.unpin_file(file_item.full_path)
        self.populate_quick_access()
    
    def unpin_file_by_path(self, file_path: str):
        """Unpin a file by path"""
        self.pin_manager.unpin_file(file_path)
        self.populate_quick_access()
    
    def remove_from_history(self, file_path: str):
        """Remove specific file from history"""
        # Find and remove the item
        self.history_manager.history_items = [
            item for item in self.history_manager.history_items 
            if item.full_path != file_path
        ]
        self.history_manager.save_history()
        self.populate_history()
    
    # FIXED: Implemented change_item_password method
    def change_item_password(self, item: FileItem):
        """Change password for a file item"""
        if not isinstance(item, FileItem):
            QMessageBox.warning(self, "Error", "Password can only be changed for files!")
            return
        
        success = self.password_manager.change_password(item, self)
        if success:
            QMessageBox.information(
                self, 
                "Success", 
                f"Password for '{item.display_name}' has been changed successfully!"
            )
    
    def resizeEvent(self, event: QEvent):
        """Handle window resize"""
        super().resizeEvent(event)
        self.populate_files()
        self.populate_history()
        self.populate_quick_access()
    
    def showEvent(self, event: QEvent):
        """Handle window show"""
        super().showEvent(event)
        self.populate_files()
        self.populate_history()
        self.populate_quick_access()


# [ScrollAreaManager and main function remain unchanged]
class ScrollAreaManager:
    """Manages scroll area functionality"""
    
    @staticmethod
    def setup_horizontal_scroll(scroll_area: QScrollArea):
        """Setup horizontal scrolling with mouse wheel"""
        def wheel_event(event):
            h_scroll = scroll_area.horizontalScrollBar()
            delta = event.angleDelta().y()
            h_scroll.setValue(h_scroll.value() - delta // 2)
            event.accept()
        
        scroll_area.wheelEvent = wheel_event
    
    @staticmethod
    def setup_vertical_scroll(scroll_area: QScrollArea):
        """Setup vertical scrolling with mouse wheel"""
        def wheel_event(event):
            v_scroll = scroll_area.verticalScrollBar()
            delta = event.angleDelta().y()
            v_scroll.setValue(v_scroll.value() - delta // 4)
            event.accept()
        
        scroll_area.wheelEvent = wheel_event


def main(q_app_instance):
    global main_window_instance
    main_window_instance = MainWindow()
    main_window_instance.show()

if __name__ == "__main__":
    app_standalone = QApplication(sys.argv)
    main_window_instance_standalone = MainWindow()
    main_window_instance_standalone.show()
    sys.exit(app_standalone.exec())