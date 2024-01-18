import time, os

def log(text:str, *args):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    strArgs = "\t" + "\t".join(map(str, args))
    print(f'[{now}] {text}{strArgs}')

def check_path(file_path):
    folder_path = os.path.dirname(file_path)

    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        log(f"Folder '{folder_path}' created.")

if __name__ == "__main__":
    check_path(os.path.join('test', 'ttt', 'aaa.txt'))
