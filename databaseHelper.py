import mysql.connector
from datetime import datetime, timedelta


class DatabaseHelper:
    def __init__(self):
        self.db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="backend_web_proj"
        )
        self.cursor = self.db.cursor()

    def create_table(self):
        # self.cursor.execute("CREATE DATABASE backed_project")
        # self.cursor.execute(
        #     "CREATE TABLE users ("
        #     "id int not null primary key auto_increment,"
        #     "created_at datetime,"
        #     "user_name varchar(100),"
        #     "password varchar(256)) auto_increment=1 "
        # )

        # self.cursor.execute(
        #     "CREATE TABLE urls ("
        #     "id int not null primary key auto_increment,"
        #     "user_id int,"
        #     "created_at datetime,"
        #     "url varchar(256),"
        #     "threshold int,"
        #     "failed_times int,"
        #     "foreign key (user_id) references users (id)) auto_increment=1 "
        # )

        # self.cursor.execute(
        #     "CREATE TABLE requests ("
        #     "id int not null primary key auto_increment,"
        #     "created_at datetime,"
        #     "url_id int,"
        #     "response int,"
        #     "foreign key (url_id) references urls (id)) auto_increment=1 "
        # )

        self.cursor.execute(
            "CREATE TABLE alerts ("
            "id int not null primary key auto_increment,"
            "created_at datetime,"
            "url_id int,"
            "alert varchar(256),"
            "foreign key (url_id) references urls (id)) auto_increment=1 "
        )

    def add_user(self, user_name, password):
        sql = f"INSERT INTO users (created_at, user_name, password) VALUES (%s, %s, %s)"
        val = (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), user_name, password)
        self.cursor.execute(sql, val)

        self.db.commit()

        print(self.cursor.rowcount, "record inserted in database.")
        id_inserted = self.cursor.lastrowid

        return id_inserted

    def insert_to_db(self, table_name, public_id, name, email, password):
        sql = f"INSERT INTO {table_name} (public_id, user_name, email, password) VALUES (%s, %s, %s, %s)"
        val = (public_id, name, email, password)
        self.cursor.execute(sql, val)

        self.db.commit()

        print(self.cursor.rowcount, "record inserted in database.")
        id_inserted = self.cursor.lastrowid

        return id_inserted

    def search_user(self, key, value):
        query = f"select * from users where {key} = '{value}'"
        self.cursor.execute(query)
        res = self.cursor.fetchone()
        if res:
            return {'id': res[0],
                    'created_at': res[1],
                    'user_name': res[2],
                    'password': res[3]}
        return None

    def search_all(self, table_name):
        query = f"select * from {table_name}"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def add_url(self, user_id, url, threshold):
        query = f"insert into urls (user_id, created_at, url, threshold, failed_times) " \
                f"values (%s, %s, %s, %s, %s)"
        values = (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url, threshold, 0)
        self.cursor.execute(query, values)

        self.db.commit()
        print(self.cursor.rowcount, "record inserted in database.")

    def search_user_urls(self, user_id):
        query = f"select * from urls where user_id = '{user_id}'"
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        urls = []
        for item in result:
            urls.append({
                'url_id': item[0],
                'created_at': item[2],
                'url': item[3],
                'threshold': item[4],
                'failed_times': item[5]
            })
        return urls

    def get_urls_data(self):
        query = f"select * from urls"
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        url_data = []
        for item in result:
            url_data.append({
                'id': item[0],
                'user_id': item[1],
                'created_at': item[2],
                'url': item[3],
                'threshold': item[4],
                'failed_times': item[5]
            })
        return url_data

    def update_failed_times(self, _id):
        query = f"update urls set failed_times = failed_times + 1 where id = {_id}"
        self.cursor.execute(query)
        self.db.commit()
        print(self.cursor.rowcount, "row updated in urls")

    def get_threshold_failed(self, _id):
        query = f"select threshold, failed_times from urls where id = {_id}"
        self.cursor.execute(query)
        res = self.cursor.fetchone()
        return res[0], res[1]

    def insert_to_requests(self, url_id, response):
        query = f"insert into requests (created_at, url_id, response) values (%s, %s, %s)"
        values = (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), url_id, response)
        self.cursor.execute(query, values)
        self.db.commit()
        print(self.cursor.rowcount, "record inserted into requests")

    def select_request_stats(self, url_id):
        query = f"select * from requests where url_id = '{url_id}'"
        self.cursor.execute(query)
        result = self.cursor.fetchall()
        stats = []
        for item in result:
            created_at = item[1]
            yesterday = datetime.strptime((datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S"),
                                          "%Y-%m-%d %H:%M:%S")
            now = datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
            if yesterday < created_at < now:
                stats.append({
                    'status_code': item[3],
                    'created_at': item[1]
                })
        return stats


if __name__ == '__main__':
    db = DatabaseHelper()
    # db.create_table()
    # db.insert_to_db('users', '123', 'ali', 'ali@com', '222')
    # print(db.search_user('sara@com'))
    # db.add_user('fatemeh', '1234')
    # db.add_url('1', 'time.ir', 5)
    # print(db.search_user_urls('3'))
    # db.get_threshold_failed('2')
