# frontend\components\__init__.py
"""Paquete de componentes de UI.

Sin re-exports a este nivel: cada subpaquete (alerts, chat, dashboard, dialogs,
music, schedule, widgets) expone sus propios componentes. Importar siempre desde
el subpaquete, p. ej. ``from frontend.components.chat import BotMutePanel``.
"""
