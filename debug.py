#!/usr/bin/env python3
import ansible_runner
import os
import time
import shutil
import logging
from datetime import datetime

# 配置统一的日志文件路径
LOG_FILE_PATH = "/enginization/logs/enginization.log"

# 1. 创建记录器
logger = logging.getLogger('my_app')
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


def ansible_logs_normalized(task_result):
    """
    将时间戳和任务结果以纯文本格式写入日志文件

    """
    try:
        # 提取关键信息
#        event_type = task_result.get('event_type', 'unknown')
        host = task_result.get('host', 'all')
        task_name = task_result.get('task_name', '').replace('|', '-')  # 避免与分隔符冲突
        status = task_result.get('status', '')

        # 构建详细信息部分
        details = []
        if 'changed' in task_result:
            details.append(f"changed:{task_result['changed']}")
        if 'return_code' in task_result:
            details.append(f"rc:{task_result['return_code']}")
        if 'message' in task_result:
            # 清理消息中的换行符和分隔符
            message = str(task_result['message']).replace('\n', ';').replace('|', '-')
            details.append(f"msg:{message[:100]}")  # 限制消息长度

        details_str = ';'.join(details)

        # 构建纯文本日志行
        log_line = f"exectue task [{task_name}] on [{host}] {status}, msg: [{details_str}]"
        logger.info(log_line)
        logger.info(log_line)
        return True
    except Exception as e:
        print(f"Errors happen while write logs: {str(e)}")
        return False


def event_handler(event_data):
    """
    事件处理器，将Ansible执行过程的关键信息记录到统一的日志文件
    使用纯文本格式，每行一个事件[1,4](@ref)
    """
    try:
        # 获取当前时间戳（使用更易读的格式）

        event_type = event_data.get('event', '')

        # 根据事件类型提取任务结果信息[3](@ref)
        task_result = {'event_type': event_type}

        # 处理任务执行结果事件[1](@ref)
        if event_type in ['runner_on_ok', 'runner_on_failed', 'runner_on_unreachable', 'runner_on_skipped']:
            # 提取主机和任务信息
            host = event_data.get('event_data', {}).get('host', 'unknown')
            task_name = event_data.get('event_data', {}).get('task', '')
            res_data = event_data.get('event_data', {}).get('res', {})

            # 构建简化的任务结果
            task_result.update({
                'host': host,
                'task_name': task_name,
                'status': event_type.replace('runner_on_', '')
            })

            # 添加关键的任务执行结果信息
            if 'changed' in res_data:
                task_result['changed'] = res_data['changed']
            if 'rc' in res_data:
                task_result['return_code'] = res_data['rc']
            if 'msg' in res_data:
                # 清理消息内容
                message = str(res_data['msg']).replace('\n', ';').replace('|', '-')
                task_result['message'] = message[:100]  # 限制消息长度
            # 写入纯文本格式日志
            ansible_logs_normalized(task_result)
        return True

    except Exception as e:
        print(f"处理事件时发生错误: {str(e)}")
        return False


def status_handler(status_data, runner_config):
    pass


def enginiztion():
    """健壮的运行器，包含完整错误处理"""
    logger.info("doing enginization......")

    max_retries = 0
    retry_delay = 5

    for attempt in range(max_retries + 1):
        try:
            # 记录开始执行的时间戳和结果
            start_result = {
                'event_type': 'execution_start',
                'host': 'all',
                'task_name': 'playbook_execution',
                'status': 'started'
            }
            ansible_logs_normalized(start_result)

            result = ansible_runner.run(
                private_data_dir='/enginization',
                playbook='/enginization/enginization.yml',
                inventory='/enginization/inventory/inventory.ini',
                status_handler=status_handler,
                event_handler=event_handler,  # 添加事件处理器
                quiet=False
            )
            end_result = {
                'event_type': 'execution_completed',
                'host': 'all',
                'task_name': 'playbook_execution',
                'status': result.status,
                'return_code': result.rc,
                'attempt': attempt + 1
            }
            ansible_logs_normalized(end_result)

            if result.status == 'successful':
                return result
            elif attempt < max_retries:
                print(f"执行失败，{retry_delay}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print("达到最大重试次数，放弃执行")
                return result

        except Exception as e:
            # 记录错误信息
            error_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            error_result = {
                'event_type': 'execution_error',
                'host': 'all',
                'task_name': 'playbook_execution',
                'status': 'error',
                'error_message': str(e)[:200],  # 限制错误消息长度
                'attempt': attempt + 1
            }
            ansible_logs_normalized(error_timestamp, error_result)

            if attempt < max_retries:
                print(f"发生错误: {str(e)}，{retry_delay}秒后重试...")
                time.sleep(retry_delay)
            else:
                print("达到最大错误重试次数")
                raise e

def before_engine():
    logger.info("preparation for before engine")

def after_engine():
    logger.info("preparation for after engine")

def main():

    try:
      before_engine()
    except Exception as e:
      print(f"Error happens: {str(e)}")
      print("Mark fault status here")

    try:
       enginiztion()
    except Exception as e:
#      print(f"Error happens: {str(e)}")
      print("Mark fault status here")

    try:
      after_engine()
    except Exception as e:
      print(f"Error happens: {str(e)}")
      print("Mark fault status here")


if __name__ == '__main__':
    main()

