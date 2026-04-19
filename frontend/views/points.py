import sys
import os
import urllib.parse
import requests
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QLineEdit, 
                             QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
                             QDialog, QSlider, QSpinBox, QDoubleSpinBox)
from PyQt6.QtCore import Qt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from backend.database import (cargar_sesion, guardar_vinculo_recompensa, obtener_vinculos_recompensas, 
                              eliminar_vinculo_recompensa, actualizar_ajustes_recompensa)
from backend.connection.kick_api import obtener_recompensas_kick
from frontend.theme import STYLES, Palette, get_sheet
from frontend.utils import get_icon_colored

# ==========================================
# EL MODAL FLOTANTE DE EDICIÓN
# ==========================================
class EditMediaModal(QDialog):
    def __init__(self, parent, data):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle(f"Ajustes: {data['name']}")
        self.setFixedSize(380, 420 if data['type'] in ['video', 'image'] else 200)
        self.setStyleSheet(get_sheet())
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # VOLUMEN (Para todos excepto imágenes)
        if self.data['type'] in ['video', 'audio']:
            layout.addWidget(QLabel("Volumen (%)", objectName="h4"))
            self.vol_spin = QSpinBox()
            self.vol_spin.setRange(0, 100)
            self.vol_spin.setValue(self.data['volume'])
            self.vol_spin.setStyleSheet(STYLES["spinbox_modern"])
            layout.addWidget(self.vol_spin)

        # POSICIÓN Y ESCALA (Solo Video e Imágenes)
        if self.data['type'] in ['video', 'image']:
            layout.addWidget(QLabel("Escala (Tamaño)", objectName="h4"))
            self.scale_spin = QDoubleSpinBox()
            self.scale_spin.setRange(0.1, 5.0)
            self.scale_spin.setSingleStep(0.1)
            self.scale_spin.setValue(self.data['scale'])
            self.scale_spin.setStyleSheet(STYLES["spinbox_modern"])
            layout.addWidget(self.scale_spin)

            layout.addWidget(QLabel("Posición en OBS", objectName="h4"))
            self.pos_combo = QComboBox()
            self.pos_combo.setStyleSheet(STYLES["combobox_modern"])
            self.pos_combo.addItems(["Centro de la pantalla", "Posición Aleatoria", "Coordenadas Exactas"])
            
            if self.data['is_random']: self.pos_combo.setCurrentIndex(1)
            elif self.data['pos_x'] == 0 and self.data['pos_y'] == 0: self.pos_combo.setCurrentIndex(0)
            else: self.pos_combo.setCurrentIndex(2)
            
            self.pos_combo.currentIndexChanged.connect(self.toggle_coords)
            layout.addWidget(self.pos_combo)

            # Contenedor de Coordenadas (X, Y)
            self.coords_container = QWidget()
            c_lay = QHBoxLayout(self.coords_container)
            c_lay.setContentsMargins(0,0,0,0)
            
            self.x_spin = QSpinBox(); self.x_spin.setRange(0, 3840)
            self.y_spin = QSpinBox(); self.y_spin.setRange(0, 2160)
            self.x_spin.setValue(self.data['pos_x']); self.y_spin.setValue(self.data['pos_y'])
            self.x_spin.setStyleSheet(STYLES["spinbox_modern"]); self.y_spin.setStyleSheet(STYLES["spinbox_modern"])
            
            c_lay.addWidget(QLabel("X:")); c_lay.addWidget(self.x_spin)
            c_lay.addWidget(QLabel("Y:")); c_lay.addWidget(self.y_spin)
            layout.addWidget(self.coords_container)
            
            self.toggle_coords() # Ocultar/Mostrar según el valor inicial

        layout.addStretch()

        # BOTONES
        btn_lay = QHBoxLayout()
        btn_save = QPushButton("Guardar Ajustes")
        btn_save.setStyleSheet(STYLES["btn_primary"])
        btn_save.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setStyleSheet(STYLES["btn_outlined"])
        btn_cancel.clicked.connect(self.reject)
        
        btn_lay.addWidget(btn_cancel); btn_lay.addWidget(btn_save)
        layout.addLayout(btn_lay)

    def toggle_coords(self):
        self.coords_container.setVisible(self.pos_combo.currentIndex() == 2)

    def get_results(self):
        """Extrae la información ingresada por el usuario."""
        is_random = False
        pos_x = 0; pos_y = 0

        if self.data['type'] in ['video', 'image']:
            idx = self.pos_combo.currentIndex()
            if idx == 1: is_random = True
            elif idx == 2:
                pos_x = self.x_spin.value()
                pos_y = self.y_spin.value()

        return {
            "volume": self.vol_spin.value() if self.data['type'] in ['video', 'audio'] else 100,
            "scale": self.scale_spin.value() if self.data['type'] in ['video', 'image'] else 1.0,
            "is_random": is_random,
            "pos_x": pos_x,
            "pos_y": pos_y
        }

# ==========================================
# LA VISTA PRINCIPAL
# ==========================================
class PointsView(QWidget):
    def __init__(self):
        super().__init__()
        self.sesion = cargar_sesion()
        self.init_ui()
        self.cargar_tabla()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        header_lbl = QLabel("Alertas de Puntos de Canal")
        header_lbl.setObjectName("h1")
        layout.addWidget(header_lbl)

        # --- TARJETA 1: VINCULAR RECOMPENSA ---
        link_card = QFrame()
        link_card.setStyleSheet(STYLES["card"])
        l_lay = QVBoxLayout(link_card)
        
        l_lay.addWidget(QLabel("1. Selecciona la recompensa de Kick:", objectName="h5"))
        row1 = QHBoxLayout()
        self.combo_rewards = QComboBox()
        self.combo_rewards.setStyleSheet(STYLES["combobox_modern"])
        self.btn_fetch = QPushButton(" Cargar de Kick")
        self.btn_fetch.setStyleSheet(STYLES["btn_outlined"])
        self.btn_fetch.clicked.connect(self.fetch_rewards)
        row1.addWidget(self.combo_rewards, 1); row1.addWidget(self.btn_fetch)
        l_lay.addLayout(row1)

        l_lay.addWidget(QLabel("2. Busca tu archivo multimedia en la PC:", objectName="h5"))
        row2 = QHBoxLayout()
        self.path_input = QLineEdit()
        self.path_input.setStyleSheet(STYLES["input_readonly"])
        self.path_input.setReadOnly(True)
        self.btn_browse = QPushButton(" Explorar...")
        self.btn_browse.setStyleSheet(STYLES["btn_outlined"])
        self.btn_browse.clicked.connect(self.browse_file)
        row2.addWidget(self.path_input, 1); row2.addWidget(self.btn_browse)
        l_lay.addLayout(row2)

        self.btn_save = QPushButton(" Añadir Alerta")
        self.btn_save.setStyleSheet(STYLES["btn_primary"])
        self.btn_save.clicked.connect(self.save_link)
        l_lay.addWidget(self.btn_save)
        layout.addWidget(link_card)

        # --- TARJETA 2: TABLA DE ALERTAS ACTIVAS ---
        table_card = QFrame()
        table_card.setStyleSheet(STYLES["card"])
        t_lay = QVBoxLayout(table_card)
        t_lay.addWidget(QLabel("Tus Alertas Configuradas:", objectName="h3"))

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Recompensa", "Archivo", "Acciones"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet(STYLES["table_clean"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers) 
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        
        # --- NUEVAS LÍNEAS ---
        # 1. Ocultar los números (cabecera vertical)
        self.table.verticalHeader().setVisible(False)
        
        # 2. Controlar la altura de las filas (45px es un buen tamaño)
        self.table.verticalHeader().setDefaultSectionSize(45)
        # ---------------------

        t_lay.addWidget(self.table)

        layout.addWidget(table_card)

    def fetch_rewards(self):
        if not self.sesion: return
        self.btn_fetch.setText(" Cargando...")
        self.btn_fetch.setEnabled(False)
        data = obtener_recompensas_kick(self.sesion['access_token'])
        self.combo_rewards.clear()
        if data:
            for rew in data: self.combo_rewards.addItem(rew.get("title", "Sin Título"), rew.get("id", ""))
        self.btn_fetch.setText(" Cargar de Kick")
        self.btn_fetch.setEnabled(True)

    def browse_file(self):
        file_filter = "Multimedia (*.mp4 *.webm *.mp3 *.wav *.png *.jpg *.gif)"
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Alerta", "", file_filter)
        if path: self.path_input.setText(path)

    def save_link(self):
        if self.combo_rewards.count() == 0 or not self.path_input.text(): return
        
        reward_name = self.combo_rewards.currentText()
        reward_id = self.combo_rewards.currentData()
        media_path = self.path_input.text()
        if not reward_id: return 
        
        ext = media_path.split('.')[-1].lower()
        if ext in ['mp4', 'webm']: media_type = 'video'
        elif ext in ['mp3', 'wav']: media_type = 'audio'
        else: media_type = 'image'

        guardar_vinculo_recompensa(reward_id, reward_name, media_type, media_path)
        self.path_input.clear()
        self.cargar_tabla()

    def cargar_tabla(self):
        self.table.setRowCount(0)
        vinculos = obtener_vinculos_recompensas()
        
        for v in vinculos:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Columna 0: Nombre con Icono Dinámico
            item_nombre = QTableWidgetItem(" " + v['name'])
            icono_name = "film.svg" if v['type'] == 'video' else ("music.svg" if v['type'] == 'audio' else "image.svg")
            item_nombre.setIcon(get_icon_colored(icono_name, Palette.White_N1, 18))
            self.table.setItem(row, 0, item_nombre)
            
            # Columna 1: Nombre de archivo
            self.table.setItem(row, 1, QTableWidgetItem(os.path.basename(v['path'])))
            
            # Columna 2: Botones de Acción
            actions_widget = QWidget()
            actions_widget.setStyleSheet("background-color: transparent;")
            boxTools = QHBoxLayout(actions_widget)
            boxTools.setContentsMargins(5, 2, 5, 2)
            boxTools.setSpacing(5)

            btn_test = QPushButton(); btn_test.setIcon(get_icon_colored("play.svg", Palette.status_info, 18)); btn_test.setStyleSheet(STYLES["btn_icon_ghost"]); btn_test.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit = QPushButton(); btn_edit.setIcon(get_icon_colored("edit.svg", Palette.NeonGreen_Main, 18)); btn_edit.setStyleSheet(STYLES["btn_icon_ghost"]); btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del = QPushButton();  btn_del.setIcon(get_icon_colored("trash.svg", Palette.status_error, 18));  btn_del.setStyleSheet(STYLES["btn_icon_ghost"]); btn_del.setCursor(Qt.CursorShape.PointingHandCursor)

            btn_test.clicked.connect(lambda checked, data=v: self.test_alert(data))
            btn_edit.clicked.connect(lambda checked, data=v: self.open_edit_modal(data))
            btn_del.clicked.connect(lambda checked, r_id=v['reward_id']: self.delete_link(r_id))

            boxTools.addWidget(btn_test); boxTools.addWidget(btn_edit); boxTools.addWidget(btn_del)
            self.table.setCellWidget(row, 2, actions_widget)

    def test_alert(self, data):
        """Simula la alerta enviándola al OBS Server local."""
        ruta_codificada = urllib.parse.quote(data['path'])
        url_media = f"http://127.0.0.1:8081/serve_media?path={ruta_codificada}"
        
        payload = {
            "action": "play_media",
            "type": data['type'],
            "url": url_media,
            "volume": data['volume'],
            "random": data['is_random'],
            "scale": data['scale'],
            "pos_x": data['pos_x'],
            "pos_y": data['pos_y']
        }
        try:
            requests.post("http://127.0.0.1:8081/api/trigger", json=payload)
        except Exception as e:
            print(f"Error probando alerta (Asegúrate que el OBS server esté prendido): {e}")

    def open_edit_modal(self, data):
        modal = EditMediaModal(self, data)
        if modal.exec() == QDialog.DialogCode.Accepted:
            nuevos_ajustes = modal.get_results()
            actualizar_ajustes_recompensa(
                data['reward_id'], 
                nuevos_ajustes['volume'], nuevos_ajustes['scale'], 
                nuevos_ajustes['is_random'], nuevos_ajustes['pos_x'], nuevos_ajustes['pos_y']
            )
            self.cargar_tabla()

    def delete_link(self, reward_id):
        eliminar_vinculo_recompensa(reward_id)
        self.cargar_tabla()