# frontend/components/dialogs/__init__.py

from .base_dialogs import ModernBaseDialog, ModernConfirmDialog
from .update_dialog import UpdateDialog
from .alert_dialogs import DraggableAlertBox, VisualPositionerDialog, AlertConfigWizard
from .command_dialogs import CommandConfigWizard

__all__ = [
    "ModernBaseDialog",
    "ModernConfirmDialog",
    "UpdateDialog",
    "DraggableAlertBox",
    "VisualPositionerDialog",
    "AlertConfigWizard",
    "CommandConfigWizard"
]