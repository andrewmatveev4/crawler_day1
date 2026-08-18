from errors import classify_http_status, TransientError, PermanentError

# имитируем: какой класс даёт классификатор для разных статусов
cases = {
    404: PermanentError,
    403: PermanentError,
    401: PermanentError,
    503: TransientError,
    429: TransientError,
    500: TransientError,
}

print("Проверка классификатора (без сети):")
all_ok = True
for status, expected in cases.items():
    got = classify_http_status(status)
    ok = got is expected
    all_ok = all_ok and ok
    mark = "✅" if ok else "❌"
    print(f"  {mark} {status} → {got.__name__} (ждали {expected.__name__})")

print(f"\n{'ВСЁ ВЕРНО' if all_ok else 'ЕСТЬ ОШИБКИ'}")