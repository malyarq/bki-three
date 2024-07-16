import logging
import random
from logging.handlers import RotatingFileHandler
from flask import Flask, request, jsonify
from jsonformatter import JsonFormatter

app = Flask(__name__)


# Настройка логирования
def setup_logging():
    """
    Настройка логирования для приложения.
    Включает логирование в файл и вывод логов в консоль.
    """
    log_handler = RotatingFileHandler(
        "/opt/synapse/logs/log.log", maxBytes=1000000, backupCount=3
    )
    formatter = JsonFormatter(
        {
            "level": "levelname",
            "timestamp": "asctime",
            "msg": "message",
            "URL": "URL",
            "method": "method",
            "remoteAddr": "remoteAddr",
            "status": "status",
            "traceid": "traceid",
        }
    )
    log_handler.setFormatter(formatter)
    log_handler.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    app.logger.addHandler(log_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)


setup_logging()


# Функция для формирования заготовленного ответа
def get_prepared_response(data):
    """
    Возвращает заготовленный ответ на основе входящих данных.
    """
    return {
        "status": "sent",
        "bki": data["bki"],
        "request_id": "req123456",
        "report": {
            "credit_score": 750,
            "credit_history": [
                {
                    "date": "2022-01-01",
                    "type": "loan_issued",
                    "amount": 15000.0,
                    "status": "active",
                },
                {
                    "date": "2021-12-01",
                    "type": "payment_missed",
                    "amount": 500.0,
                    "status": "closed",
                },
            ],
        },
    }


# Функция для проверки входящих данных
def validate_request_data(data):
    """
    Проверяет наличие обязательных полей в запросе.
    Возвращает True и None, если все поля присутствуют, иначе False и сообщение об ошибке.
    """
    required_fields = ["bki", "client_id"]
    for field in required_fields:
        if field not in data:
            return False, f"Missing required field: {field}"
    return True, None


# Симуляция внутренней ошибки сервера
def simulate_server_error():
    """
    Вызывает исключение, имитирующее ошибку подключения к базе данных.
    """
    raise Exception("Database connection error")


@app.route("/credit_history", methods=["POST"])
def get_credit_history():
    """
    Обрабатывает POST-запрос для получения кредитной истории.
    """
    data = request.json

    # Логирование входящего запроса
    app.logger.info(
        "Received request",
        extra={
            "URL": request.path,
            "method": request.method,
            "remoteAddr": request.remote_addr,
            "status": "received",
            "traceid": request.headers.get("x-b3-traceId", "none"),
        },
    )

    # Проверка на наличие обязательных полей
    is_valid, error_msg = validate_request_data(data)
    if not is_valid:
        app.logger.error(
            error_msg,
            extra={
                "URL": request.path,
                "method": request.method,
                "remoteAddr": request.remote_addr,
                "status": "400",
                "traceid": request.headers.get("x-b3-traceId", "none"),
            },
        )
        return jsonify({"error": error_msg}), 400

    # Проверка на внутреннюю ошибку сервера
    if data.get("client_id") == "0" or random.random() < 0.05:
        # Допустим, для клиента "0" или в 5 процентах случаев возникает ошибка сервера
        try:
            simulate_server_error()
        except Exception as e:
            app.logger.error(
                str(e),
                extra={
                    "URL": request.path,
                    "method": request.method,
                    "remoteAddr": request.remote_addr,
                    "status": "500",
                    "traceid": request.headers.get("x-b3-traceId", "none"),
                },
            )
            return jsonify({"error": str(e)}), 500

    # Обработка запроса и формирование ответа
    response = get_prepared_response(data)
    return jsonify(response), 200


if name == "__main__":
    app.run(debug=True)
