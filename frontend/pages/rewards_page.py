# frontend/pages/rewards_page.py

import os
from PyQt6.QtWidgets import (QDoubleSpinBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, 
                             QPushButton, QLineEdit, QSpinBox, QCheckBox, 
                             QFileDialog, QFormLayout, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QAbstractItemView, QFrame, QMessageBox, QApplication)
from PyQt6.QtGui import QTextCursor, QPixmap, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QThreadPool, QSize

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
        
        self.threadpool = QThreadPool.globalInstance()
        
        self.init_ui()
        self.actualizar_tabla()

    def init_ui(self):
        # Fondo principal oscuro estilo dashboard
        self.setStyleSheet("background-color: #0E0E0E; color: #FFFFFF; font-family: 'Segoe UI', Ubuntu, sans-serif;")
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # --- INFO SUPERIOR (OBS URL) ---
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame { background-color: #161616; border-radius: 8px; border: 1px solid #252525; }
            QLabel { color: #A0A0A0; font-size: 13px; }
        """)
        info_frame_layout = QHBoxLayout(info_frame)
        info_frame_layout.setContentsMargins(15, 10, 15, 10)
        
        lbl_link_icon = QLabel()
        lbl_link_icon.setPixmap(get_icon("link.svg").pixmap(18, 18))
        
        info_obs = QLabel("URL para OBS: <b style='color:#53fc18;'>http://127.0.0.1:8081</b> <span style='color:#666;'>(1920x1080)</span>")
        info_obs.setTextFormat(Qt.TextFormat.RichText)
        info_obs.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_obs.setStyleSheet("border: none; background: transparent;")
        
        self.btn_copy_url = QPushButton(" Copiar")
        self.btn_copy_url.setIcon(get_icon("copy.svg"))
        self.btn_copy_url.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_copy_url.setStyleSheet("""
            QPushButton { background-color: transparent; color: #888; border: 1px solid #333; border-radius: 4px; padding: 4px 10px; }
            QPushButton:hover { background-color: #252525; color: #FFF; }
        """)
        self.btn_copy_url.clicked.connect(lambda: QApplication.clipboard().setText("http://127.0.0.1:8081"))
        
        info_frame_layout.addWidget(lbl_link_icon)
        info_frame_layout.addWidget(info_obs)
        info_frame_layout.addStretch()
        info_frame_layout.addWidget(self.btn_copy_url)
        
        main_layout.addWidget(info_frame)

        # --- CONTENEDOR DIVIDIDO ---
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)
        
        # ==========================================
        # PANEL IZQUIERDO: TABLA ESTILO DASHBOARD
        # ==========================================
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)
        
        # Toolbar de la tabla
        table_toolbar = QHBoxLayout()
        
        lbl_table_title = QLabel("Recompensas y Triggers")
        lbl_table_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #FFF; border: none; background: transparent;")
        
        self.btn_refresh = QPushButton()
        self.btn_refresh.setIcon(get_icon("refresh.svg"))
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.setStyleSheet("QPushButton { background: transparent; border: none; padding: 5px; } QPushButton:hover { background: #252525; border-radius: 4px; }")
        self.btn_refresh.clicked.connect(self.actualizar_tabla)
        
        self.btn_new = QPushButton(" + Nueva Local")
        self.btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_new.setStyleSheet("""
            QPushButton { background-color: #252525; color: #FFF; border: 1px solid #333; border-radius: 6px; padding: 6px 12px; font-weight: bold; }
            QPushButton:hover { background-color: #333; }
        """)
        self.btn_new.clicked.connect(self.limpiar_formulario)
        
        table_toolbar.addWidget(lbl_table_title)
        table_toolbar.addStretch()
        table_toolbar.addWidget(self.btn_refresh)
        table_toolbar.addWidget(self.btn_new)
        left_layout.addLayout(table_toolbar)
        
        # La Tabla
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Origen", "Descripción", "Costo", "Estado"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setIconSize(QSize(16, 16))
        
        # Estilos de la tabla para imitar el diseño
        self.table.setStyleSheet("""
            QTableWidget { background-color: transparent; border: none; color: #D0D0D0; }
            QTableWidget::item { border-bottom: 1px solid #1E1E1E; padding: 8px 5px; }
            QTableWidget::item:selected { background-color: #1A1D1E; color: #FFF; }
            QHeaderView::section { background-color: transparent; color: #777; font-weight: 600; font-size: 12px; border: none; border-bottom: 1px solid #252525; padding-bottom: 5px; text-align: left; }
        """)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        self.table.itemSelectionChanged.connect(self.on_table_select)
        left_layout.addWidget(self.table)
        
        # ==========================================
        # PANEL DERECHO: MENÚ DE EDICIÓN
        # ==========================================
        right_panel = QFrame()
        right_panel.setFixedWidth(340)
        right_panel.setStyleSheet("""
            QFrame { background-color: #121212; border-radius: 10px; border: 1px solid #1E1E1E; }
            QLabel { background: transparent; border: none; color: #A0A0A0; font-size: 12px; }
            QLineEdit { background-color: #1A1A1A; border: 1px solid #2A2A2A; border-radius: 6px; padding: 6px 10px; color: #FFF; font-size: 13px; }
            QLineEdit:focus { border: 1px solid #53fc18; }
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)
        
        lbl_edit_title = QLabel("Detalles de Recompensa")
        lbl_edit_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #FFF; margin-bottom: 5px;")
        right_layout.addWidget(lbl_edit_title)
        
        # Campos de texto simples
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("Ej. Sonido de victoria")
        
        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Descripción breve...")
        
        # Fila doble: Costo y Color
        cost_color_layout = QHBoxLayout()
        self.inp_cost = QSpinBox()
        self.inp_cost.setRange(1, 9999999)
        self.inp_cost.setPrefix("Pts: ")
        
        self.inp_color = QLineEdit()
        self.inp_color.setPlaceholderText("Color Hex (Ej. #53fc18)")
        
        cost_color_layout.addWidget(self.inp_cost)
        cost_color_layout.addWidget(self.inp_color)
        
        right_layout.addWidget(QLabel("Descripción"))
        right_layout.addWidget(self.inp_name)
        right_layout.addWidget(self.inp_desc)
        right_layout.addWidget(QLabel("Costo y Color"))
        right_layout.addLayout(cost_color_layout)
        
        self.chk_enabled = QCheckBox(" Activo")
        self.chk_enabled.setStyleSheet("QCheckBox { color: #FFF; background: transparent; border: none; font-size: 13px; }")
        self.chk_enabled.setChecked(True)
        right_layout.addWidget(self.chk_enabled)
        
        # Separador
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #252525; border: none;")
        right_layout.addWidget(sep)
        
        # --- SECCIÓN ATTACHMENTS (Drag & Drop Look) ---
        lbl_overlay_title = QLabel("Attachments (Overlay)")
        lbl_overlay_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #FFF;")
        right_layout.addWidget(lbl_overlay_title)
        
        # Caja estilo Drag & Drop
        self.box_file = QFrame()
        self.box_file.setCursor(Qt.CursorShape.PointingHandCursor)
        self.box_file.setStyleSheet("""
            QFrame { background-color: #161616; border: 1px dashed #444; border-radius: 8px; }
            QFrame:hover { border: 1px dashed #777; background-color: #1A1A1A; }
        """)
        box_file_layout = QVBoxLayout(self.box_file)
        box_file_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        box_file_layout.setContentsMargins(10, 15, 10, 15)
        
        self.lbl_preview = QLabel()
        self.lbl_preview.setFixedSize(140, 80)
        self.lbl_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_preview.setStyleSheet("background: transparent; border: none;")
        
        self.lbl_file_text = QLabel("Haz clic para buscar archivo\nJPG, PNG, MP4, MP3")
        self.lbl_file_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_file_text.setStyleSheet("color: #777; font-size: 11px; background: transparent; border: none;")
        
        box_file_layout.addWidget(self.lbl_preview, alignment=Qt.AlignmentFlag.AlignCenter)
        box_file_layout.addWidget(self.lbl_file_text)
        
        # Truco para que la caja entera funcione como botón
        self.box_file.mousePressEvent = lambda e: self.select_file()
        right_layout.addWidget(self.box_file)
        
        # Opciones de posición
        pos_layout = QHBoxLayout()
        self.inp_scale = QDoubleSpinBox()
        self.inp_scale.setRange(0.1, 5.0)
        self.inp_scale.setSingleStep(0.1)
        self.inp_scale.setValue(1.0)
        self.inp_scale.setPrefix("Esc: ")
        
        self.inp_x = QSpinBox()
        self.inp_x.setRange(0, 4000)
        self.inp_x.setPrefix("X: ")
        
        self.inp_y = QSpinBox()
        self.inp_y.setRange(0, 4000)
        self.inp_y.setPrefix("Y: ")
        
        pos_layout.addWidget(self.inp_scale)
        pos_layout.addWidget(self.inp_x)
        pos_layout.addWidget(self.inp_y)
        right_layout.addWidget(QLabel("Escala y Posición"))
        right_layout.addLayout(pos_layout)
        
        self.chk_random = QCheckBox(" Posición Aleatoria")
        self.chk_random.setStyleSheet("QCheckBox { color: #A0A0A0; background: transparent; border: none; }")
        right_layout.addWidget(self.chk_random)
        
        right_layout.addStretch()
        
        # Botones de Acción final
        action_layout = QHBoxLayout()
        self.btn_delete = QPushButton("Borrar")
        self.btn_delete.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_delete.setStyleSheet("""
            QPushButton { background-color: transparent; color: #FF453A; border: 1px solid #FF453A; border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: rgba(255, 69, 58, 0.1); }
        """)
        self.btn_delete.clicked.connect(self.delete_reward)
        
        self.btn_save = QPushButton("Guardar")
        self.btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save.setStyleSheet("""
            QPushButton { background-color: #EDEDED; color: #000; border: none; border-radius: 6px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #FFF; }
        """)
        self.btn_save.clicked.connect(self.save_reward)
        
        action_layout.addWidget(self.btn_delete)
        action_layout.addWidget(self.btn_save)
        right_layout.addLayout(action_layout)
        
        split_layout.addWidget(left_panel, stretch=1)
        split_layout.addWidget(right_panel)
        main_layout.addLayout(split_layout)

        # Consola minimizada/limpia
        self.consola = QTextEdit()
        self.consola.setReadOnly(True)
        self.consola.setFixedHeight(80)
        self.consola.setStyleSheet("""
            QTextEdit { background-color: #121212; border: 1px solid #1E1E1E; border-radius: 6px; color: #666; font-family: monospace; font-size: 11px; padding: 5px; }
        """)
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
            
            # 1. Columna Origen
            item_origen = QTableWidgetItem(" Kick" if es_kick else " Local")
            item_origen.setIcon(get_icon("kick.svg" if es_kick else "file.svg"))
            item_origen.setForeground(QColor("#53fc18") if es_kick else QColor("#A0A0A0"))
            
            nombre_real = datos_kick.get("title", titulo).title()
            item_nombre = QTableWidgetItem(nombre_real)
            item_nombre.setData(Qt.ItemDataRole.UserRole, titulo) 
            
            costo = datos_kick.get("cost", datos_db.get("cost", 100))
            item_costo = QTableWidgetItem(f"{costo} pts")
            item_costo.setForeground(QColor("#53fc18")) # Resaltamos el costo en verde
            
            activo = datos_kick.get("is_enabled", datos_db.get("enabled", True))
            item_estado = QTableWidgetItem("Activo" if activo else "Inactivo")
            item_estado.setForeground(QColor("#D0D0D0") if activo else QColor("#555555"))
            
            self.table.setItem(idx, 0, item_origen)
            self.table.setItem(idx, 1, item_nombre)
            self.table.setItem(idx, 2, item_costo)
            self.table.setItem(idx, 3, item_estado)

    def _actualizar_preview(self, path, ftype):
        if not path:
            self.lbl_file_text.setText("Haz clic para buscar archivo\nJPG, PNG, MP4, MP3")
            self.lbl_preview.clear()
            self.box_file.setStyleSheet("QFrame { background-color: #161616; border: 1px dashed #444; border-radius: 8px; } QFrame:hover { border: 1px dashed #777; background-color: #1A1A1A; }")
            return
            
        nombre_archivo = os.path.basename(path)
        
        if not os.path.exists(path):
            self.lbl_file_text.setText(f"Error: {nombre_archivo} no encontrado")
            self.lbl_file_text.setStyleSheet("color: #FF453A; font-size: 11px;")
            self.lbl_preview.setPixmap(get_icon("warning.svg").pixmap(40, 40))
            self.box_file.setStyleSheet("QFrame { background: rgba(255, 69, 58, 0.05); border: 1px dashed #FF453A; border-radius: 8px; }")
            return
            
        self.lbl_file_text.setText(nombre_archivo)
        self.lbl_file_text.setStyleSheet("color: #53fc18; font-size: 11px;")
        self.box_file.setStyleSheet("QFrame { background-color: #1A1A1A; border: 1px solid #333; border-radius: 8px; }")

        self.lbl_preview.clear()
        if ftype == "audio":
            self.lbl_preview.setPixmap(get_icon("audio.svg").pixmap(40, 40))
        elif ftype == "image":
            pixmap = QPixmap(path)
            self.lbl_preview.setPixmap(pixmap.scaled(140, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        elif ftype == "video":
            self.lbl_preview.setPixmap(get_icon("video.svg").pixmap(40, 40)) 
            worker = ThumbnailWorker(path, 140)
            worker.signals.finished.connect(self._on_thumbnail_ready)
            self.threadpool.start(worker)

    def _on_thumbnail_ready(self, pixmap):
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