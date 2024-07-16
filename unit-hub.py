import logging
import requests
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

# Словарь для хранения информации о сервисах
SERVICES = {
    "bki1": "http://mapping:8081/json",
    "bki2": "http://kafka-adapter:8080/",
    "bki3": "http://bki-three:8080/credit_history",
}


def get_combined_headers():
    """
    Получает заголовки для запроса, комбинируя переданные заголовки с новыми.
    """
    X_headers = {k: v for k, v in request.headers.items() if k.startswith("X-")}
    headers = {
        "schema": "root",
        "Content-Type": "application/json",
    }
    combined_headers = {**X_headers, **headers}

    # Логируем все хедеры
    app.logger.info(combined_headers)

    return combined_headers


def send_request(bki, data):
    """
    Отправляет запрос на соответствующий сервис в зависимости от bki.
    """
    combined_headers = get_combined_headers()
    url = SERVICES.get(bki)
    if not url:
        raise ValueError("Invalid bki value")

    app.logger.info(
        "Sending request",
        extra={
            "URL": url,
            "method": "POST",
            "remoteAddr": request.remote_addr,
            "status": "sending",
            "traceid": combined_headers.get("X-B3-Traceid", "none"),
        },
    )

    try:
        response = requests.post(url, json=data, headers=combined_headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        app.logger.error(
            str(e),
            extra={
                "URL": url,
                "method": "POST",
                "remoteAddr": request.remote_addr,
                "status": "500",
                "traceid": combined_headers.get("X-B3-Traceid", "none"),
            },
        )
        raise

    app.logger.info(
        "Received response",
        extra={
            "URL": url,
            "method": "POST",
            "remoteAddr": request.remote_addr,
            "status": response.status_code,
            "traceid": combined_headers.get("X-B3-Traceid", "none"),
        },
    )

    return response.json()


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


def log_request(status, msg, url=None, method=None, remote_addr=None, traceid=None):
    """
    Логирует запрос с дополнительной информацией.
    """
    app.logger.info(
        msg,
        extra={
            "URL": url or request.path,
            "method": method or request.method,
            "remoteAddr": remote_addr or request.remote_addr,
            "status": status,
            "traceid": traceid or request.headers.get("X-B3-Traceid", "none"),
        },
    )


@app.route("/", methods=["POST"])
def handle_request():
    """
    Обрабатывает POST-запрос и отправляет его на соответствующий сервис в зависимости от bki.
    """
    data = request.json

    # Логирование входящего запроса
    log_request("received", "Received request")

    # Проверка на наличие обязательных полей
    is_valid, error_msg = validate_request_data(data)
    if not is_valid:
        log_request("400", error_msg)
        return jsonify({"error": error_msg}), 400

    responses = {}
    if data["bki"] == "all":
        # Обработка запроса для всех сервисов
        for bki in SERVICES.keys():
            try:
                response = send_request(bki, data)
                responses[f"responseFrom{bki.capitalize()}"] = response
            except Exception as e:
                log_request("500", str(e))
                responses[f"responseFrom{bki.capitalize()}"] = {"error": str(e)}
        return jsonify(responses), 200
    else:
        # Обработка запроса для одного сервиса
        try:
            response = send_request(data["bki"], data)
            return jsonify(response), 200
        except Exception as e:
            log_request("500", str(e))
            return jsonify({"error": str(e)}), 500


if name == "__main__":
    app.run(debug=True)
