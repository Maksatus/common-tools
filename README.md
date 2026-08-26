# CommonTools

Набор небольших утилит и настроек для повседневной работы.

## Содержание

- [Git](#git)
  - [ToolsReset — Soft Reset для Fork](#toolsreset--soft-reset-для-fork)

## Git

### ToolsReset — Soft Reset для Fork

Добавляет в [Fork](https://git-fork.com/) две кастомные команды:

| Команда | Что делает |
| --- | --- |
| **Soft Reset (undo last commit)** | `git reset --soft HEAD~1` — отменяет последний коммит, файлы из него возвращаются в незакоммиченные изменения. |
| **Soft Reset to Remote** | `git reset --soft @{u}` — отменяет все коммиты, которые ещё не улетели на сервер. Файлы так же возвращаются в незакоммиченные изменения. |

#### Скачать

**[⬇ Скачать установщик](https://github.com/Maksatus/CommonTools/releases/latest/download/ToolsReset-Installer.bat)** — один файл, `custom-commands.json` уже внутри.

Все версии — на странице [Releases](https://github.com/Maksatus/CommonTools/releases).

#### Установка

Запустить скачанный `ToolsReset-Installer.bat` — он сам закроет Fork, сделает бэкап старых команд и положит `custom-commands.json` в `%LOCALAPPDATA%\Fork`.

Видео:

https://github.com/user-attachments/assets/68127fa9-a824-4ad0-99bc-aa85158e4ed8

#### Использование

Открыть Fork, нажать `Ctrl+P`, набрать `soft` и выбрать нужную команду.

Видео:

https://github.com/user-attachments/assets/04f233c9-0de7-48e7-b281-24943a4ebda0

---