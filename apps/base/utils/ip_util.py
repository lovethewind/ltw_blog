from starlette.requests import Request

from apps.base.utils.path_util import PathUtil
from apps.base.utils.xdb_search import XdbSearcher


class AddressInfo:

    def __init__(self, country: str = "", province: str = "", city: str = "", operator: str = ""):
        self.country = country
        self.province = province
        self.city = city
        self.operator = operator  # 运营商

    def get_simple_str(self):
        if self.country == "中国":
            return self.province
        return self.country

    def __str__(self):
        return f"{self.__class__.__name__}(country={self.country}, province={self.province})"


class IpUtil:
    _inited = False
    dbPath = PathUtil.get_resource_path("ip2region.xdb")
    cb = XdbSearcher.loadContentFromFile(dbfile=dbPath)
    # 2. 创建查询对象
    searcher = XdbSearcher(contentBuff=cb)

    @classmethod
    def get_ip_address(cls, request: Request):
        """

        :param request:
        :return:
        """
        unknown = "unknown"
        ip = request.headers.get("x-forwarded-for")
        if not ip or ip == unknown:
            ip = request.headers.get("Proxy-Client-IP")
        if not ip or ip == unknown:
            ip = request.headers.get("WL-Proxy-Client-IP")
        if not ip or ip == unknown:
            ip = request.headers.get("RemoteAddr")
        if not ip or ip == unknown:
            ip = request.client.host
        # 对于通过多个代理的情况，第一个IP为客户端真实IP,多个IP按照','分割
        if ip and len(ip) > 15:
            ip = ip.split(",")[0]
        return ip

    @classmethod
    def get_address_from_ip(cls, ip: str):
        """

        :param ip:
        :return:
        """
        region = cls.searcher.searchByIPStr(ip)
        region = region.replace("|0", "").replace("0|", "")
        split = region.split("|")
        address = AddressInfo()
        address.country = split[0]
        address.province = split[1]
        try:
            address.city = split[2]
            address.operator = split[3]
        except IndexError:
            pass
        return address.get_simple_str()

    @classmethod
    def get_address_from_request(cls, request):
        return cls.get_address_from_ip(cls.get_ip_address(request))


if __name__ == '__main__':
    print(IpUtil.get_address_from_ip("127.0.0.1"))
