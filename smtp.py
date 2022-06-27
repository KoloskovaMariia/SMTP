import base64
import socket
import ssl
import random
import re


class Doc:  # класс для документов
    def __init__(self, name, file, extension):
        self.name = name
        self.file = file
        self.extension = extension


class Image:  # класс для изображений
    def __init__(self, name, file, extension):
        self.name = name
        self.file = file
        self.extension = extension


host_addr = 'smtp.yandex.ru'  # используем хост Яндекса
port = 465
user_name = 'mar@ya.ru'  # если хотим использовать, всталяем сюда свою яндекс почту
password = '12345'  # а сюда пароль, если используем в приложении, то испольуем пароль для приложения
re_subject = re.compile("Subject: (.+?)\n")  # парсер конфига и темы
re_files = re.compile("Files: (.+?)")


def request(sock, req):  # обращение к smtp Яндекса
    sock.send((req + '\n').encode())
    recv_data = sock.recv(65535).decode()
    return recv_data


def authorization(client):  # авторизация благодаря паролю пользователя
    base64login = base64.b64encode(user_name.encode()).decode()
    base64password = base64.b64encode(password.encode()).decode()
    print(request(client, 'AUTH LOGIN'))
    print(request(client, base64login))
    print(request(client, base64password))


def start2(client, sender, receivers):
    print(request(client, f'MAIL FROM:{sender}@yandex.ru'))
    for receiver in receivers:  # кому отдавать письмо
        print(request(client, f"RCPT TO:{receiver}"))  # кому отдавать письмо
    print(request(client, 'DATA'))  # запрос данных


def letter_formation(sender, receivers, flag, subject):
    mail = ''
    mail += f"From: Me <{sender}@yandex.ru>\n"  # sender - это мы
    for receiver in receivers:  # кому отправлям
        mail += f"To: A A <{receiver}>\n"
    mail += "MIME-Version: 1.0\n"
    mail += f"Subject: {subject}\n"  # subject - тема письма, которую мы получам из конфига
    if flag:
        mail += "Content-Type: multipart/mixed;\n"
        bound = "----==--bound." + str(random.randint(0, 100000000))
        mail += f"    boundary=\"{bound}\"\n\n\n"
        return mail, bound
    return mail, None


def add_text(text, bound, flag):
    mail = ''
    if flag:
        mail += f"--{bound}\n"
    mail += "Content-Transfer-Encoding: 8bit\n"
    mail += "Content-Type: text/plain; charset=utf-8\n"
    mail += f"\n{text}\n"
    return mail


def add_document(doc, bound):
    mail = ''
    mail += f"--{bound}\n"
    mail += "Content-Disposition: attachment;\n"
    mail += f"\tfilename=\"{doc.name}\"\n"
    mail += "Content-Transfer-Encoding: base64\n"
    mail += f"Content-Type: application/{doc.extension};"
    mail += f"\tname=\"{doc.name}\"\n\n"
    mail += f"{doc.file}\n"
    return mail


def add_image(image, bound):
    mail = ""
    mail += f"--{bound}\n"
    mail += "Content-Disposition: attachment;\n"
    mail += f"\tfilename=\"{image.name}\"\n"
    mail += "Content-Transfer-Encoding: base64\n"
    mail += f"Content-Type: image/{image.extension};"
    mail += f"\tname=\"{image.name}\"\n\n"
    mail += f"{image.file}\n"
    return mail


def end_mail(bound, flag):
    mail = ""
    if flag:
        mail += f"--{bound}--\n"
    mail += "."
    return mail


def get_subject():
    try:
        with open("Config", "r", encoding="utf-8") as config:
            line = config.readlines()
            return re_subject.fullmatch(line[0]).group(1)
    except:
        return "default"


def get_receivers():
    try:
        with open("Receivers", "r") as config:
            return config.read().split('\n')
    except:
        return 'praktikauchebnaya@yandex.ru'


def get_text():
    try:
        with open("Message", "r", encoding="utf-8") as config:
            lines = config.readlines()
            text = ''
            for line in lines:
                textline = ''
                if line.count('.') == len(line):
                    textline += line + '.\n'
                else:
                    for i in range(len(line)):
                        if line[i] == '.':
                            textline += '.'
                            continue
                        elif i != 0:
                            textline += '.' + line[-i:]
                            break
                        else:
                            textline = line
                            break
                text += textline
            return text
    except:
        return 'default'


def get_files():
    try:
        with open("Config", "r", encoding="utf-8") as config:
            line = config.readlines()
            file_names = str(re_files.fullmatch(line[1]).group(1)).split('/')
            files = []
            for file_name in file_names:
                extension = file_name.split('.')[-1]
                if extension == 'png' or extension == 'jpg':
                    with open(f"files/{file_name}", "rb") as filer:
                        files.append(Image(file_name, base64.b64encode(
                            filer.read()).decode('utf-8'), extension))
                else:
                    with open(f"files/{file_name}", "rb") as filer:
                        files.append(Doc(file_name, base64.b64encode(
                            filer.read()).decode('utf-8'), extension))
            return files
    except:
        return []


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((host_addr, port))
        client = ssl.wrap_socket(client)
        print(client.recv(1024))
        print(request(client, 'EHLO Фамилия Имя'))
        authorization(client)  # авторизация клиента
        start2(client, user_name, get_receivers())  # запросили данные
        files = get_files()  # получили файлы из конфига
        flag = len(files) > 0  # формируем фаг, который нужен, чтобы понять, нужно ли нам делить на bound
        mail, bound = letter_formation(user_name, get_receivers(), flag, get_subject())  # формирует mail и наш bound
        mail += add_text(get_text(), bound, flag)  # боунд формируетстя случайным образом
        for file in files:
            if file is Image:
                mail += add_image(file, bound)
            else:
                mail += add_document(file, bound)
        mail += end_mail(bound, flag)
        print(request(client, mail))
        print(request(client, 'QUIT'))


if __name__ == '__main__':
    main()
