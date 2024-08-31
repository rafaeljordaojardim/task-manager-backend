class RunConfig:

    MONGO_HOST = 'mongo'
    MONGO_PORT = 27017
    MONGO_DBNAME = 'my_database'
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DBNAME}"

class TestConfig:

    MONGO_HOST = '127.0.0.1'
    MONGO_PORT = 27019
    MONGO_DBNAME = 'my_database_test_1'
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DBNAME}"
    TESTING = True
    