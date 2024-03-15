import scrlib.mlib as lib
import os

class MFile:
    def __init__(self, config) -> None:
        self.config = config
        self.savepath = os.path.join("static", 'cloudfolder' in config and config['cloudfolder'] or 'file') + os.path.sep
        lib.check_path(self.savepath)
    def savefile(self, file):
        # 检查文件类型是否允许
        if file and self.allowed_file(file):
            # 保存文件到服务器
            file.save(os.path.join(self.savepath, file.filename))
            return True
        else:
            return False
    def allowed_file(self, file):
        return True
