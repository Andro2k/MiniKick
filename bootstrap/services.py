# bootstrap\services.py\\

from backend.config import APP_VERSION
from bootstrap.translator import load_translator

UPDATE_REPO_OWNER = "Andro2k"
UPDATE_REPO_NAME = "MiniKick"
INSTANCE_PORT = 45678


class StartupServices:
    def create_database(self):
        from backend.database import DatabaseManager
        return DatabaseManager()

    def create_translator(self, db_manager):
        from backend.database import SQLiteSettingsStorage
        return load_translator(SQLiteSettingsStorage(db_manager))

    def create_container(self, db_manager, i18n):
        from backend.core.app_container_core import AppContainerCore
        return AppContainerCore(db_manager=db_manager, i18n=i18n)

    def create_instance_guard(self):
        from backend.services.system import SocketInstanceProvider
        return SocketInstanceProvider(port=INSTANCE_PORT)

    def create_updater(self):
        from backend.services.system import GithubUpdateProvider, UpdateManager, WindowsInstaller

        github = GithubUpdateProvider(repo_owner=UPDATE_REPO_OWNER, repo_name=UPDATE_REPO_NAME)
        return UpdateManager(
            current_version=APP_VERSION,
            checker=github,
            downloader=github,
            installer=WindowsInstaller(),
        )