import os
import subprocess
import sys

def main():
    print("=========================================")
    print("      ファイル閲覧サーバー         ")
    print("=========================================")
    
    # このプログラムが置いてあるフォルダのパスを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    print(f"[公開中のフォルダ]: {current_dir}")
    print("[ポート番号]: 50007")
    print("\n※ 終了するには、この画面を閉じるか Ctrl+C を押してください。")
    print("-----------------------------------------")

    try:
        # Python標準のhttp.serverを、このフォルダをルートとして起動
        # 外部からの読み取りのみを許可し、コマンド実行や書き換えは不可能です
        subprocess.run(
            [sys.executable, "-m", "http.server", "50007"],
            cwd=current_dir
        )
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")

if __name__ == "__main__":
    main()