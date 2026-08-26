# CommonTools

Набор небольших утилит и настроек для повседневной работы.

## Содержание

- [Git](#git)
  - [Auto Soft Reset](#auto-soft-reset)
- [Blender](#blender)
  - [Addon Harbor](#addon-harbor)

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

## Blender

### Addon Harbor

Расширение для Blender 4.2+. Добавляет кнопку в топбаре, из которой можно ставить, обновлять и удалять расширения из этого репозитория.

#### Скачать

**[⬇ Скачать AddonHarbor-v0.2.1.zip](https://github.com/Maksatus/CommonTools/releases/download/addonharbor-v0.2.1/AddonHarbor-v0.2.1.zip)**

#### Установка

Распаковывать архив не нужно, Blender ставит расширения прямо из zip:

1. `Edit → Preferences → Get Extensions`
2. Кнопка `⌄` справа сверху → `Install from Disk…`
3. Выбрать скачанный `AddonHarbor-v0.2.1.zip`

#### Использование

Кнопка **Addon Harbor** в топбаре открывает список расширений из репозитория.

---