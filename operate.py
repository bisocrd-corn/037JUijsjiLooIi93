import socket
import pickle
import struct
import cv2
import os

def start_remote_client():
    target_ip = input("操作先（相手）PCのIPアドレスを入力してください: ")
    PORT = 50007

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((target_ip, PORT))
        print("接続成功！画面内をクリックすると操作できます。")
        print("[L]キーを押すと、同じフォルダにある 'load.py' の中身を即座に実行させます。")
    except Exception as e:
        print(f"接続失敗: {e}")
        return

    def mouse_callback(event, x, y, flags, param):
        cmd = None
        if event == cv2.EVENT_LBUTTONDOWN:
            cmd = {'type': 'click', 'x': x, 'y': y, 'button': 'left'}
        elif event == cv2.EVENT_RBUTTONDOWN:
            cmd = {'type': 'click', 'x': x, 'y': y, 'button': 'right'}
        elif event == cv2.EVENT_MOUSEMOVE and (flags & cv2.EVENT_FLAG_LBUTTON):
            cmd = {'type': 'move', 'x': x, 'y': y}
            
        if cmd:
            try:
                cmd_data = pickle.dumps(cmd)
                client_socket.sendall(struct.pack(">L", len(cmd_data)) + cmd_data)
            except: pass

    cv2.namedWindow('Remote View')
    cv2.setMouseCallback('Remote View', mouse_callback)

    data = b""
    payload_size = struct.calcsize(">L")

    try:
        while True:
            while len(data) < payload_size:
                packet = client_socket.recv(4096)
                if not packet: break
                data += packet
            if len(data) < payload_size: break
            
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack(">L", packed_msg_size)
            
            while len(data) < msg_size:
                packet = client_socket.recv(4096)
                if not packet: break
                data += packet
                
            frame_data = data[:msg_size]
            data = data[msg_size:]
            
            frame = pickle.loads(frame_data)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            cv2.imshow('Remote View', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key != 255:
                char = chr(key)
                
                # 【新機能】「L」キーが押されたら、load.pyファイルを読み込んで送信
                if char.lower() == 'l':
                    if os.path.exists("load.py"):
                        with open("load.py", "r", encoding="utf-8") as f:
                            full_code = f.read()
                        
                        if full_code.strip():
                            cmd = {'type': 'code', 'text': full_code}
                            cmd_data = pickle.dumps(cmd)
                            client_socket.sendall(struct.pack(">L", len(cmd_data)) + cmd_data)
                            print("➔ 'load.py' の中身を送信・実行しました！")
                    else:
                        print("➔ エラー: 同じフォルダに 'load.py' が見つかりません。")
                else:
                    # 通常のキー入力
                    cmd = {'type': 'key', 'key': char}
                    cmd_data = pickle.dumps(cmd)
                    client_socket.sendall(struct.pack(">L", len(cmd_data)) + cmd_data)
                
    except Exception as e:
        print(f"切断されました: {e}")
    finally:
        cv2.destroyAllWindows()
        client_socket.close()

if __name__ == "__main__":
    start_remote_client()
