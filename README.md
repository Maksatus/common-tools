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

Файлы: [`Git/ToolsReset`](Git/ToolsReset)

#### Установка

Запустить [`install-fork-commands.bat`](Git/ToolsReset/install-fork-commands.bat) — он сам закроет Fork, сделает бэкап старых команд и положит `custom-commands.json` в `%LOCALAPPDATA%\Fork`.

Видео:

https://github.com/user-attachments/assets/68127fa9-a824-4ad0-99bc-aa85158e4ed8

#### Использование

Открыть Fork, нажать `Ctrl+P`, набрать `soft` и выбрать нужную команду.

Видео: [Doc/Usage.mp4](Doc/Usage.mp4)

https://github.com/user-attachments/assets/REPLACE_ME_USAGE
