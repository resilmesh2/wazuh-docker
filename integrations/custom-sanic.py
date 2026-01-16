#!/usr/bin/env /python3
import json
import os
import sys

ERR_NO_REQUEST_MODULE = 1
ERR_FILE_NOT_FOUND = 6
ERR_INVALID_JSON = 7

try: 
    import requests
except ModuleNotFoundError:
    print("requests module not found. Please install it using 'pip install requests'")
    sys.exit(ERR_NO_REQUEST_MODULE)

# ossec.conf configuration:
# <integration>
#   <name>nats</name>
#   <hook_url>nats://resilmesh-ap-nats:4222</hook-url> <!-- Replace with your sanic server hook URL -->
#   <alert_format>json</alert_format>
# </integration>

# Global vars
debug_enabled = False
pwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
json_alert = {}

# Log
LOG_FILE = f'{pwd}/logs/integrations.log'

# Constants
ALERT_INDEX = 1
ERR_BAD_ARGUMENTS = 2
WEBHOOK_INDEX = 3

def main(args):
    global debug_enabled
    try:
        # Read arguments
        bad_arguments: bool = False
        if len(args) >= 4:
            msg = '{0} {1} {2} {3} {4}'.format(
                args[1], args[2], args[3], args[4] if len(sys.argv) > 4 else '', args[5] if len(sys.argv) > 5 else ''
            )
            debug_enabled = len(args) > 4 and args[4] == 'debug'
        else:
            msg = '# ERROR: Wrong arguments'
            bad_arguments = True

        # Logging the call
        with open(LOG_FILE, 'a') as f:
            f.write(msg + '\n')

        if bad_arguments:
            debug('# ERROR: Exiting, bad arguments. Inputted: %s' % args)
            sys.exit(ERR_BAD_ARGUMENTS)

        # Core function
        process_args(args)


    except Exception as e:
        debug(str(e))
        raise

def process_args(args) -> None:
    """This is the core function, creates a message with all valid fields
    and overwrite or add with the optional fields.

    Parameters
    ----------
    args : list[str]
        The argument list from main call
    """
    debug('# Running Sanic script')

    # Read args
    alert_file_location: str = args[ALERT_INDEX]
    webhook: str = args[WEBHOOK_INDEX]

    # Load alert. Parse JSON object.
    json_alert = get_json_alert(alert_file_location)
    debug(f"# Opening alert file at '{alert_file_location}' with '{json_alert}'")

    debug('# Generating message')
    msg: str = generate_msg(json_alert)

    # Check if alert is skipped
    if isinstance(msg, str):
        if not msg:
            return

    debug(f'# Sending message {msg} to Shuffle server')
    send_msg(msg, webhook)


def debug(msg: str) -> None:
    """Log the message in the log file with the timestamp, if debug flag
    is enabled.

    Parameters
    ----------
    msg : str
        The message to be logged.
    """
    if debug_enabled:
        print(msg)
        with open(LOG_FILE, 'a') as f:
            f.write(msg + '\n')

def generate_msg(alert: any) -> str:
    """Generate the JSON object with the message to be send.

    Parameters
    ----------
    alert : any
        JSON alert object.
    options: any
        JSON options object.

    Returns
    -------
    msg: str
        The JSON message to send
    """
    if alert["rule"].get("mitre") is None:
        return ''
    else:
        return json.dumps(alert)



def send_msg(msg: str, url: str) -> None:
    """Send the message to the API.

    Parameters
    ----------
    msg : str
        JSON message.
    url: str
        URL of the API.
    """
    headers = {'content-type': 'application/json', 'Accept-Charset': 'UTF-8'}
    res = requests.post(url, data=msg, headers=headers, timeout=10)
    debug('# Response received: %s' % res.json)

def get_json_alert(file_location: str) -> any:
    """Read JSON alert object from file.

    Parameters
    ----------
    file_location : str
        Path to the JSON file location.

    Returns
    -------
    dict: any
        The JSON object read it.

    Raises
    ------
    FileNotFoundError
        If no JSON file is found.
    JSONDecodeError
        If no valid JSON file are used
    """
    try:
        with open(file_location) as alert_file:
            return json.load(alert_file)
    except FileNotFoundError:
        debug("# JSON file for alert %s doesn't exist" % file_location)
        sys.exit(ERR_FILE_NOT_FOUND)
    except json.decoder.JSONDecodeError as e:
        debug('Failed getting JSON alert. Error: %s' % e)
        sys.exit(ERR_INVALID_JSON)

if __name__ == '__main__':
    main(sys.argv)
