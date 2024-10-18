from enum import Enum
from decouple import config
# Import all the models in the database

URL_DATABASE = config("DATABASE_URL")
REDIS_HOST = config("REDIS_HOST")
REDIS_PORT = config("REDIS_PORT")

ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")
ADMIN_EMAIL = config("ADMIN_EMAIL")

SUPERADMIN_USERNAME = config("SUPERADMIN_USERNAME")
SUPERADMIN_PASSWORD = config("SUPERADMIN_PASSWORD")
SUPERADMIN_EMAIL = config("SUPERADMIN_EMAIL")

class PermissionEnum(Enum):
    MONITOR_SYSTEM = 'GIÁM SÁT HỆ THỐNG'
    CONTROL_DEVICE = 'ĐIỀU KHIỂN THIẾT BỊ'
    REPORT = 'BÁO CÁO'
    MANAGE_USER = 'QUẢN LÝ USER'
    CONFIG_DEVICE = 'CẤU HÌNH THIẾT BỊ'
    VIEW_CHANGE_LOG = 'XEM NHẬT KÝ THAY ĐỔI'

    