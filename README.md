# Renju Online


Веб-реализация японской настольной логической игры [рендзю](https://ru.wikipedia.org/wiki/%D0%A0%D1%8D%D0%BD%D0%B4%D0%B7%D1%8E).  

---

- [Описание](#описание)
- [Стэк](#стэк)
- [Правила](#правила)
- [Технические детали](#технические-детали)
- [Иллюстрации](#иллюстрации)

### Описание

**Рендзю** - японская настольная логическая игра, представляющая собой в предельном упрощении спортивную вариацию крестиков-ноликов до 5 в ряд.  
Данное приложение позволяет играть в рендзю онлайн с другими людьми.  

### Стэк

- FastAPI
- PostgreSQL 14
- SQLAlchemy 1.4/2.0 (asyncpg)
- Alembic
- WebSockets
- AsyncIO
- Pytest
- Docker & docker-compose
- Nginx
- HTML / CSS / JavaScript

### Правила

- По умолчанию: крестики-нолики на поле 15х15; 2 игрока; для победы нужно собрать 5 камней в ряд.
- С текущими модами игроков может быть 3, а поле - размера 30х30.
- Сдача, выход или разрыв соединения после подтверждения готовности приводят к поражению.
- Единственный оставшийся в игре игрок получает техническую победу.
- Закончившееся свободное место на доске ведет к проставлению всем игрокам ничьей.

### Технические детали

- Используемые протоколы:
  - WebSocket: для действий, требующих уведомления других пользователей
  - HTTP: для всех остальных действий
- Процесс авторизации унифицирован для HTTP и WebSocket с помощью [FastAPI Dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/), ради чего пришлось отказаться от расширения fastapi-users.
- Access token един для HTTP и WebSocket; в первом случае он передается в заголовке (Bearer), во втором - как параметр запроса.
- Для тестов при подъеме docker-compose создается отдельная БД.

### Иллюстрации

Основной функционал. Как бэкенд-разработчик, я делал упор на бэкенд-составляющую, так что внешний вид... может не впечатлять :)  
Мобильные устройства на текущий момент не поддерживаются.  

Главное меню:
![mainScreenNotLogged](/pics/main_mot_logged.png)

После регистрации, верификации почты и аутентификации:
![mainScreenLogged](/pics/main_logged.png)

Меню создания новой игры. Правила определяются на основе выбранных модов. Крестиком отмечены недоступные на данный момент моды (находящиеся в планах/в разработке):
![createChooseMod](/pics/create_mod.png)

Для тестовой игры примем правила по умолчанию:
![createGameNoMods](/pics/create_no_mods.png)

К созданной игре можно присоединиться по ее ID либо, если чекбокс Private с предыдущего скриншота не был установлен, - через список публичных игр:
![joinPublicGame](/pics/join_public.png)

Создатель игры, тем временем, был перенаправлен на экран игры и подтвердил готовность:
![gamePlayer1Ready](/pics/game_1_ready.png)

Игра не начинается, пока оба игрока не подтвердят готовность. До подтверждения можно покинуть игру и не получить техническое поражение.
![gamePlayer2NotReady](/pics/game_2_not_ready.png)

Все подтвердили готовность, определяется очередность ходов - доска разблокирована для текущего игрока:
![gamePlayer1Started](/pics/game_1_started.png)

Белые сделали ход - доска разблокирована для следующего игрока:
![gamePlayer2Started](/pics/game_2_started.png)

В напряженной борьбе белые собирают 5 камней в ряд и побеждают. Результаты сохряняются. Игроки возвращаются в главное меню.
![gamePlayer1Won](/pics/game_1_won.png)
