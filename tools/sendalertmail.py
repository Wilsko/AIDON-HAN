import time
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
import platform

NEWLINE='\n'
CONFIG_FILE="/opt/hservice/alertmail.config"

def load_mail_config(filename=CONFIG_FILE):
    config = {}
    try:
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
#    print(config)    
            
        return config
    except:
        pass

    return None  
   
  


def send_alert(subject, body):
    cfg = load_mail_config()
#    print(cfg)
    if not cfg==None:
        enabled=cfg["enabled"]
        servername=cfg["server"]
        port=cfg["port"]
        from_addr=cfg["from_addr"]
        password=cfg["password"]
        to_addr=cfg["to_addr"]
        stamp=get_local_time()
        date_time = stamp.strftime("%d.%m.%Y  %H:%M:%S")
        host=platform.node()    
        message = host+NEWLINE+date_time+NEWLINE+body 
        #    message=body
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = from_addr
        msg["To"] = to_addr
        if enabled=="1":
            with smtplib.SMTP_SSL(servername, port, timeout=10) as server:
                server.set_debuglevel(1)
                server.login(from_addr, password)
                server.send_message(msg)
        else:
            for x in cfg:
                print(f"{x} = {cfg[x]}")
            print()
            print(f"Alertmail disabled in {CONFIG_FILE}")
            
    else:
        print(f"{CONFIG_FILE} missing")
       


def get_local_time():
    """
    Returns the current local time adjusted for the system's local timezone.
    """
    # Replace 'Europe/Helsinki' with your local timezone
    local_timezone = pytz.timezone("Europe/Helsinki")

    # Get current UTC time and convert to local time
    local_time = datetime.now(pytz.utc).astimezone(local_timezone)
    return local_time


send_alert("Test alert", "This is a test message from the HAN system.")
