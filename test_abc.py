from storage import DataStorage


# попытка создать абстрактный класс напрямую — Python должен запретить
try:
    s = DataStorage()
    print("FAIL: абстрактный класс создался, а не должен был")
except TypeError as e:
    print(f"OK: Python запретил создание → {e}")