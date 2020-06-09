from django.core.files.storage import Storage
from fdfs_client.client import Fdfs_client, get_tracker_conf


class FDFSStorage(Storage):
    # fast dfs文件存储类
    def _open(self, name, mode='rb'):
        # 打开文件时使用
        pass

    def _save(self, name, content):
        # 保存文件时使用
        # name: 你选择上传文件的名字
        # content:包含你上传文件内容的File对象

        # 创建Fdfs_client对象
        trackers = get_tracker_conf('./utils/fdfs/client.conf')
        client = Fdfs_client(trackers=trackers)
        # 上传文件到fast dfs系统中
        res = client.upload_by_buffer(content.read())
        # 返回字典

        # if res.get('Status') != 'Upload successed':
        #     # 上传失败
        #     raise Exception('上传文件到fast dfs失败')
        # 获取返回的文件ID
        filename = res.get('Remote file_id')
        return filename.decode('utf8')

    def exists(self, name):
        # Django判断文件名是否可用
        return False

    def url(self, name):
        # 返回访问文件的url路径
        return 'http://192.168.1.104:8888/' + name
