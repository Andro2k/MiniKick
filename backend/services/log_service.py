# backend/services/log_service.py

import os

class LogService:
    def __init__(self):
        app_data_dir = os.environ.get('LOCALAPPDATA', os.path.expanduser('~'))
        self.log_dir = os.path.join(app_data_dir, '.Minikick', 'logs')
        os.makedirs(self.log_dir, exist_ok=True)

    def get_log_files(self) -> list[str]:
        """Devuelve una lista ordenada de los archivos de log disponibles."""
        if not os.path.exists(self.log_dir):
            return []
        files = [f for f in os.listdir(self.log_dir) if f.startswith('minikick.log')]
        files.sort(reverse=True)
        return files

    def read_log_file(self, file_name: str) -> str:
        """Lee y devuelve el contenido de un archivo de log."""
        file_path = os.path.join(self.log_dir, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def delete_log_file(self, file_name: str):
        """Elimina un archivo de log específico."""
        file_path = os.path.join(self.log_dir, file_name)
        os.remove(file_path)