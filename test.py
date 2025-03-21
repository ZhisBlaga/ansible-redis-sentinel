import time
from redis import RedisError, sentinel
import sys
import ssl

ERROR_KEY_NOT_FOUND = "Key not found in redis"


class RedisDriver:
    def __init__(self, redis_config):
        self.service = redis_config["service_name"]
        self.__connect(redis_config)

    def __connect(self, redis_config):
        try:
            tls_params = {
                'ssl': True,  # Включаем TLS
                'ssl_cert_reqs': ssl.CERT_NONE,  # Требуем сертификат
                'ssl_ca_certs': '/data/git/zhis/infra/redis/ansible/files/ca.pem',  # Путь к CA-сертификату
                'ssl_version': ssl.PROTOCOL_TLSv1_1,
            }       

            self.connection = sentinel.Sentinel([(redis_config["master_host"],
                                                  redis_config["master_port"]),
                                                 (redis_config["slave_1_host"],
                                                  redis_config["slave_1_port"]),
                                                 (redis_config["slave_2_host"],
                                                  redis_config["slave_2_port"]),
                                                 (redis_config["slave_3_host"],
                                                  redis_config["slave_3_port"])],
                                                password=redis_config["password"],
                                                # min_other_sentinels=2,
                                                encoding="utf-8",
                                                decode_responses=True, **tls_params)

        except RedisError as err:
            error_str = "Error while connecting to redis : " + str(err)
            sys.exit(error_str)

    def set(self, key, value):
        key_str = str(key)
        val_str = str(value)
        try:
            master = self.connection.master_for(self.service)
            master.set(key_str, val_str)
            return {"success": True}
        except RedisError as err:
            error_str = "Error while connecting to redis : " + str(err)
            return {"success": False,
                    "error": error_str}

    def get(self, key):
        key_str = str(key)
        try:
            master = self.connection.master_for(self.service)
            value = master.get(key_str)
        except RedisError as err:
            error_str = "Error while retrieving value from redis : " + str(err)
            return {"success": False,
                    "error": error_str}

        if value is not None:
            return {"success": True,
                    "value": value}
        else:
            return {"success": False,
                    "error": ERROR_KEY_NOT_FOUND}

    def delete(self, key):
        key_str = str(key)
        try:
            master = self.connection.master_for(self.service)
            value = master.delete(key_str)
        except RedisError as err:
            error_str = "Error while deleting key from redis : " + str(err)
            return {"success": False,
                    "error": error_str}

        return {"success": True}


if __name__ == '__main__':
    print("*****************")
    redis_config = {"service_name": "mymaster",
                    "master_host": "redis-master",
                    "master_port": 26379,
                    "password": "123456",
                    "slave_1_host": "redis01.zhis.su",
                    "slave_1_port": 26379,
                    "slave_2_host": "redis01.zhis.su",
                    "slave_2_port": 26379,
                    "slave_3_host": "redis01.zhis.su",
                    "slave_3_port": 26379, }

    redis_driver = RedisDriver(redis_config)

    result = redis_driver.set("hello", "world")
    print(result)

    if result["success"]:
        result = redis_driver.get("hello")
        print(result)

    print("******** SLEEPING *********")
    time.sleep(120)

    print("******** AGAIN *********")
    result = redis_driver.set("hello2", "world2")
    print(result)

    if result["success"]:
        result = redis_driver.get("hello2")
        print(result)