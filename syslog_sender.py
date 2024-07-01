import json
import logging.handlers
import os
import socket

hostname = socket.gethostname()
program_name = 'netmon'

# Set the process id
process_id = os.getpid()

# Configure logging
logger = logging.getLogger('my_logger')
logger.setLevel(logging.INFO)

# Create a file handler
log_file = '/var/ossec/logs/opnsense_syslog.log'
handler = logging.FileHandler(log_file)

# Customize the syslog message format to RFC 3164
formatter = logging.Formatter(
    f'%(asctime)s {hostname} {program_name}[{process_id}]: %(message)s', datefmt='%b %d %H:%M:%S', style='%'
)
handler.setFormatter(formatter)
logger.addHandler(handler)


def send_syslog_json_message(content: dict):
    """
    Send a syslog message in JSON format
    :param content: dict
    """
    message = {
        "version": "2",
        "netflow_source": "opnsense insight scripts, parse_flow.py",
        "content": content
    }

    # message.update(content)

    logger.info(json.dumps(message))


if __name__ == '__main__':
    send_syslog_json_message({
        "message": "This is a test message",
    })

