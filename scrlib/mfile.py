from datetime import datetime

import scrlib.mlib as lib
import os

class MFile:
    def __init__(self, config) -> None:
        self.config = config
        self.savepath = os.path.join("static", 'cloudfolder' in config and config['cloudfolder'] or 'file') + os.path.sep
        lib.check_path(self.savepath)
    def savefile(self, file, username):
        nownum, nowsize = self.getUsage(username)
        num_limit = self.config['cloud']['num_limit'] or 10
        capacity = self.config['cloud']['capacity'] or 1024 * 1024 * 1024

        filecontent = file.read()
        filesize = len(filecontent)
        nowsize += filesize
        if nownum + 1 > num_limit:
            return {'error': f'Saved files number over limit: {num_limit}'}
        if nowsize > capacity:
            return {'error': 'Saved files size over limit'}
        # 检查文件类型是否允许
        if self.allowed_file(file):
            fullpath = os.path.join(self.savepath, username, file.filename)
            lib.check_path(fullpath)
            #保存filecontent
            with open(fullpath, 'wb') as f:
                f.write(filecontent)
                return None
        else:
            return {'error': f'File: {file.filename} not allowed'}
    def allowed_file(self, file):
        if file.filename == '':
            return False
        return True
        
    def deletefile(self, filename, username):
        fullpath = os.path.join(self.savepath, username, filename)
        if os.path.exists(fullpath):
            try:
                os.remove(fullpath)
                return True
            except Exception as e:
                lib.log(f"An error occurred while deleting the file: {e}")
                return False
        else:
            return False
        
    def getUsage(self, username):
        abspath = os.path.join(self.savepath, username) + os.path.sep
        lib.check_path(abspath)
        lst = os.listdir(abspath)
        totalsize = 0
        for file in lst:
            fullpath = os.path.join(abspath, file)
            filesize = os.path.getsize(fullpath)
            totalsize += filesize
        return len(lst), totalsize
    def getFilelist(self, username):
        abspath = os.path.join(self.savepath, username) + os.path.sep
        lib.check_path(abspath)
        lst = os.listdir(abspath)
        filelist = []
        for file in lst:
            fullpath = os.path.join(abspath, file)
            filesize = os.path.getsize(fullpath)
            filetime = datetime.fromtimestamp( os.path.getmtime(fullpath) ).strftime("%Y-%m-%d %H:%M:%S")
            filelist.append({'name': file, 'path': fullpath, 'size': self.formatFileSize(filesize), 'time': filetime})
        return filelist
    def formatFileSize(self, file_size):
        if file_size >= 2**30:
            return f"{file_size / 2**30:.2f} GB"
        elif file_size >= 2**20:
            return f"{file_size / 2**20:.2f} MB"
        elif file_size >= 2**10:
            return f"{file_size / 2**10:.2f} KB"
        else:
            return f"{file_size} Bytes"
