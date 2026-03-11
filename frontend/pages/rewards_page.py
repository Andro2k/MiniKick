# frontend/pages/rewards_page.py

import os
from PyQt6.QtWidgets import (QDoubleSpinBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QLineEdit, QSpinBox, QCheckBox, 
                             QFileDialog, QFormLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QFrame, QMessageBox, QApplication)
from PyQt6.QtGui import QTextCursor, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal, QThreadPool

from frontend.theme import STYLES, get_switch_style
from frontend.utils import get_icon, ThumbnailWorker

class RewardsPage(QWidget):
    request_kick_update = pyqtSignal(str, int, str, bool, str)

    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.kick_rewards_data = {}
        
        self.current_file_path = ""
        self.current_file_type = "audio"
        self.current_kick_id = ""
        
        # Pool de hilos para generar miniaturas de video sin lag
        self.threadpool = QThreadPool.globalInstance()
        
        self.init_ui()
        self.actualizar_tabla()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # --- INFO SUPERIOR (Con botón de copiar) ---
        info_frame = QFrame()
        info_frame.setStyleSheet("background-color: #121516; border-radius: 6px;")
        info_frame_layout = QHBoxLayout(info_frame)
        info_frame_layout.setContentsMargins(10, 10, 10, 10)
        
        lbl_link_icon = QLabel()
        lbl_link_icon.setPixmap(get_icon("link.svg").pixmap(18, 18))
        
        info_obs = QLabel("URL para OBS: <b style='color:#53fc18;'>http://127.0.0.1:8081</b> (Ancho 1920, Alto 1080)")
        info_obs.setTextFormat(Qt.TextFormat.RichText)
        info_obs.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        # NUEVO: Botón copiar URL
        self.btn_copy_url = QPushButton()
        self.btn_copy_url.setIcon(get_icon("copy.svg"))
        self.btn_copy_url.setToolTip("Copiar URL al portapapeles")
        self.btn_copy_url.setStyleSheet(STYLES["btn_icon_ghost"])
        self.btn_copy_url.clicked.connect(lambda: QApplication.clipboard().setText("http://127.0.0.1:8081"))
        
        info_frame_layout.addWidget(lbl_link_icon)
        info_frame_layout.addWidget(info_obs)
        info_frame_layout.addStretch()
        info_frame_layout.addWidget(self.btn_copy_url)
        
        main_layout.addWidget(info_frame)

        # --- CONTENEDOR DIVIDIDO ---
        split_layout = QHBoxLayout()
        
        # ==========================================
        # PANEL IZQUIERDO: TABLA
        # ==========================================
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        table_toolbar = QHBoxLayout()
        self.btn_refresh = QPushButton(" Actualizar Puntos")
        self.btn_refresh.setIcon(get_icon("refresh.svg"))
        self.btn_refresh.setStyleSheet(STYLES["btn_outlined"])
        self.btn_refresh.clicked.connect(self.actualizar_tabla)
        
        self.btn_new = QPushButton(" Crear Local")
        self.btn_new.setIcon(get_icon("add.svg"))
        self.btn_new.setStyleSheet(STYLES["btn_primary"])
        self.btn_new.clicked.connect(self.limpiar_formulario)
        
        table_toolbar.addWidget(self.btn_refresh)
        table_toolbar.addWidget(self.btn_new)
        table_toolbar.addStretch()
        left_layout.addLayout(table_toolbar)
        
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Origen", "Nombre del Punto", "Costo", "Estado"])
        self.table.setStyleSheet(STYLES["table_clean"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.itemSelectionChanged.connect(self.on_table_select)
        left_layout.addWidget(self.table)
        
        # ==========================================
        # PANEL DERECHO: MENÚ DE EDICIÓN
        # ==========================================
        right_panel = QFrame()
        right_panel.setStyleSheet(STYLES["card"])
        right_panel.setFixedWidth(360)
        right_layout = QVBoxLayout(right_panel)
        
        lbl_edit_title = QLabel("Detalles de Recompensa")
        lbl_edit_title.setStyleSheet(STYLES["label_title"])
        right_layout.addWidget(lbl_edit_title)
        
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 10)
        form_layout.setVerticalSpacing(12)
        
        self.inp_name = QLineEdit()
        self.inp_name.setStyleSheet(STYLES["input"])
        self.inp_name.setPlaceholderText("ID o Nombre exacto")
        
        self.inp_cost = QSpinBox()
        self.inp_cost.setStyleSheet(STYLES["spinbox_modern"])
        self.inp_cost.setRange(1, 9999999)
        
        self.inp_color = QLineEdit()
        self.inp_color.setStyleSheet(STYLES["input"])
        self.inp_color.setPlaceholderText("#53fc18")
        
        self.inp_desc = QLineEdit()
        self.inp_desc.setStyleSheet(STYLES["input"])
        self.inp_desc.setPlaceholderText("Descripción breve...")
        
        self.chk_enabled = QCheckBox("Activo en Kick/Local")
        self.chk_enabled.setStyleSheet(get_switch_style())
        self.chk_enabled.setChecked(True)
        
        form_layout.addRow("Nombre:", self.inp_name)
        form_layout.addRow("Costo:", self.inp_cost)
        form_layout.addRow("Color:", self.inp_color)
        form_layout.addRow("Descrip:", self.inp_desc)
        form_layout.addRow("", self.chk_enabled)
        
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #333;")
        right_layout.addLayout(form_layout)
        right_layout.addWidget(sep)
        
        # --- SECCIÓN MULTIMEDIA Y PREVISUALIZACIÓN ---
        overlay_layout = QFormLayout()
        overlay_layout.setContentsMargins(0, 10, 0, 0)
        
        lbl_overlay_title = QLabel("Acción en Pantalla (Overlay)")
        lbl_overlay_title.setStyleSheet("font-weight: bold; color: #8B8B8B; margin-bottom: 5px;")
        right_layout.addWidget(lbl_overlay_title)
        
        # Caja de Previsualización Visual (Miniatura)
        self.lbl_preview = QLabel()
        self.lbl_preview.setFixedSize(160, 90)
        self.lbl_preview.setStyleSheet("background-color: #1a1d1e; border-radius: 6px; border: 1px dashed #444;")
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Selector de Archivo
        file_layout = QHBoxLayout()
        self.lbl_file = QLineEdit()
        self.lbl_file.setStyleSheet(STYLES["input_readonly"])
        self.lbl_file.setReadOnly(True)
        self.lbl_file.setPlaceholderText("Sin archivo...")
        
        self.btn_file = QPushButton()
        self.btn_file.setIcon(get_icon("folder.svg"))
        self.btn_file.setStyleSheet(STYLES["btn_outlined"])
        self.btn_file.clicked.connect(self.select_file)
        
        file_layout.addWidget(self.lbl_file)
        file_layout.addWidget(self.btn_file)
        
        overlay_layout.addRow("", self.lbl_preview) # Agregamos la miniatura al formulario
        overlay_layout.addRow("Archivo:", file_layout)
        
        self.inp_scale = QDoubleSpinBox()
        self.inp_scale.setStyleSheet(STYLES["spinbox_modern"])
        self.inp_scale.setRange(0.1, 5.0)
        self.inp_scale.setSingleStep(0.1)
        self.inp_scale.setValue(1.0)
        overlay_layout.addRow("Escala:", self.inp_scale)
        
        pos_layout = QHBoxLayout()
        self.inp_x = QSpinBox()
        self.inp_x.setStyleSheet(STYLES["spinbox_modern"])
        self.inp_x.setRange(0, 4000)
        self.inp_x.setPrefix("X: ")
        
        self.inp_y = QSpinBox()
        self.inp_y.setStyleSheet(STYLES["spinbox_modern"])
        self.inp_y.setRange(0, 4000)
        self.inp_y.setPrefix("Y: ")
        
        pos_layout.addWidget(self.inp_x)
        pos_layout.addWidget(self.inp_y)
        overlay_layout.addRow("Posición:", pos_layout)
        
        self.chk_random = QCheckBox("Posición Aleatoria")
        self.chk_random.setStyleSheet(get_switch_style())
        overlay_layout.addRow("", self.chk_random)
        
        right_layout.addLayout(overlay_layout)
        right_layout.addStretch()
        
        action_layout = QHBoxLayout()
        self.btn_delete = QPushButton(" Borrar")
        self.btn_delete.setIcon(get_icon("trash.svg"))
        self.btn_delete.setStyleSheet(STYLES["btn_danger_outlined"])
        self.btn_delete.clicked.connect(self.delete_reward)
        
        self.btn_save = QPushButton(" Guardar")
        self.btn_save.setIcon(get_icon("save.svg"))
        self.btn_save.setStyleSheet(STYLES["btn_primary"])
        self.btn_save.clicked.connect(self.save_reward)
        
        action_layout.addWidget(self.btn_delete)
        action_layout.addWidget(self.btn_save)
        right_layout.addLayout(action_layout)
        
        split_layout.addWidget(left_panel, stretch=2)
        split_layout.addWidget(right_panel, stretch=1)
        main_layout.addLayout(split_layout, stretch=3)

        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setStyleSheet(STYLES["text_edit_console"])
        self.consola.setFixedHeight(120)
        main_layout.addWidget(self.consola)

        self.setLayout(main_layout)

    # --- LÓGICA DE DATOS Y PREVISUALIZACIÓN ---

    def cargar_recompensas_kick(self, lista_recompensas):
        self.kick_rewards_data.clear()
        for recompensa in lista_recompensas:
            titulo = recompensa.get("title", "").strip().lower()
            self.kick_rewards_data[titulo] = recompensa
        self.actualizar_tabla()

    def actualizar_tabla(self):
        self.table.setRowCount(0)
        triggers_db = self.db.get_all_triggers()
        todos_los_nombres = set(self.kick_rewards_data.keys()).union(set(triggers_db.keys()))
        
        for idx, titulo in enumerate(sorted(todos_los_nombres)):
            self.table.insertRow(idx)
            
            es_kick = titulo in self.kick_rewards_data
            datos_kick = self.kick_rewards_data.get(titulo, {})
            datos_db = triggers_db.get(titulo, {})
            
            # 1. Columna Origen (CON ICONOS SVG)
            item_origen = QTableWidgetItem("Kick" if es_kick else "Local")
            item_origen.setIcon(get_icon("kick.svg" if es_kick else "file.svg"))
            item_origen.setForeground(Qt.GlobalColor.green if es_kick else Qt.GlobalColor.cyan)
            
            nombre_real = datos_kick.get("title", titulo).title()
            item_nombre = QTableWidgetItem(nombre_real)
            item_nombre.setData(Qt.ItemDataRole.UserRole, titulo) 
            
            costo = datos_kick.get("cost", datos_db.get("cost", 100))
            item_costo = QTableWidgetItem(str(costo))
            
            activo = datos_kick.get("is_enabled", datos_db.get("enabled", True))
            item_estado = QTableWidgetItem("Activo" if activo else "Inactivo")
            if not activo: item_estado.setForeground(Qt.GlobalColor.darkGray)
            
            self.table.setItem(idx, 0, item_origen)
            self.table.setItem(idx, 1, item_nombre)
            self.table.setItem(idx, 2, item_costo)
            self.table.setItem(idx, 3, item_estado)

    def _actualizar_preview(self, path, ftype):
        """Valida si el archivo existe y muestra la miniatura o icono correspondiente."""
        if not path:
            self.lbl_file.setStyleSheet(STYLES["input_readonly"])
            self.lbl_file.setText("Sin archivo vinculado")
            self.lbl_preview.clear()
            return
            
        # Validar Ruta Rota (Rojo si no existe)
        if not os.path.exists(path):
            self.lbl_file.setStyleSheet("background: rgba(255, 69, 58, 0.1); color: #FF453A; border: 1px solid #FF453A; border-radius: 4px; padding: 4px;")
            self.lbl_file.setText(path)
            self.lbl_preview.setPixmap(get_icon("warning.svg").pixmap(40, 40))
            self.log(f"[WARN] El archivo no se encuentra en la ruta: {path}")
            return
            
        # Si existe, estilo normal
        self.lbl_file.setStyleSheet(STYLES["input_readonly"])
        self.lbl_file.setText(path)

        # Cargar Miniatura / Icono
        self.lbl_preview.clear()
        if ftype == "audio":
            self.lbl_preview.setPixmap(get_icon("audio.svg").pixmap(40, 40))
        elif ftype == "image":
            pixmap = QPixmap(path)
            self.lbl_preview.setPixmap(pixmap.scaled(160, 90, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        elif ftype == "video":
            # Icono temporal mientras se carga el frame del video
            self.lbl_preview.setPixmap(get_icon("video.svg").pixmap(40, 40)) 
            worker = ThumbnailWorker(path, 160)
            worker.signals.finished.connect(self._on_thumbnail_ready)
            self.threadpool.start(worker)

    def _on_thumbnail_ready(self, pixmap):
        """Se ejecuta cuando OpenCV termina de sacar el frame del video."""
        if pixmap and not pixmap.isNull():
            self.lbl_preview.setPixmap(pixmap)

    def on_table_select(self):
        selected_items = self.table.selectedItems()
        if not selected_items: return
        
        titulo_key = self.table.item(selected_items[0].row(), 1).data(Qt.ItemDataRole.UserRole)
        datos_kick = self.kick_rewards_data.get(titulo_key, {})
        datos_db = self.db.get_all_triggers().get(titulo_key, {})

        self.inp_name.setText(datos_kick.get("title", titulo_key))
        self.inp_name.setReadOnly(bool(datos_kick)) 
        
        self.inp_cost.setValue(datos_kick.get("cost", datos_db.get("cost", 100)))
        self.inp_desc.setText(datos_kick.get("description", datos_db.get("description", "")))
        self.inp_color.setText(datos_kick.get("color", datos_db.get("color", "")))
        self.chk_enabled.setChecked(datos_kick.get("is_enabled", datos_db.get("enabled", True)))
        
        self.current_file_path = datos_db.get("file", "")
        self.current_file_type = datos_db.get("type", "audio")
        self.current_kick_id = str(datos_kick.get("id", datos_db.get("kick_id", "")))
        
        # Actualizamos la previsualización visual
        self._actualizar_preview(self.current_file_path, self.current_file_type)
        
        self.inp_scale.setValue(datos_db.get("scale", 1.0))
        self.inp_x.setValue(datos_db.get("pos_x", 0))
        self.inp_y.setValue(datos_db.get("pos_y", 0))
        self.chk_random.setChecked(datos_db.get("random", False))

    def limpiar_formulario(self):
        self.table.clearSelection()
        self.inp_name.setReadOnly(False)
        self.inp_name.clear()
        self.inp_name.setFocus()
        self.inp_cost.setValue(100)
        self.inp_color.clear()
        self.inp_desc.clear()
        self.chk_enabled.setChecked(True)
        
        self.current_file_path = ""
        self.current_file_type = "audio"
        self.current_kick_id = ""
        self._actualizar_preview("", "")
        
        self.inp_scale.setValue(1.0)
        self.inp_x.setValue(0)
        self.inp_y.setValue(0)
        self.chk_random.setChecked(False)

    def select_file(self):
        file_filter = "Multimedia (*.mp3 *.wav *.ogg *.mp4 *.webm *.png *.jpg *.gif);;Audio (*.mp3 *.wav *.ogg);;Video (*.mp4 *.webm);;Imagen (*.png *.jpg *.gif)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo Multimedia", "", file_filter)
        
        if file_path:
            ruta_absoluta = os.path.normpath(file_path).replace("\\", "/")
            self.current_file_path = ruta_absoluta
            
            ext = ruta_absoluta.split('.')[-1].lower()
            if ext in ['mp4', 'webm', 'mkv']:
                self.current_file_type = "video"
            elif ext in ['png', 'jpg', 'jpeg', 'gif']:
                self.current_file_type = "image"
            else:
                self.current_file_type = "audio"
                
            self._actualizar_preview(self.current_file_path, self.current_file_type)

    def save_reward(self):
        name = self.inp_name.text().strip().lower()
        if not name:
            QMessageBox.warning(self, "Aviso", "El nombre de la recompensa no puede estar vacío.")
            return

        trigger_data = {
            "name": name,
            "file": self.current_file_path,
            "type": self.current_file_type,
            "volume": 100,
            "cost": self.inp_cost.value(),
            "color": self.inp_color.text(),
            "description": self.inp_desc.text(),
            "enabled": self.chk_enabled.isChecked(),
            "scale": self.inp_scale.value(),
            "pos_x": self.inp_x.value(),
            "pos_y": self.inp_y.value(),
            "random": self.chk_random.isChecked(),
            "kick_id": self.current_kick_id
        }

        self.db.save_trigger(trigger_data)
        self.log(f"[ÉXITO] Ajustes locales guardados para '{name}'.")
        self.actualizar_tabla()

        if self.current_kick_id:
            self.request_kick_update.emit(
                self.current_kick_id, 
                self.inp_cost.value(), 
                self.inp_desc.text(), 
                self.chk_enabled.isChecked(), 
                self.inp_color.text()
            )

    def delete_reward(self):
        name = self.inp_name.text().strip().lower()
        if not name: return
        
        reply = QMessageBox.question(self, "Confirmar", f"¿Desvincular y borrar configuración local de '{name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_trigger(name)
            self.log(f"[BORRADO] Configuración local borrada para '{name}'.")
            self.limpiar_formulario()
            self.actualizar_tabla()

    def log(self, mensaje):
        self.consola.append(mensaje)
        self.consola.moveCursor(QTextCursor.MoveOperation.End)