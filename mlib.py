import time, os

def log(text:str):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f'[{now}] {text}')

def check_path(file_path):
    folder_path = os.path.dirname(file_path)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        log(f"Folder '{folder_path}' created.")

if __name__ == "__main__":
    check_path(os.path.join('test', 'ttt', 'aaa.txt'))
