# CommonTools

Набор небольших утилит и настроек для повседневной работы.

## Содержание

- [Git](#git)
  - [Auto Soft Reset](#auto-soft-reset)

## Git

### Auto Soft Reset

Добавляет в [Fork](https://git-fork.com/) две кастомные команды:

| Команда | Что делает |
| --- | --- |
| **Soft Reset (undo last commit)** | `git reset --soft HEAD~1` — отменяет последний коммит, файлы из него возвращаются в незакоммиченные изменения. |
| **Soft Reset to Remote** | `git reset --soft @{u}` — отменяет все коммиты, которые ещё не улетели на сервер. Файлы так же возвращаются в незакоммиченные изменения. |

#### Скачать

**[⬇ Скачать AutoSoftReset-v0.1.bat](https://github.com/Maksatus/CommonTools/releases/download/autosoftreset-v0.1/AutoSoftReset-v0.1.bat)**

Все версии — на странице [Releases](https://github.com/Maksatus/CommonTools/releases).

#### Установка

Запустить скачанный `AutoSoftReset-v0.1.bat` — он сам закроет Fork, сделает бэкап старых команд и положит `custom-commands.json` в `%LOCALAPPDATA%\Fork`.

#### Использование

Открыть Fork, нажать `Ctrl+P`, набрать `soft` и выбрать нужную команду.

Видео:

https://github.com/user-attachments/assets/04f233c9-0de7-48e7-b281-24943a4ebda0

---