# frontend/pages/rewards_page.py

import json
import os
from PyQt6.QtWidgets import (QDoubleSpinBox, QWidget, QVBoxLayout, QLabel, QTextEdit, 
                             QHBoxLayout, QComboBox, QPushButton, QLineEdit, 
                             QSpinBox, QCheckBox, QFileDialog, QFormLayout, QGroupBox, QMessageBox)
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import Qt

class RewardsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.triggers_file = "triggers.json"
        self.triggers_data = {}
        self.kick_rewards_data = {}
        os.makedirs("media", exist_ok=True) 
        
        self.init_ui()
        self.load_triggers_locales()

    def load_triggers_locales(self):
        """Carga solo los datos locales (triggers.json) al iniciar la app."""
        if os.path.exists(self.triggers_file):
            try:
                with open(self.triggers_file, "r", encoding="utf-8") as f:
                    self.triggers_data = json.load(f)
            except Exception as e:
                self.log(f"❌ Error al cargar {self.triggers_file}: {e}")
        self.actualizar_combobox()

    def cargar_recompensas_kick(self, lista_recompensas):
        """Recibe la lista de recompensas directamente desde la API de Kick."""
        self.kick_rewards_data.clear()
        for recompensa in lista_recompensas:
            titulo = recompensa.get("title", "").strip().lower()
            self.kick_rewards_data[titulo] = recompensa
        
        self.actualizar_combobox()

    def actualizar_combobox(self):
        """Mezcla los puntos de Kick y los locales en el ComboBox."""
        self.combo_rewards.blockSignals(True)
        self.combo_rewards.clear()
        self.combo_rewards.addItem("-- Selecciona o crea uno nuevo --", "")
        
        # 1. Añadir los de Kick
        for titulo in self.kick_rewards_data.keys():
            self.combo_rewards.addItem(f"🟢 [Kick] {titulo.title()}", titulo)
            
        # 2. Añadir los locales que no estén en Kick (por si creaste uno manual)
        for titulo in self.triggers_data.keys():
            if titulo not in self.kick_rewards_data:
                self.combo_rewards.addItem(f"💻 [Local] {titulo.title()}", titulo)
                
        self.combo_rewards.blockSignals(False)

    def on_reward_selected(self):
        """Rellena el formulario combinando los datos de Kick y tu archivo local."""
        titulo_key = self.combo_rewards.currentData()
        if not titulo_key:
            self.clear_form()
            return
            
        # Priorizar datos de Kick si existen, si no, usar los locales
        datos_kick = self.kick_rewards_data.get(titulo_key, {})
        datos_locales = self.triggers_data.get(titulo_key, {})

        # Rellenar campos (Si viene de Kick usa el de Kick, si no, el local)
        self.inp_name.setText(datos_kick.get("title", titulo_key))
        self.inp_cost.setValue(datos_kick.get("cost", datos_locales.get("cost", 100)))
        self.inp_desc.setText(datos_kick.get("description", datos_locales.get("description", "")))
        
        # El color y el enabled vienen en formatos específicos en Kick
        self.inp_color.setText(datos_kick.get("color", datos_locales.get("color", "")))
        self.chk_enabled.setChecked(datos_kick.get("is_enabled", datos_locales.get("enabled", True)))
        
        # El archivo multimedia SIEMPRE es local
        file_name = datos_locales.get("file", "")
        if file_name:
            self.lbl_file.setText(file_name)
            self.current_file_path = file_name
            self.current_file_type = datos_locales.get("type", "audio")
        else:
            self.lbl_file.setText("Sin archivo multimedia vinculado")
            self.current_file_path = ""

    def init_ui(self):
        layout = QVBoxLayout()
        
        # --- 1. Información para OBS ---
        info_obs = QLabel("URL para OBS (Fuente de Navegador): <b style='color:#53fc18;'>http://127.0.0.1:8081</b> (Ancho 1920, Alto 1080)")
        info_obs.setTextFormat(Qt.TextFormat.RichText)
        info_obs.setStyleSheet("background-color: #121516; padding: 10px; border: 1px solid #333; border-radius: 4px; margin-bottom: 5px;")
        info_obs.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(info_obs)

        # --- 2. Panel de Control de Recompensas ---
        group_box = QGroupBox("Gestión de Puntos Locales (triggers.json)")
        group_box.setStyleSheet("QGroupBox { border: 1px solid #333; border-radius: 5px; padding-top: 15px; font-weight: bold; }")
        group_layout = QVBoxLayout()

        # Selector y botón de nueva recompensa
        top_hlayout = QHBoxLayout()
        self.combo_rewards = QComboBox()
        self.combo_rewards.currentIndexChanged.connect(self.on_reward_selected)
        
        self.btn_new = QPushButton("✨ Crear Punto")
        self.btn_new.setStyleSheet("background-color: #00e5ff; color: black; font-weight: bold; padding: 5px;")
        self.btn_new.clicked.connect(self.create_new_reward)

        top_hlayout.addWidget(QLabel("Recompensa:"))
        top_hlayout.addWidget(self.combo_rewards, stretch=1)
        top_hlayout.addWidget(self.btn_new)
        group_layout.addLayout(top_hlayout)

        # Formulario de ajustes del punto
        form_layout = QFormLayout()
        
        self.inp_name = QLineEdit()
        self.inp_cost = QSpinBox()
        self.inp_cost.setRange(1, 9999999)
        self.inp_color = QLineEdit()
        self.inp_desc = QLineEdit()
        self.chk_enabled = QCheckBox("Punto Activado")
        
        # --- NUEVOS CONTROLES VISUALES ---
        self.inp_scale = QDoubleSpinBox()
        self.inp_scale.setRange(0.1, 5.0)
        self.inp_scale.setValue(1.0)
        self.inp_scale.setSingleStep(0.1)
        
        self.inp_duration = QSpinBox()
        self.inp_duration.setRange(0, 300) # 0 significa duración automática
        self.inp_duration.setSuffix(" seg (0 = Auto)")
        
        self.chk_random = QCheckBox("Aparición Aleatoria en pantalla")
        # ---------------------------------

        # Modal/Selector de archivo multimedia
        file_layout = QHBoxLayout()
        self.lbl_file = QLabel("Ningún archivo seleccionado")
        self.btn_file = QPushButton("📂 Añadir Archivo")
        self.btn_file.clicked.connect(self.select_file)
        file_layout.addWidget(self.lbl_file, stretch=1)
        file_layout.addWidget(self.btn_file)

        form_layout.addRow("Nombre (ID):", self.inp_name)
        form_layout.addRow("Coste:", self.inp_cost)
        form_layout.addRow("Color Hex:", self.inp_color)
        form_layout.addRow("Descripción:", self.inp_desc)
        form_layout.addRow("Multimedia:", file_layout)
        form_layout.addRow("Tamaño (Escala):", self.inp_scale)
        form_layout.addRow("Duración:", self.inp_duration)
        form_layout.addRow("", self.chk_random)
        form_layout.addRow("", self.chk_enabled)

        group_layout.addLayout(form_layout)

        # Botón para Guardar en JSON
        self.btn_save = QPushButton("💾 Guardar Recompensa")
        self.btn_save.setStyleSheet("background-color: #53fc18; color: black; font-weight: bold; padding: 8px; margin-top: 5px;")
        self.btn_save.clicked.connect(self.save_reward)
        group_layout.addWidget(self.btn_save)

        group_box.setLayout(group_layout)
        layout.addWidget(group_box)

        # --- 3. Consola de Canjes ---
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet("background-color: #121516; color: #00e5ff; font-family: Consolas; font-size: 13px; border: none;")
        layout.addWidget(self.consola)

        self.setLayout(layout)

    # --- FUNCIONES DE LÓGICA ---

    def load_triggers(self):
        """Carga los datos del archivo JSON en el ComboBox."""
        self.combo_rewards.blockSignals(True)
        self.combo_rewards.clear()
        self.combo_rewards.addItem("-- Selecciona o crea uno nuevo --", None)
        
        if os.path.exists(self.triggers_file):
            try:
                with open(self.triggers_file, "r", encoding="utf-8") as f:
                    self.triggers_data = json.load(f)
                    for key in self.triggers_data.keys():
                        self.combo_rewards.addItem(key, key)
            except Exception as e:
                self.log(f"❌ Error al cargar {self.triggers_file}: {e}")
        
        self.combo_rewards.blockSignals(False)

    def on_reward_selected(self):
        """Rellena el formulario con los datos de la recompensa seleccionada."""
        key = self.combo_rewards.currentData()
        if not key or key not in self.triggers_data:
            self.clear_form()
            return
            
        data = self.triggers_data[key]
        self.inp_name.setText(key)
        self.inp_cost.setValue(data.get("cost", 100))
        self.inp_color.setText(data.get("color", ""))
        self.inp_desc.setText(data.get("description", ""))
        self.chk_enabled.setChecked(data.get("enabled", True))
        
        file_name = data.get("file", "")
        if file_name:
            self.lbl_file.setText(file_name)
            self.current_file_path = file_name
            self.current_file_type = data.get("type", "audio")
        else:
            self.lbl_file.setText("Sin archivo")
            self.current_file_path = ""

    def clear_form(self):
        """Limpia los campos del formulario."""
        self.inp_name.clear()
        self.inp_cost.setValue(100)
        self.inp_color.clear()
        self.inp_desc.clear()
        self.chk_enabled.setChecked(True)
        self.lbl_file.setText("Ningún archivo seleccionado")
        self.current_file_path = ""

    def create_new_reward(self):
        """Limpia el formulario y abre el modal para elegir el archivo inmediatamente."""
        self.combo_rewards.setCurrentIndex(0)
        self.clear_form()
        self.inp_name.setFocus()
        self.select_file() # Abre el modal al darle a "Crear Punto"

    def select_file(self):
        file_filter = "Multimedia (*.mp3 *.wav *.ogg *.mp4 *.webm *.png *.jpg *.gif);;Audio (*.mp3 *.wav *.ogg);;Video (*.mp4 *.webm);;Imagen (*.png *.jpg *.gif)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo Multimedia", "", file_filter)
        
        if file_path:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join("media", file_name)
            
            if os.path.abspath(file_path) != os.path.abspath(dest_path):
                try:
                    import shutil
                    shutil.copy(file_path, dest_path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"No se pudo copiar: {e}")
                    return

            self.current_file_path = file_name
            self.lbl_file.setText(file_name)
            
            ext = file_name.split('.')[-1].lower()
            if ext in ['mp4', 'webm', 'mkv']:
                self.current_file_type = "video"
            elif ext in ['png', 'jpg', 'jpeg', 'gif']:
                self.current_file_type = "image"
            else:
                self.current_file_type = "audio"

    def save_reward(self):
        """Guarda los datos del formulario en triggers.json."""
        name = self.inp_name.text().strip().lower() # Guardamos en minúsculas para fácil validación
        
        if not name:
            QMessageBox.warning(self, "Aviso", "El nombre de la recompensa no puede estar vacío.")
            return

        # Actualizamos el diccionario en memoria
        self.triggers_data[name] = {
            "file": self.current_file_path,
            "type": self.current_file_type,
            "volume": 100, # Volumen por defecto
            "cost": self.inp_cost.value(),
            "color": self.inp_color.text(),
            "description": self.inp_desc.text(),
            "enabled": self.chk_enabled.isChecked()
        }

        # Guardamos en disco
        try:
            with open(self.triggers_file, "w", encoding="utf-8") as f:
                json.dump(self.triggers_data, f, indent=4, ensure_ascii=False)
            
            self.log(f"✅ Punto '{name}' guardado correctamente.")
            
            # Recargar combobox
            current_name = self.combo_rewards.currentText()
            self.load_triggers()
            
            # Volver a seleccionar el que acabamos de guardar
            index = self.combo_rewards.findData(name)
            if index >= 0:
                self.combo_rewards.setCurrentIndex(index)
                
        except Exception as e:
            self.log(f"❌ Error al guardar: {e}")

    def log(self, mensaje):
        """Escribe en la consola visual de esta pestaña."""
        self.consola.append(mensaje)
        self.consola.moveCursor(QTextCursor.MoveOperation.End)