# password_manager.py

import sys
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox, QApplication
)
from PySide6.QtCore import Qt, QSize
from hash import hash_password, verify_password, save_hashed_password, load_hashed_password

class ChangePasswordDialog(QDialog):
    # filePath: Hangi parola dosyasının değiştirileceği (örn: "data/main.bin" veya "data/KlasorAdı/content.bin")
    # currentHash: Opsiyonel. Eğer değiştirmeden önce mevcut hash'i biliyorsak, yükleme adımını atlayabiliriz.
    def __init__(self, filePath: str, parent=None, currentHash: bytes = None):
        super().__init__(parent)
        self.filePath = filePath
        print(filePath)
        self.currentHash = currentHash # Başlangıçta verilen hash

        self.setWindowTitle("Parolayı Değiştir")
        self.setFixedSize(400, 280) # Boyutu biraz büyüttüm
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        self.setStyleSheet("""
            QDialog {
                background-color: #3a3a3a;
                border-radius: 5px;
            }
            QLabel {
                color: white;
                font-size: 14px;
                margin-bottom: 5px;
            }
            QLineEdit {
                background-color: #2E2E2E;
                color: white;
                font-size: 16px;
                height: 35px;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 5px;
            }
            QPushButton {
                background-color: #3498DB;
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 4px;
                padding: 8px 15px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2980B9;
            }
            QPushButton:pressed {
                background-color: #1F6F97;
            }
        """)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        # Eski Parola (Sadece dosya zaten varsa göster)
        # Eğer parola dosyası yoksa (yani ilk kez parola belirlenecekse), eski parola sormaya gerek yok.
        # Bunu filePath'in varlığına göre kontrol edeceğiz.
        if os.path.exists(self.filePath):
            self.layout.addWidget(QLabel("Eski Parola:"))
            self.old_password_entry = QLineEdit(self)
            self.old_password_entry.setEchoMode(QLineEdit.Password)
            self.layout.addWidget(self.old_password_entry)
        else:
            self.old_password_entry = None # Dosya yoksa eski parola girişi yok
            # İlk defa parola belirlendiğini belirten bir mesaj gösterebiliriz.
            self.layout.addWidget(QLabel("Bu dosya için bir parola belirliyorsunuz."))


        # Yeni Parola
        self.layout.addWidget(QLabel("Yeni Parola:"))
        self.new_password_entry = QLineEdit(self)
        self.new_password_entry.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.new_password_entry)

        # Yeni Parola Tekrar
        self.layout.addWidget(QLabel("Yeni Parola (Tekrar):"))
        self.confirm_password_entry = QLineEdit(self)
        self.confirm_password_entry.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.confirm_password_entry)

        # Butonlar
        button_layout = QHBoxLayout()
        self.change_button = QPushButton("Kaydet", self) # "Kaydet" veya "Değiştir"
        self.change_button.clicked.connect(self.save_new_password)
        button_layout.addWidget(self.change_button)

        self.cancel_button = QPushButton("İptal", self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        self.layout.addLayout(button_layout)

        # İlk odak noktasını ayarla
        if self.old_password_entry:
            self.old_password_entry.setFocus()
        else:
            self.new_password_entry.setFocus()

    def save_new_password(self):
        old_pw = self.old_password_entry.text() if self.old_password_entry else "" # Eğer eski parola girişi yoksa boş string
        new_pw = self.new_password_entry.text()
        confirm_pw = self.confirm_password_entry.text()

        # Parola dosyasının bulunduğu dizini oluştur (yoksa)
        print("New Password saved to: "+self.filePath)
        
        os.makedirs(os.path.dirname(self.filePath), exist_ok=True)

        stored_hash = self.currentHash # Başlangıçta verilen hash'i kullan
        if stored_hash is None and os.path.exists(self.filePath):
            # Eğer başlangıçta hash verilmediyse ama dosya varsa, yükle
            try:
                stored_hash = load_hashed_password(self.filePath)
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Parola dosyası yüklenirken hata: {e}")
                return

        # Eğer dosya zaten varsa ve eski parola girişi aktifse, eski parolayı doğrula
        if self.old_password_entry is not None:
            if stored_hash is None: # Eski parola alanı varsa ama hash yüklenememişse
                QMessageBox.critical(self, "Hata", "Mevcut parola yüklenemedi. Dosya bozuk olabilir.")
                return

            if not verify_password(stored_hash, old_pw):
                QMessageBox.warning(self, "Hata", "Eski parola yanlış.")
                self.old_password_entry.clear()
                self.old_password_entry.setFocus()
                return

        # Yeni parolaların eşleştiğini ve boş olmadığını kontrol et
        if not new_pw:
            QMessageBox.warning(self, "Hata", "Yeni parola boş olamaz.")
            self.new_password_entry.setFocus()
            return
        
        if new_pw != confirm_pw:
            QMessageBox.warning(self, "Hata", "Yeni parolalar eşleşmiyor.")
            self.new_password_entry.clear()
            self.confirm_password_entry.clear()
            self.new_password_entry.setFocus()
            return
        
        # Yeni parolayı hash'le ve kaydet
        try:
            new_hashed_pw = hash_password(new_pw)
            save_hashed_password(self.filePath, new_hashed_pw)
            QMessageBox.information(self, "Başarılı", "Parola başarıyla kaydedildi!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Parola kaydedilirken bir hata oluştu: {e}")