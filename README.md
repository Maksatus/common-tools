# CommonTools

Набор небольших утилит и настроек для повседневной работы.

## Содержание

- [Git](#git)
  - [Fork Macros](#fork-macros)
- [Blender](#blender)
  - [Addon Harbor](#addon-harbor)

## Git

### Fork Macros

Кастомные команды для [Fork](https://git-fork.com/) — один установщик, внутри все макросы:

| Команда | Что делает |
| --- | --- |
| **Soft Reset (undo last commit)** | `git reset --soft HEAD~1` — отменяет последний коммит, файлы из него возвращаются в незакоммиченные изменения. |
| **Soft Reset to Remote** | `git reset --soft @{u}` — отменяет все коммиты, которые ещё не улетели на сервер. Файлы так же возвращаются в незакоммиченные изменения. |
| **Merge develop into current branch** | `git fetch` + `git merge --no-edit origin/develop` — обновляет `develop` с сервера и вливает его в текущую ветку. Только коммитит, ничего не пушит. |

#### Скачать

**[⬇ Скачать ForkMacros-v0.3.bat](https://github.com/Maksatus/CommonTools/releases/download/forkmacros-v0.3/ForkMacros-v0.3.bat)**

Все версии — на странице [Releases](https://github.com/Maksatus/CommonTools/releases).

#### Установка

Запустить скачанный `ForkMacros-v0.3.bat` — он сам закроет Fork, сделает бэкап старых команд и положит `custom-commands.json` в `%LOCALAPPDATA%\Fork`.

#### Использование

Открыть Fork, нажать `Ctrl+P` и выбрать нужную команду (`soft` — для сбросов, `merge` — для влития `develop`).

Видео:

https://github.com/user-attachments/assets/04f233c9-0de7-48e7-b281-24943a4ebda0

## Blender

### Addon Harbor

Расширение для Blender 4.2+. Добавляет кнопку в топбаре, из которой можно ставить, обновлять и удалять расширения из этого репозитория.

#### Скачать

**[⬇ Скачать AddonHarbor-v0.2.3.zip](https://github.com/Maksatus/CommonTools/releases/download/addonharbor-v0.2.3/AddonHarbor-v0.2.3.zip)**

#### Установка

Распаковывать архив не нужно, Blender ставит расширения прямо из zip:

1. `Edit → Preferences → Get Extensions`
2. Кнопка `⌄` справа сверху → `Install from Disk…`
3. Выбрать скачанный `AddonHarbor-v0.2.3.zip`

#### Использование

Кнопка **Addon Harbor** в топбаре открывает страницу расширения в настройках Blender
со списком расширений репозитория: установка, обновление и удаление в один клик.

---