def load_manual(file_path="data/manual.txt"):
    """
    Загружает содержимое файла методички.
    :param file_path: Путь к файлу (по умолчанию data/manual.txt)
    :return: Строка с содержимым файла
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            manual_content = file.read()
        return manual_content
    except FileNotFoundError:
        print(f"Ошибка: Файл {file_path} не найден.")
        return ""
    except Exception as e:
        print(f"Ошибка при загрузке файла: {e}")
        return ""

if __name__ == "__main__":
    manual = load_manual()
    print("Методичка загружена. Размер:", len(manual), "символов")