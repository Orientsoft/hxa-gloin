from starlette.config import Config
import pytz

timezone = pytz.timezone('Asia/Shanghai')

config = Config("config")
project_name: str = config('project_name', cast=str, default='fastapi')
host: str = config('host', cast=str, default='0.0.0.0')
port: int = config('port', cast=int, default=8000)
debug: bool = config('debug', cast=bool, default=True)
version: str = config('version', cast=str, default='0.0.1')
allowed_hosts: str = config('allowed_hosts', cast=str, default='')
secret_key: str = config('secret_key', cast=str, default='welcome1')
api_key: str = config('api_key', cast=str, default='welcome1')
prefix_url: str = config('prefix_url', cast=str, default='/api')

# jwt
algorithm: str = config('algorithm', cast=str, default='HS256')
access_token_expire_minutes: int = config('access_token_expire_minutes', cast=int, default=60 * 24)
jwt_token_prefix: str = config('jwt_token_prefix', cast=str, default='Bearer')

# mongodb
database_url: str = config('database_url', cast=str,
                           default='mongodb://chromo:d2VsY29tZTEK@mongo:27017/chromoManager')
max_connections_count: int = config('max_connections_count', cast=int, default=10)
min_connections_count: int = config('min_connections_count', cast=int, default=10)
database_name: str = config('database_name', cast=str, default='chromoManager')
user_collection_name: str = config('user_collection_name', cast=str, default='user')
case_collection_name: str = config('case_collection_name', cast=str, default='case')
analysis_collection_name: str = config('analysis_collection_name', cast=str, default='analysis')
count_collection_name: str = config('count_collection_name', cast=str, default='count')
group_collection_name: str = config('group_collection_name', cast=str, default='group')
division_collection_name: str = config('division_collection_name', cast=str, default='division')

# redis
redis_host: str = config('redis_host', cast=str, default='127.0.0.1')
redis_port: int = config('redis_port', cast=int, default=6379)
redis_password: str = config('redis_password', cast=str, default=None)

# 导出路径
export_path: str = config('export_path', cast=str, default='D:\chromo-manager-export')
# 扫描路径
src_path: str = config('src_path', cast=str, default='/media/msd')
# 文件后缀
src_ext: str = config('src_ext', cast=str, default='MMI')
