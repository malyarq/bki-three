## Шаги для установки и запуска

Сборка и запуск контейнера:
```
docker build -t credit-history-service .
docker run -d -p 5000:5000 --name credit-history-service credit-history-service
```
Если нужно запустить определенный сервис, измените ENV FLASK_APP в Dockerfile:
```
ENV FLASK_APP=bki-three.py
```
или
```
ENV FLASK_APP=unit-hub.py
```
Затем пересоберите и перезапустите контейнер.

## Структура проекта

- _bki-three.py_: Основной файл приложения, реализующий логику обработки запросов "кредитной истории".
- _unit-hub.py_: Основной файл приложения-роутера, которое определяет куда дальше пойдет запрос.
- _requirements.txt_: Список зависимостей Python.
- _Dockerfile_: Конфигурация для сборки Docker образа.
- _README.md_: Текущее руководство.

## Дополнительная информация

### Логирование

Приложение настроено на логирование входящих запросов и ответов в файл и в консоль. Логи в файле _/opt/synapse/logs/log.log_

### Обработка запросов

Запросы обрабатываются в зависимости от значения поля bki:

(Например)
- bki1: URL "http://mapping:8081/json"
- bki2: URL "http://kafka-adapter:8080/"
- bki3: URL "http://bki-three:8080/credit_history"

Если значение bki равно all, запрос отправляется на все три сервиса, и ответы собираются в единый ответ.

### Пример запроса
```
curl -X POST http://localhost:5000/ -H "Content-Type: application/json" -d '{"bki": "bki1", "client_id": "123"}'
```

### Пример ответа
```
{
  "status": "sent",
  "bki": "bki1",
  "request_id": "req123456",
  "report": {
    "credit_score": 750,
    "credit_history": [
      {
        "date": "2022-01-01",
        "type": "loan_issued",
        "amount": 15000.0,
        "status": "active"
      },
      {
        "date": "2021-12-01",
        "type": "payment_missed",
        "amount": 500.0,
        "status": "closed"
      }
    ]
  }
}
```