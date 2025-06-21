import logging

from colorlog import ColoredFormatter

# Tạo formatter với màu sắc
formatter = ColoredFormatter(
    "%(log_color)s%(levelname)s:%(reset)s %(message)s",
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
)

# Handler mặc định đến stdout
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Gán handler vào root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[handler]
)
