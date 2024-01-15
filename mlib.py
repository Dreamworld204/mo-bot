import time

def log(text:str):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f'[{now}] {text}')

if __name__ == "__main__":
    log("test")
