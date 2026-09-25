# CommonTools

Набор небольших утилит и настроек для повседневной работы.

<div align="center">

<a href="https://maksatus.github.io/common-tools/"><img alt="Открыть CommonTools в браузере" src="https://img.shields.io/badge/%F0%9F%8C%90%20%D0%9E%D1%82%D0%BA%D1%80%D1%8B%D1%82%D1%8C%20CommonTools-%D0%B2%D1%81%D1%91%20%D0%BD%D0%B0%20%D0%BE%D0%B4%D0%BD%D0%BE%D0%B9%20%D1%81%D1%82%D1%80%D0%B0%D0%BD%D0%B8%D1%86%D0%B5%20%E2%86%92-1E7A5C?style=for-the-badge" height="44"></a>

**Веб-инструменты работают прямо в браузере, всё остальное скачивается в один клик.**

</div>

## Содержание

- [Blender](#blender)
  - [Addon Harbor](#addon-harbor)
- [Git](#git)
  - [Fork Macros](#fork-macros)
- [Веб-инструменты](#веб-инструменты)

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

## Веб-инструменты

Открываются в браузере на [сайте](https://maksatus.github.io/common-tools/), скачивать ничего не нужно.
Файлы, которые бросаете в инструмент, никуда не загружаются: всё считается в браузере.

| Инструмент | Что делает |
| --- | --- |
| **[Сборщик рампы](https://maksatus.github.io/common-tools/#ramp-extractor)** | Восстанавливает градиент, которым раскрашен флипбук или текстура. Отдаёт рампу, ч/б версию и опорные точки для Gradient Map. |
| **[Размытие кубмапы](https://maksatus.github.io/common-tools/#cubemap-blur)** | Угловое размытие полосы 6:1 по направлениям на сфере, поэтому грани сходятся без стыков. `.hdr` и `.png`. |

---