from itsdangerous import TimedJSONWebSignatureSerializer
from django.conf import settings
from itsdangerous import BadData
def generate_secret_openid(openid):
    """对传入的openid进行加密处理,返回加密后的内容"""
    #settings.SECRET_KEY:加密使用的密钥
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY,
                                                 expires_in=600)

    # 待加密数据
    data = {'openid': openid}
    # 数据加密操作
    secret_openid = serializer.dumps(data).decode()

    # 返回加密后的openid
    return secret_openid

def check_secret_openid(secret_openid):
    """对加密的 openid 进行解密"""
    # 创建对象
    serializer = TimedJSONWebSignatureSerializer(settings.SECRET_KEY)

    try:
        # 进行解密操作
        data = serializer.loads(secret_openid)
    except BadData:
        # 解密出错，返回 None
        return None
    else:
        # 获取解密之后的 openid 并返回
        return data.get('openid')