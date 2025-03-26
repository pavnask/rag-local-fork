# AI Summary of Changes
---

## 🧠 Standards Evaluation: Rule vs AI

| System | Rule Match | AI Opinion | Verdict |
|--------|------------|------------|---------|
| **ecogroup.berezka.systems.berezka** | ✅ | ✅ Yes | ✅ Confirmed |
| **ecogroup.berezka.systems.berezka.catalog** | ✅ | ❌ No | ⚠️ Conflict |
| **ecogroup.berezka.systems.osinka** | ✅ | ✅ Yes | ✅ Confirmed |
| **ecogroup.berezka.systems.sosinka** | ✅ | ✅ Yes | ✅ Confirmed |
| **ecogroup.berezka.systems.dubok** | ✅ | ❌ No | ⚠️ Conflict |

> ⚠️ Conflicts indicate systems that passed rule-based checks but may need manual review based on AI interpretation.
> This is especially useful for standards that are fuzzy or rely on implicit context like "resides in Tier III".

---

\n\n## .YAML Files\n\n### KA/v2023/application/systems.yaml\n\nОбновления в YAML-файле в переводе на русский:

1. Добавлен секция `ecogroup.berezka.systems.fias`, которая описывает систему ФИАС (Федеральная информационная адресная система) и включает такие ключи, как `title`, `description`, `class`, `group`, `location`, `ownership`, `live_stage`, `live_stage_target`, `target_status`, `change_type`. Эта система является целевой и используется в промышленной эксплуатации.

2. Добавлена секция `ecogroup.berezka.systems.fias_gate`, которая описывает шлюз ФИАС (Fias Gate) и включает такие ключи, как `title`, `description`, `class`, `group`, `location`, `ownership`, `live_stage`, `live_stage_target`, `target_status`, `change_type`. Этот шлюз также является целевым и используется в промышленной эксплуатации.

3. Добавлена секция `ecogroup.berezka.repository.telegram`, которая описывает репозиторий Telegram и включает такие ключи, как `name`, `url`, `branch`. Этот репозиторий не является целевым и используется в разработке / приобретении.

4. Добавлены секции `ecogroup.berezka.systems.sosinka`, `ecogroup.berezka.systems.dubok`, которые описывают соответственно систему Sosinka и Dubok, являющиеся частями маркетплейса в разработке / приобретении. Эти системы не являются целевыми, но относятся к критическим бизнес-процессам (Business Critical).

5. Обновлены значения `live_stage` и `live_stage_target` для нескольких секций систем, включая Fias, Fias Gate, Sosinka, Dubok, для которых изменено состояние жизненного цикла от разработки / приобретения к промышленной эксплуатации.

6. Обновлена секция `ecogroup.berezka.systems.fias`, которая включает такие параметры, как `criticality`, `performance`, `rto`, `rpo`, `sla`, `monitoring`. Это обновление влияет на показатели KPI и конфигурацию системы ФИАС.

7. Обновлена секция `ecogroup.berezka.systems.dubok`, которая включает такие параметры, как `parent`. Это обновление указывает, что система Dubok является частью системы Sosinka.

8. Добавлены значения для ключей `name` и `url`, относящихся к репозиторию Telegram, а также значение `branch` для указанного репозитория в секции `ecogroup.berezka.repository.telegram`.

9. Обновлены значения параметров `rto`, `rpo` и `sla` для нескольких систем, включая Fias, Fias Gate, Sosinka, Dubok, что влияет на показатели KPI и конфигурацию этих систем.

10. В секциях `ecogroup.berezka.systems.fias` и `ecogroup.berezka.systems.fias_gate` добавлено значение `monitoring`, которое равно «Нет». Это обновление влияет на конфигурацию шлюза ФИАС и системы ФИАС, так как отсутствует мониторинг этих систем.

Вывод: Были добавлены секции для систем Fias, Fias Gate, Sosinka, Dubok и репозитория Telegram, обновлено состояние жизненного цикла для нескольких систем, а также внесены изменения в значения показателей KPI и конфигурацию различных систем.\n#### Requirements Check\n\n- ⚠️ sla value 95 is below the minimum of 99\n- ⚠️ rto value 24 exceeds the maximum of 20\n\n\n### _ecosystems_/kadzo/v2023/entities/application/systems.yaml\n\nВ репозитории были добавлены изменения в файле YAML, который описывает систему управления данными (CDD). Ниже приведена сводка об изменениях:

  * В раздел `repositories` добавлена новая структура `cdd`, которая содержит следующие ключи и секции:
    + `name` - имя репозитория.
    + `url` - URL-адрес репозитория.
    + `branches` - список веток, для которых будет производиться синхронизация.
  * В раздел `stages` добавлено новое состояние `test`, в который были включены следующие шаги:
    + `lint` - запуск linter для проверки кода на соответствие стандартам.
    + `analysis` - запуск статического анализатора для обнаружения уязвимостей и ошибок в коде.
    + `unit_tests` - выполнение единичных тестов, написанных для отдельных модулей или функций.
  * В раздел `jobs` добавлены новые задания:
    + `build` - сборка проекта и создание артефактов (пакеты, библиотеки).
    + `test` - тестирование проекта на уровне единичных тестов и интеграционных тестов.
    + `deploy` - развертывание проекта в продуктивную среду (производство, тестирование).
  * В секцию `jobs.build.steps` добавлен шаг `install_dependencies`, в котором описывается процесс установки зависимостей для проекта.
  * В секцию `jobs.test.steps` добавлен шаг `deploy`, в котором описано развертывание тестовой среды перед началом тестирования.
  * В секцию `services` добавлено новое сервисное приложение `sentry-dsn`, которое будет отправлять сообщения об ошибках в Sentry для анализа и обработки.

   Эти изменения увеличивают функциональность и эффективность системы управления данными, обеспечивая более надежную работу, автоматизацию тестирования и развертывания проектов.\n#### Requirements Check\n\n- ✅ YAML meets all requirements\n\n\n### dochub.yaml\n\nВ этом файле YAML конфигурации добавлен новый файл доchub.yaml. Существенные изменения в этом файле следующие:

  - Добавлен раздел "imports", который подключает три других YAML-файла: _ecosystems_/root.yaml, KA/root.yaml и _эталонные данные шаблона ДЗО без ошибок_.
  - Коментарии для подключения еще трех файлов (eco_facades/root.yaml, KA_template/root.yaml и drw/root.yaml) удалены или комментированы.

 Изменения в файле могут иметь значительный влияние на поведение и конфигурацию проекта:
 - Подключение _экосистема_/root.yaml включает стандарты Сбера.
 - Подключение KA/root.yaml используется для использования эталонных данных шаблона ДЗО без ошибок.

 Эти изменения должны улучшить соответствие проекта к стандартам Сбера и помогают избежать ошибок в использовании данных шаблона ДЗО.\n#### Requirements Check\n\n- ❌ Missing required field: title\n- ❌ Missing required field: description\n- ❌ Missing required field: class\n\n