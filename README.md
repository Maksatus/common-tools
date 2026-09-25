# CommonTools

Набор небольших утилит и настроек для повседневной работы.

**🌐 [maksatus.github.io/common-tools](https://maksatus.github.io/common-tools/)**: веб-инструменты и ссылки на скачивание всего остального.

## Содержание

- [Веб-инструменты](#веб-инструменты)
- [Blender](#blender)
  - [Addon Harbor](#addon-harbor)
- [Git](#git)
  - [Fork Macros](#fork-macros)

## Веб-инструменты

Открываются в браузере на [сайте](https://maksatus.github.io/common-tools/), скачивать ничего не нужно.
Файлы, которые бросаете в инструмент, никуда не загружаются: всё считается в браузере.

| Инструмент | Что делает |
| --- | --- |
| **[Сборщик рампы](https://maksatus.github.io/common-tools/#ramp-extractor)** | Восстанавливает градиент, которым раскрашен флипбук или текстура. Отдаёт рампу, ч/б версию и опорные точки для Gradient Map. |
| **[Размытие кубмапы](https://maksatus.github.io/common-tools/#cubemap-blur)** | Угловое размытие полосы 6:1 по направлениям на сфере, поэтому грани сходятся без стыков. `.hdr` и `.png`. |

#### Как добавить инструмент

1. Положить его в `Web/tools/<id>/index.html`.
2. Добавить запись в массив `TOOLS` в `Web/index.html`:
   ```js
   { id: "<id>", name: "Название", desc: "Что делает, одним-двумя предложениями.", tags: ["PNG"] }
   ```
3. Влить в `main`. Сайт обновится сам за минуту-две ([workflow](.github/workflows/pages.yml)).

Проверить до пуша: открыть `Web/index.html` двойным щелчком.

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

---