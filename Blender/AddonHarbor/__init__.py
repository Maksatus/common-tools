"""Addon Harbor — установка расширений из приватного репозитория.

Кнопка в топбаре открывает страницу настроек со списком расширений:
установка, обновление, удаление, описания и ссылки.
"""

import json
import os
import re
import threading
import time
import urllib.error
import urllib.request

import bpy

# =============================================================== настройки

REPO_URL = "https://harbor-gate.streetworkout042000.workers.dev/blender-repo/index.json"
REPO_NAME = "Addon Harbor"
REPO_MODULE = "addon_harbor_repo"

EXTRA_FILE = "harbor_extra.json"   # описания и ссылки, лежит рядом с index.json
BUTTON_TEXT = "Addon Harbor"
TIMEOUT = 15                       # секунд на запрос
NO_TAG = "Прочее"                  # группа для расширений без тегов

# --- разметка списка ---
NAME_COLUMN = 0.6      # доля ширины под название
VERSION_WIDTH = 5.0    # ui_units: колонка версии
ACTION_WIDTH = 7.0     # ui_units: кнопка Install / Update
TRASH_WIDTH = 1.5      # ui_units: корзина
DESC_WIDTH = 78        # символов в строке описания (полное окно)
ERROR_WIDTH = 58       # символов в строке ошибки
INSTALLED_TTL = 2.0    # секунд: кэш списка установленного

LOG = "[Addon Harbor]"

# =============================================================== состояние

_state = {
    "packages": [],      # список словарей из index.json
    "extra": {},         # описания и ссылки из harbor_extra.json
    "error": None,       # текст ошибки загрузки
    "loading": False,
    "loaded": False,
    "collapsed": set(),  # id расширений со свёрнутым описанием
                         # (по умолчанию описание раскрыто)
    "updates": 0,
    "installed": 0,
    "tick": 0,           # счётчик для многоточия у надписи «Загрузка»
}

_installed_cache = {"data": {}, "time": 0.0}


# =============================================================== утилиты

def _log(message):
    print(f"{LOG} {message}")


def _prefs():
    """Настройки расширения или None, если Blender их ещё не поднял."""
    try:
        return bpy.context.preferences.addons[__package__].preferences
    except (KeyError, AttributeError):
        return None


def _token():
    """Токен доступа, введённый пользователем. Пустая строка — не настроен."""
    prefs = _prefs()
    return (getattr(prefs, "token", "") or "").strip() if prefs else ""


def _call_op(operator, variants):
    """Вызывает оператор, перебирая наборы аргументов от полного к простому.

    Параметры операторов расширений менялись между версиями Blender,
    поэтому вместо одного жёсткого вызова пробуем несколько.
    Возвращает (успех, последняя ошибка).
    """
    last_error = None
    for kwargs in variants:
        try:
            operator(**kwargs)
            return True, None
        except TypeError as exc:      # неподходящее имя параметра — пробуем дальше
            last_error = exc
        except RuntimeError as exc:   # оператор отказался работать — дальше смысла нет
            return False, exc
    return False, last_error


def _wrap(text, width):
    """Режет строку на куски: в UI Blender нет переноса по словам."""
    lines, current = [], ""
    for word in str(text).split(" "):
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:width])
            word = word[width:]
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def _version_tuple(value):
    """'3.78.41' -> (3, 78, 41). Нечисловые части считаем нулями."""
    parts = [
        int(chunk) if chunk.isdigit() else 0
        for chunk in re.split(r"[.\-+]", str(value or ""))
    ]
    return tuple(parts) or (0,)


def _has_update(local, remote):
    """True, если в репозитории версия новее установленной."""
    if not local or not remote:
        return False
    left, right = _version_tuple(local), _version_tuple(remote)
    length = max(len(left), len(right))
    left += (0,) * (length - len(left))
    right += (0,) * (length - len(right))
    return right > left


def _redraw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            area.tag_redraw()


# =============================================================== репозиторий

def _matching_repos():
    """Записи, похожие на наш репозиторий: [(индекс, объект, признак)].

    Ищем по трём признакам, потому что URL мог измениться, а имя и module
    пользователь может переименовать вручную.
    """
    found = []
    for index, repo in enumerate(bpy.context.preferences.extensions.repos):
        if getattr(repo, "remote_url", "") == REPO_URL:
            found.append((index, repo, "url"))
        elif repo.module == REPO_MODULE:
            found.append((index, repo, "module"))
        elif repo.name == REPO_NAME:
            found.append((index, repo, "name"))
    found.sort(key=lambda item: 0 if item[2] == "url" else 1)
    return found


def _find_repo():
    """(индекс, объект) нашего репозитория или (-1, None)."""
    found = _matching_repos()
    return found[0][:2] if found else (-1, None)


def _save_prefs():
    try:
        bpy.ops.wm.save_userpref()
    except Exception as exc:
        _log(f"save_userpref: {exc}")


def _repair_repo(repo):
    """Приводит найденную запись в рабочее состояние. Возвращает список правок."""
    fixed = []
    checks = [
        ("remote_url", REPO_URL, "URL"),
        ("module", REPO_MODULE, "module"),
        ("use_remote_url", True, "тип: удалённый"),
        ("enabled", True, "включён"),
    ]
    # свои запросы мы подписываем сами, но пакеты качает Blender —
    # ему токен нужно положить в саму запись репозитория
    token = _token()
    if token:
        checks += [
            ("use_access_token", True, "токен включён"),
            ("access_token", token, "токен"),
        ]
    else:
        # токена нет — снимаем флаг, иначе синк отвалится с пустым токеном
        checks.append(("use_access_token", False, "токен выключен"))
    for attribute, expected, label in checks:
        current = getattr(repo, attribute, expected)
        if current == expected:
            continue
        try:
            setattr(repo, attribute, expected)
            fixed.append(label)
        except Exception as exc:
            _log(f"{attribute}: {exc}")
    return fixed


def _remove_repo_at(index):
    return _call_op(
        bpy.ops.preferences.extension_repo_remove,
        [dict(index=index, remove_files=False), dict(index=index), dict()],
    )


def _add_repo():
    return _call_op(
        bpy.ops.preferences.extension_repo_add,
        [
            dict(name=REPO_NAME, remote_url=REPO_URL, type='REMOTE',
                 use_sync_on_startup=True),
            dict(name=REPO_NAME, remote_url=REPO_URL, type='REMOTE'),
            dict(name=REPO_NAME, remote_url=REPO_URL),
            dict(remote_url=REPO_URL),
        ],
    )


def _ensure_repo():
    """Находит, чинит или создаёт репозиторий. Возвращает (индекс, объект)."""
    # лишние записи от прежних попыток — удаляем с конца, чтобы не съехали индексы
    duplicates = _matching_repos()[1:]
    for index, _repo, _how in sorted(duplicates, key=lambda item: -item[0]):
        ok, error = _remove_repo_at(index)
        if not ok:
            _log(f"удаление дубля: {error}")

    index, repo = _find_repo()

    if repo is not None:
        fixed = _repair_repo(repo)
        if fixed:
            _log("исправлено -> " + ", ".join(fixed))
            _save_prefs()
        return index, repo

    ok, error = _add_repo()
    if not ok:
        _log(f"extension_repo_add: {error}")
        return -1, None

    index, repo = _find_repo()
    if repo is not None:
        _repair_repo(repo)
        _save_prefs()
        _log(f"репозиторий добавлен: {REPO_URL}")
    return index, repo


def _on_token_changed():
    """Токен поменяли в настройках: переписать его в репозиторий и перечитать список."""

    # из update-колбэка свойства нельзя вызывать операторы, поэтому отложенно
    def apply():
        _state.update(packages=[], error=None, loaded=False)
        try:
            _index, repo = _find_repo()
            if repo is None:
                _ensure_repo()
            elif _repair_repo(repo):
                _save_prefs()
        except Exception as exc:
            _log(f"применение токена: {exc}")

        if _token():
            # синхронно, а не фоном: короткая пауза лучше, чем окно,
            # застрявшее на «Загрузка»
            _fetch_index(force=True)
            _invalidate_installed()
            _recount()
        _redraw()
        return None

    bpy.app.timers.register(apply, first_interval=0.0)


def _sync_repo(index):
    ok, error = _call_op(
        bpy.ops.extensions.repo_sync, [dict(repo_index=index), dict()]
    )
    if not ok:
        _call_op(bpy.ops.extensions.repo_sync_all, [dict()])
        _log(f"repo_sync: {error}")


def _install_package(index, repo, pkg_id):
    variants = [
        dict(repo_index=index, pkg_id=pkg_id, enable_on_install=True),
        dict(repo_index=index, pkg_id=pkg_id),
    ]
    directory = getattr(repo, "directory", "") if repo else ""
    if directory:
        variants.append(
            dict(repo_directory=directory, pkg_id=pkg_id, enable_on_install=True)
        )
    return _call_op(bpy.ops.extensions.package_install, variants)


def _uninstall_package(index, repo, pkg_id):
    variants = [dict(repo_index=index, pkg_id=pkg_id)]
    directory = getattr(repo, "directory", "") if repo else ""
    if directory:
        variants.append(dict(repo_directory=directory, pkg_id=pkg_id))
    return _call_op(bpy.ops.extensions.package_uninstall, variants)


# =============================================================== установленное

def _read_manifest_version(path):
    """Версия из blender_manifest.toml установленного расширения."""
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
    except OSError:
        return None

    try:
        import tomllib
        return str(tomllib.loads(raw.decode("utf-8")).get("version", "")) or None
    except Exception:
        pass

    match = re.search(
        r'^\s*version\s*=\s*["\']([^"\']+)["\']',
        raw.decode("utf-8", errors="replace"),
        re.M,
    )
    return match.group(1) if match else None


def _scan_installed():
    """{pkg_id: версия или None} — читает папку репозитория."""
    _, repo = _find_repo()
    directory = getattr(repo, "directory", "") if repo else ""
    if not directory or not os.path.isdir(directory):
        return {}

    result = {}
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isdir(path) and not name.startswith("."):
            result[name] = _read_manifest_version(
                os.path.join(path, "blender_manifest.toml")
            )
    return result


def _installed_map(force=False):
    """То же со кэшем: draw вызывается на каждое движение мыши."""
    now = time.monotonic()
    if not force and now - _installed_cache["time"] < INSTALLED_TTL:
        return _installed_cache["data"]

    data = _scan_installed()
    _installed_cache.update(data=data, time=now)
    return data


def _invalidate_installed():
    _installed_cache["time"] = 0.0


def _recount():
    """Пересчитывает счётчики установленного и обновлений."""
    installed = _installed_map(force=True)
    updates = 0
    for package in _state["packages"]:
        local = installed.get(package["id"])
        if local is not None and _has_update(local, package.get("version")):
            updates += 1
    _state["updates"] = updates
    _state["installed"] = sum(
        1 for package in _state["packages"] if package["id"] in installed
    )


# =============================================================== загрузка

def _http_json(url, required, token=""):
    """Скачивает JSON. Возвращает (данные, ошибка).

    required=False — отсутствие файла (404) не считается ошибкой.
    Токен передаётся аргументом: функция вызывается из фонового потока,
    а читать bpy.context оттуда нельзя.
    """
    try:
        headers = {"User-Agent": "AddonHarbor/2.0"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        request = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            if not required:
                return None, None
            return None, "404 — файла нет по этому адресу. Проверь путь"
        if exc.code in (401, 403):
            reason = ("токен не принят — проверь, что он введён верно "
                      "и ещё действует" if token else "нужен токен доступа")
            return None, f"{exc.code} — доступ закрыт: {reason}"
        return None, f"HTTP {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        return None, f"Нет соединения: {exc.reason}"
    except TimeoutError:
        return None, f"Таймаут ({TIMEOUT} c) — сервер не ответил"
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"

    try:
        return json.loads(body), None
    except json.JSONDecodeError:
        return None, "по адресу лежит не JSON — ссылка должна вести на index.json"


def _fetch_index(force=False, token=None):
    """Читает index.json и harbor_extra.json. Синхронно.

    token=None — взять из настроек; из фонового потока его надо передать
    заранее прочитанным, оттуда bpy.context недоступен.
    """
    if _state["loaded"] and not force:
        return

    if token is None:
        token = _token()

    data, error = _http_json(REPO_URL, required=True, token=token)
    if error:
        _state.update(packages=[], error=error, loaded=True, loading=False)
        return

    raw = data.get("data") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        _state.update(
            packages=[], error="в index.json нет списка расширений",
            loaded=True, loading=False,
        )
        return

    packages = [item for item in raw if isinstance(item, dict) and item.get("id")]
    packages.sort(key=lambda item: (item.get("name") or item["id"]).lower())

    base = REPO_URL.rsplit("/", 1)[0]
    extra, extra_error = _http_json(f"{base}/{EXTRA_FILE}", required=False,
                                    token=token)
    if extra_error:
        _log(f"{EXTRA_FILE}: {extra_error}")

    _state.update(
        packages=packages,
        extra=extra if isinstance(extra, dict) else {},
        error=None,
        loaded=True,
        loading=False,
    )


def _fetch_index_async():
    """Фоновая загрузка при старте — чтобы счётчик появился без открытия окна."""
    if _state["loading"]:
        return
    _state["loading"] = True

    # пока грузим, дёргаем перерисовку: сама по себе она не случится,
    # а надпись «Загрузка…» должна шевелиться
    def tick():
        if not _state["loading"]:
            _redraw()
            return None
        _state["tick"] += 1
        _redraw()
        return 0.25

    bpy.app.timers.register(tick, first_interval=0.25)

    # токен читаем здесь, в главном потоке, и отдаём потоку готовым
    token = _token()

    def worker():
        try:
            _fetch_index(force=True, token=token)
        except Exception as exc:
            # без этого падение потока оставило бы вечную «Загрузку»
            _state.update(packages=[], loaded=True,
                          error=f"{type(exc).__name__}: {exc}")

        def apply():
            _state["loading"] = False
            _recount()
            _redraw()
            return None

        bpy.app.timers.register(apply, first_interval=0.0)

    threading.Thread(target=worker, daemon=True).start()


def _package_details(pkg_id):
    """(описание, [(подпись, ссылка)]) из harbor_extra.json."""
    entry = _state["extra"].get(pkg_id)
    if not isinstance(entry, dict):
        return None, []

    links = []
    for link in entry.get("links") or []:
        if not isinstance(link, dict):
            continue
        url = str(link.get("url") or "").strip()
        if not url.startswith(("http://", "https://")):
            continue      # только веб-ссылки: никаких file:// и javascript:
        links.append((str(link.get("label") or url)[:48], url))

    return entry.get("description"), links[:6]


def _group_by_tag(packages):
    """[(тег, [пакеты])]. Расширение попадает в группу по первому тегу."""
    groups = {}
    for package in packages:
        tags = package.get("tags")
        tag = str(tags[0]) if isinstance(tags, (list, tuple)) and tags else NO_TAG
        groups.setdefault(tag, []).append(package)

    ordered = sorted((tag for tag in groups if tag != NO_TAG), key=str.lower)
    if NO_TAG in groups:
        ordered.append(NO_TAG)
    return [(tag, groups[tag]) for tag in ordered]


# =============================================================== операторы

class ADDONHARBOR_OT_refresh(bpy.types.Operator):
    bl_idname = "addon_harbor.refresh"
    bl_label = "Обновить список"
    bl_description = "Заново скачать список расширений из репозитория"

    def execute(self, context):
        _ensure_repo()
        _fetch_index(force=True)
        _invalidate_installed()
        _recount()
        self.report({'INFO'}, f"Найдено расширений: {len(_state['packages'])}")
        return {'FINISHED'}


class ADDONHARBOR_OT_install(bpy.types.Operator):
    bl_idname = "addon_harbor.install"
    bl_label = "Установить"
    bl_description = "Скачать и включить это расширение"

    pkg_id: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        index, repo = _ensure_repo()
        if repo is None:
            self.report({'ERROR'}, "Не удалось добавить репозиторий")
            return {'CANCELLED'}

        _sync_repo(index)
        ok, error = _install_package(index, repo, self.pkg_id)

        _invalidate_installed()
        _recount()

        if not ok:
            self.report({'ERROR'}, f"Установка не удалась: {error}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Установлено: {self.pkg_id}")
        return {'FINISHED'}


class ADDONHARBOR_OT_uninstall(bpy.types.Operator):
    bl_idname = "addon_harbor.uninstall"
    bl_label = "Удалить"
    bl_description = "Удалить это расширение"

    pkg_id: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        index, repo = _find_repo()
        if repo is None:
            self.report({'ERROR'}, "Репозиторий не найден")
            return {'CANCELLED'}

        ok, error = _uninstall_package(index, repo, self.pkg_id)

        _invalidate_installed()
        _recount()

        if not ok:
            self.report({'ERROR'}, f"Удаление не удалось: {error}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Удалено: {self.pkg_id}")
        return {'FINISHED'}


class ADDONHARBOR_OT_install_all(bpy.types.Operator):
    bl_idname = "addon_harbor.install_all"
    bl_label = "Установить всё"
    bl_description = "Установить отсутствующие и обновить устаревшие расширения"

    def execute(self, context):
        index, repo = _ensure_repo()
        if repo is None:
            self.report({'ERROR'}, "Не удалось добавить репозиторий")
            return {'CANCELLED'}

        _sync_repo(index)

        installed = _installed_map(force=True)
        added, updated, failed = 0, 0, 0

        for package in _state["packages"]:
            pkg_id = package["id"]
            is_installed = pkg_id in installed
            if is_installed and not _has_update(
                installed.get(pkg_id), package.get("version")
            ):
                continue

            ok, error = _install_package(index, repo, pkg_id)
            if not ok:
                _log(f"{pkg_id}: {error}")
                failed += 1
            elif is_installed:
                updated += 1
            else:
                added += 1

        _invalidate_installed()
        _recount()
        self.report(
            {'INFO'},
            f"Установлено: {added}, обновлено: {updated}, ошибок: {failed}",
        )
        return {'FINISHED'}


class ADDONHARBOR_OT_toggle_expand(bpy.types.Operator):
    bl_idname = "addon_harbor.toggle_expand"
    bl_label = "Подробнее"
    bl_description = "Показать или скрыть описание и ссылки"
    bl_options = {'INTERNAL'}

    pkg_id: bpy.props.StringProperty(options={'SKIP_SAVE'})

    def execute(self, context):
        collapsed = _state["collapsed"]
        if self.pkg_id in collapsed:
            collapsed.discard(self.pkg_id)
        else:
            collapsed.add(self.pkg_id)
        return {'FINISHED'}


class ADDONHARBOR_OT_reset_repo(bpy.types.Operator):
    bl_idname = "addon_harbor.reset_repo"
    bl_label = "Пересоздать репозиторий"
    bl_description = (
        "Удалить все записи репозитория и создать заново. "
        "Установленные расширения не удаляются"
    )

    def execute(self, context):
        removed = 0
        for index, _repo, _how in sorted(_matching_repos(), key=lambda i: -i[0]):
            ok, error = _remove_repo_at(index)
            if ok:
                removed += 1
            else:
                _log(f"remove: {error}")

        index, repo = _ensure_repo()
        if repo is None:
            self.report({'ERROR'}, "Не удалось создать репозиторий")
            return {'CANCELLED'}

        _sync_repo(index)
        _fetch_index(force=True)
        _invalidate_installed()
        _recount()
        self.report({'INFO'}, f"Удалено записей: {removed}, создан заново")
        return {'FINISHED'}


class ADDONHARBOR_OT_open_prefs(bpy.types.Operator):
    bl_idname = "addon_harbor.open_prefs"
    bl_label = "Открыть полный список"
    bl_description = "Открыть страницу Addon Harbor в настройках Blender"

    def execute(self, context):
        _ensure_repo()
        _fetch_index(force=True)
        _invalidate_installed()
        _recount()

        # addon_show открывает настройки и раскрывает запись нашего аддона
        ok, error = _call_op(
            bpy.ops.preferences.addon_show, [dict(module=__package__)]
        )
        if not ok:
            _log(f"addon_show: {error}")
            _call_op(bpy.ops.screen.userpref_show, [dict()])
            try:
                context.preferences.active_section = 'ADDONS'
            except Exception as exc:
                _log(f"active_section: {exc}")

        # фильтр по названию, чтобы не листать весь список аддонов
        try:
            context.window_manager.addon_search = BUTTON_TEXT
        except Exception as exc:
            _log(f"addon_search: {exc}")

        return {'FINISHED'}


# =============================================================== отрисовка

def _draw_summary(layout, with_refresh=False):
    """Строка статистики и кнопка массовой установки."""
    _recount()

    top = layout.row(align=True)
    stats = top.row()
    stats.enabled = False
    stats.label(
        text=(
            f"Всего {len(_state['packages'])}"
            f"  \u00b7  Установлено {_state['installed']}"
            f"  \u00b7  Обновлений {_state['updates']}"
        )
    )
    if with_refresh:
        top.operator("addon_harbor.refresh", text="", icon='FILE_REFRESH')

    updates = _state["updates"]
    layout.operator(
        "addon_harbor.install_all",
        text=(
            f"Установить и обновить всё ({updates})" if updates
            else "Установить всё"
        ),
        icon='IMPORT',
    )


def _draw_loading(layout):
    """Заглушка на время загрузки: пустой список и «загружается» — разные вещи."""
    dots = "." * (_state["tick"] % 4)
    row = layout.row()
    row.enabled = False
    row.label(text=f"Загрузка списка{dots}", icon='SORTTIME')


def _draw_token_form(layout):
    """Экран для тех, кто ещё не ввёл токен: без него репозиторий не отвечает."""
    box = layout.box()
    box.label(text="Нужен токен доступа", icon='LOCKED')

    hint = box.column(align=True)
    hint.enabled = False
    hint.scale_y = 0.8
    text = ("Введите токен, выданный вместе с доступом к репозиторию. "
            "Он сохранится в настройках Blender — вводить каждый раз не нужно.")
    for chunk in _wrap(text, ERROR_WIDTH):
        hint.label(text=chunk)

    prefs = _prefs()
    if prefs is None:
        box.separator(factor=0.5)
        box.label(text="Настройки расширения недоступны", icon='ERROR')
        return

    box.separator(factor=0.5)
    box.prop(prefs, "token", text="")
    box.operator("addon_harbor.refresh", text="Проверить", icon='FILE_REFRESH')


def _draw_error(layout):
    box = layout.box()
    box.label(text="Репозиторий недоступен", icon='ERROR')

    message = box.column(align=True)
    message.scale_y = 0.8
    for chunk in _wrap(_state["error"], ERROR_WIDTH):
        message.label(text=chunk)

    box.separator(factor=0.5)
    address = box.column(align=True)
    address.enabled = False
    address.scale_y = 0.8
    address.label(text="Адрес:")
    for chunk in _wrap(REPO_URL, ERROR_WIDTH):
        address.label(text=chunk)

    prefs = _prefs()
    if prefs is not None:
        # чаще всего причина как раз в токене, поэтому поле под рукой
        box.separator(factor=0.5)
        box.prop(prefs, "token")

    box.separator(factor=0.5)
    row = box.row(align=True)
    row.operator("addon_harbor.refresh", text="Повторить", icon='FILE_REFRESH')
    row.operator("addon_harbor.reset_repo", text="Пересоздать", icon='TRASH')


def _draw_row(layout, package, installed):
    """Одна карточка расширения."""
    pkg_id = package["id"]
    remote_version = package.get("version")
    local_version = installed.get(pkg_id)
    is_installed = pkg_id in installed
    can_update = is_installed and _has_update(local_version, remote_version)
    is_open = pkg_id not in _state["collapsed"]

    description, links = _package_details(pkg_id)
    has_details = bool(description or links)

    box = layout.box()

    # --- строка: название | версия | действие | корзина ---
    # split даёт жёсткие колонки: правый край не зависит от длины названия
    split = box.split(factor=NAME_COLUMN, align=True)
    split.label(
        text=package.get("name") or pkg_id,
        icon='IMPORT' if can_update else ('CHECKMARK' if is_installed else 'DOT'),
    )

    right = split.row(align=True)

    version = right.row()
    version.enabled = False
    version.alignment = 'RIGHT'
    version.ui_units_x = VERSION_WIDTH
    if can_update:
        version.label(text=f"{local_version} \u2192 {remote_version}")
    elif remote_version:
        version.label(text=str(remote_version))

    action = right.row(align=True)
    action.ui_units_x = ACTION_WIDTH
    if can_update:
        action.operator(
            "addon_harbor.install", text="Update", icon='FILE_REFRESH'
        ).pkg_id = pkg_id
    elif not is_installed:
        action.operator("addon_harbor.install", text="Install").pkg_id = pkg_id
    else:
        stub = action.row()
        stub.enabled = False
        stub.alignment = 'CENTER'
        stub.label(text="установлено")

    trash = right.row(align=True)
    trash.ui_units_x = TRASH_WIDTH
    if is_installed:
        trash.operator(
            "addon_harbor.uninstall", text="", icon='TRASH'
        ).pkg_id = pkg_id
    else:
        trash.label(text="")   # заглушка, иначе правый край прыгает

    if not has_details:
        return

    # --- стрелка отдельной строкой под текстом, чтобы не сдвигать название ---
    toggle = box.row(align=True)
    toggle.alignment = 'LEFT'
    toggle.operator(
        "addon_harbor.toggle_expand",
        text="Свернуть" if is_open else "Подробнее",
        icon='TRIA_UP' if is_open else 'TRIA_DOWN',
        emboss=False,
    ).pkg_id = pkg_id

    if not is_open:
        return

    if description:
        block = box.column(align=True)
        block.scale_y = 0.8
        for paragraph in str(description).split("\n"):
            if not paragraph.strip():
                block.separator(factor=0.4)
                continue
            for chunk in _wrap(paragraph.strip(), DESC_WIDTH):
                block.label(text=chunk)

    if links:
        link_column = box.column(align=True)
        for label, url in links:
            link_column.operator("wm.url_open", text=label, icon='URL').url = url


class ADDONHARBOR_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    token: bpy.props.StringProperty(
        name="Токен доступа",
        description="Выдаётся вместе с доступом к репозиторию. "
                    "Хранится в настройках Blender, вводится один раз",
        subtype='PASSWORD',
        update=lambda self, context: _on_token_changed(),
    )

    def draw(self, context):
        layout = self.layout

        if not _token():
            _draw_token_form(layout)
            return

        layout.prop(self, "token")
        layout.separator(factor=0.5)

        if _state["loading"] or not _state["loaded"]:
            _draw_loading(layout)
            return

        if _state["error"]:
            _draw_error(layout)
            return

        if not _state["packages"]:
            row = layout.row(align=True)
            row.label(text="Список пуст", icon='INFO')
            row.operator("addon_harbor.refresh", text="Обновить",
                         icon='FILE_REFRESH')
            return

        installed = _installed_map()
        _draw_summary(layout, with_refresh=True)
        layout.separator(factor=0.5)

        for tag, packages in _group_by_tag(_state["packages"]):
            column = layout.column(align=True)
            header = column.row()
            header.scale_y = 0.9
            header.label(text=tag, icon='BOOKMARKS')
            for package in packages:
                _draw_row(column, package, installed)
            layout.separator(factor=0.3)


def _topbar_draw(self, context):
    # топбар рисуется дважды — для левого и правого региона. Нужен правый.
    if context.region.alignment != 'RIGHT':
        return

    # число берём из состояния: здесь нельзя считать ничего тяжёлого,
    # функция вызывается на каждую перерисовку интерфейса
    updates = _state["updates"]
    self.layout.operator(
        "addon_harbor.open_prefs",
        text=f"{BUTTON_TEXT} ({updates})" if updates else BUTTON_TEXT,
        icon='IMPORT' if updates else 'URL',
    )


# =============================================================== регистрация

_classes = (
    ADDONHARBOR_OT_refresh,
    ADDONHARBOR_OT_install,
    ADDONHARBOR_OT_uninstall,
    ADDONHARBOR_OT_install_all,
    ADDONHARBOR_OT_toggle_expand,
    ADDONHARBOR_OT_reset_repo,
    ADDONHARBOR_OT_open_prefs,
    ADDONHARBOR_Preferences,
)


def _deferred_setup():
    """Выполняется после запуска Blender: в register() операторы вызывать нельзя."""
    if not _token():
        # без токена репозиторий всё равно ответит 401 — не шумим на старте,
        # окно аддона попросит токен
        _log("токен не введён — настройте расширение")
        return None

    try:
        _ensure_repo()
    except Exception as exc:
        _log(f"не удалось добавить репозиторий: {exc}")

    try:
        _fetch_index_async()
    except Exception as exc:
        _log(f"фоновая проверка: {exc}")
    return None


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_HT_upper_bar.prepend(_topbar_draw)
    bpy.app.timers.register(_deferred_setup, first_interval=0.5)


def unregister():
    bpy.types.TOPBAR_HT_upper_bar.remove(_topbar_draw)
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)
