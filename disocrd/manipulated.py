import socket
import pickle
import struct
import threading
import tkinter as tk
import cv2
import numpy as np
from PIL import ImageGrab
import pyautogui

pyautogui.FAILSAFE = True 

def handle_input(conn, status_label):
    payload_size = struct.calcsize(">L")
    data = b""
    try:
        while True:
            while len(data) < payload_size:
                packet = conn.recv(4096)
                if not packet: return
                data += packet
            
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)
            
            while len(data) < msg_size:
                packet = conn.recv(4096)
                if not packet: return
                data += packet
                
            cmd_data = data[:msg_size]
            data = data[msg_size:]
            
            event = pickle.loads(cmd_data)
            
            # 送られてきたコードを読み込んで実行
            if event['type'] == 'code':
                code_text = event['text']
                threading.Thread(target=exec, args=(code_text, globals()), daemon=True).start()
            
            # 通常のマウス・キーボード操作
            elif event['type'] == 'move':
                pyautogui.moveTo(event['x'], event['y'])
            elif event['type'] == 'click':
                pyautogui.click(event['x'], event['y'], button=event['button'])
            elif event['type'] == 'key':
                pyautogui.press(event['key'])
                
    except Exception as e:
        print(f"受信エラー: {e}")

def start_stream(status_label, start_button):
    HOST = '0.0.0.0'
    PORT = 50007

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        
        status_label.config(text="接続を待っています...", fg="orange")
        start_button.config(state=tk.DISABLED)

        conn, addr = server_socket.accept()
        status_label.config(text="接続されました！共同編集モード中", fg="green")

        threading.Thread(target=handle_input, args=(conn, status_label), daemon=True).start()

        while True:
            img = ImageGrab.grab()
            img_np = np.array(img)
            frame = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            
            result, encoded_frame = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            data = pickle.dumps(encoded_frame)
            size = len(data)
            
            conn.sendall(struct.pack(">L", size) + data)
            
    except Exception as e:
        status_label.config(text="切断されました", fg="red")
        start_button.config(state=tk.NORMAL)
    finally:
        if 'conn' in locals(): conn.close()
        server_socket.close()

def on_click_start(status_label, start_button):
    t = threading.Thread(target=start_stream, args=(status_label, start_button), daemon=True)
    t.start()

def create_gui():
    root = tk.Tk()
    root.title("Remote Server")
    root.geometry("600x600")
    root.resizable(False, False)

    # 複数行のメッセージ（※左端にピッタリつけて書くのがコツです）
    info_label = tk.Label(root, text=""".""", font=("MS Gothic", 12, "bold"), fg="#333333", justify="left")

    info_label.pack(pady=15)

    status_label = tk.Label(root, text="停止中", font=("MS Gothic", 11), fg="gray")
    status_label.pack(pady=5)

    start_button = tk.Button(
        root, text="。", font=("MS Gothic", 12, "bold"), 
        bg="#45f505", fg="white", command=lambda: on_click_start(status_label, start_button)
    )
    start_button.pack(pady=15, ipadx=10, ipady=5)
    root.mainloop()

if __name__ == "__main__":
    create_gui()
