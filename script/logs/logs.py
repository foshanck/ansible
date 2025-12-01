import logging
from datetime import datetime

# 配置统一的日志文件路径
LOG_FILE_PATH = "/enginization/logs/enginization.log"

def init_logger(logger_name):
    # 1. 创建记录器
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)  # 记录器处理DEBUG及以上的级别

    # 2. 创建处理器（控制台和文件）
    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler('app.log')

    # 为不同处理器设置不同级别
    console_handler.setLevel(logging.WARNING)  # 控制台只显示WARNING及以上
    file_handler.setLevel(logging.DEBUG)       # 文件记录所有DEBUG及以上的信息

    # 3. 创建格式器
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # 4. 将处理器添加到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

logger = init_logger("enginization")
