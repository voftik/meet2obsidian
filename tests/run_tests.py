#!/usr/bin/env python3
"""
Скрипт для запуска тестов.
Добавляет родительскую директорию в путь Python для правильного импорта модулей.

Использование:
    ./run_tests.py                    # Запустить все модульные тесты
    ./run_tests.py --integration      # Запустить модульные и интеграционные тесты
    ./run_tests.py --component name   # Запустить тесты для конкретного компонента
    ./run_tests.py --coverage         # Запустить тесты с анализом покрытия кода
    ./run_tests.py path/to/test.py    # Запустить конкретный тест
"""

import os
import sys
import argparse
import pytest
from typing import List, Dict

# Добавляем директорию проекта в путь Python
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Карта компонентов для удобного запуска соответствующих тестов
COMPONENT_MAP: Dict[str, List[str]] = {
    "launchagent": ["unit/test_launchagent.py", "unit/test_application_manager_launchagent.py",
                    "integration/test_launchagent_integration.py"],
    "monitor": ["unit/test_application_manager.py", "integration/test_file_monitor_integration.py"],
    "config": ["unit/test_config.py"],
    "cli": ["unit/test_cli.py"],
    "security": ["unit/test_security.py", "integration/test_security_integration.py"],
    "logging": ["unit/test_logging.py"]
}


def parse_args():
    """
    Парсинг аргументов командной строки.
    """
    parser = argparse.ArgumentParser(description='Запуск тестов meet2obsidian')

    # Выбор тестов
    group = parser.add_argument_group('Выбор тестов')
    group.add_argument('--unit', action='store_true', help='Запустить только модульные тесты')
    group.add_argument('--integration', action='store_true', help='Запустить все тесты, включая интеграционные')
    group.add_argument('--component', type=str, help='Запустить тесты для компонента: ' +
                      ', '.join(COMPONENT_MAP.keys()))
    group.add_argument('test_paths', nargs='*', help='Пути к файлам тестов для запуска')

    # Опции анализа покрытия
    coverage = parser.add_argument_group('Анализ покрытия кода')
    coverage.add_argument('--coverage', '-c', action='store_true', help='Включить анализ покрытия кода')
    coverage.add_argument('--html', action='store_true', help='Создать HTML-отчет о покрытии')
    coverage.add_argument('--fail-under', type=int, default=0,
                         help='Установить минимальный процент покрытия для прохождения теста')

    # Дополнительные опции
    extra = parser.add_argument_group('Дополнительные опции')
    extra.add_argument('--verbose', '-v', action='count', default=1,
                      help='Увеличить детализацию вывода (можно указать несколько раз, например -vv)')
    extra.add_argument('--failfast', '-f', action='store_true', help='Остановить тесты при первой ошибке')
    extra.add_argument('--list', '-l', action='store_true', help='Вывести список тестов без запуска')

    return parser.parse_args()


def get_test_paths(args):
    """
    Определяет, какие тесты нужно запустить на основе переданных аргументов.
    """
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # Если указаны конкретные пути, используем их
    if args.test_paths:
        return args.test_paths

    # Если указан компонент, запускаем соответствующие тесты
    if args.component:
        component = args.component.lower()
        if component in COMPONENT_MAP:
            return [os.path.join(test_dir, path) for path in COMPONENT_MAP[component]]
        else:
            print(f"Предупреждение: Неизвестный компонент '{component}'")
            print(f"Доступные компоненты: {', '.join(COMPONENT_MAP.keys())}")
            return [test_dir]

    # По умолчанию запускаем все тесты в директории test/
    if args.unit:
        return [os.path.join(test_dir, 'unit')]
    elif args.integration:
        return [test_dir]  # Все тесты, включая интеграционные
    else:
        return [test_dir]  # По умолчанию запускаем все модульные


def build_pytest_args(args, test_paths):
    """
    Собирает аргументы командной строки для pytest.
    """
    pytest_args = []

    # Настраиваем уровень детализации
    if args.verbose:
        pytest_args.extend(["-" + "v" * args.verbose])

    # Остановка при первой ошибке
    if args.failfast:
        pytest_args.append("--exitfirst")

    # Только список тестов
    if args.list:
        pytest_args.append("--collect-only")

    # Опции покрытия кода
    if args.coverage:
        pytest_args.append("--cov=meet2obsidian")

        if args.html:
            pytest_args.append("--cov-report=html")
        else:
            pytest_args.append("--cov-report=term")

        if args.fail_under > 0:
            pytest_args.append(f"--cov-fail-under={args.fail_under}")

    # Исключаем интеграционные тесты если не указаны --integration и --component
    if not args.integration and not args.component and not any("integration" in path for path in test_paths):
        pytest_args.extend(["-m", "not integration"])

    # Добавляем пути к тестам
    pytest_args.extend(test_paths)

    return pytest_args


if __name__ == "__main__":
    args = parse_args()

    # Определяем, какие тесты запускать
    test_paths = get_test_paths(args)

    # Собираем аргументы для pytest
    pytest_args = build_pytest_args(args, test_paths)

    # Запускаем pytest
    print(f"Запуск тестов с аргументами: {' '.join(pytest_args)}")
    sys.exit(pytest.main(pytest_args))