#!/bin/bash

echo "🔧 Установка зависимостей для программы распознавания чисел..."

# Проверяем наличие Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew не найден. Установите Homebrew сначала:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# Устанавливаем Tesseract
echo "📦 Установка Tesseract OCR..."
brew install tesseract

# Создаем виртуальную среду
echo "🐍 Создание виртуальной среды..."
python3 -m venv venv

# Активируем виртуальную среду
echo "🔄 Активация виртуальной среды..."
source venv/bin/activate

# Устанавливаем Python зависимости
echo "📦 Установка Python зависимостей..."
pip install -r requirements.txt

echo "✅ Установка завершена!"
echo ""
echo "🚀 Для запуска программы выполните:"
echo "   source venv/bin/activate"
echo "   python 123456789000.py"
echo ""
echo "📊 Для просмотра данных:"
echo "   source venv/bin/activate" 
echo "   python 123456789000.py --view" 