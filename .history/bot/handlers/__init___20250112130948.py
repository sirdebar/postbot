# handlers/__init__.py
from aiogram import Dispatcher
from .admin_handlers import register_admin_handlers
from .user_handlers import register_user_handlers
from .search_handlers import register_search_handlers
from .misc_handlers import register_misc_handlers

def setup_handlers(dp: Dispatcher, redis_instance):
    """
    Регистрирует все обработчики в диспетчере.
    """
    register_admin_handlers(dp)
    register_user_handlers(dp)
    register_search_handlers(dp)
    register_misc_handlers(dp, redis_instance)