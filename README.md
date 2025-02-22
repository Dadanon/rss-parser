# RSS Parser

## Публичные методы:

### 1. Получить название и описание канала
```
get_channel_title_and_description(self) -> Optional[Dict[Optional[str], Optional[str]]]
```
Получить название и описание канала в формате
```
{'title': 'www.rbc.ru', 'description': None}
```
### 2. Получить следующую статью
```
get_next() -> Optional[Item]
```
```
class Item:
    title: Optional[str]
    link: Optional[str]
    description: Optional[str]
```
Получить следующую статью в формате
```
{'title': 'Переговоры Путина и Орбана завершились', 'link': 'https://www.rbc.ru/rbcfreenews/6687f60b9a79476cb5021603', 'description': 'Президент России Владимир Путин и премьер-министр Венгрии Виктор Орбан завершили переговоры в Москве, сообщило"РИА Новости&raquo; со ссылкой на пресс-секретаря Путина Дмитрия Пескова.'}
```
### 3. Получить предыдущую статью
```
get_prev() -> Optional[Item]
```
Получить предыдущую статью в формате
```
{'title': 'Ликсутов рассказал о борьбе с жарой в московском метро', 'link': 'https://www.rbc.ru/rbcfreenews/6687f1619a79470b82d91827', 'description': 'В жаркую погоду сотрудники столичного метро работают в усиленном режиме - в том числе замеряют температуру на станциях и вестибюлях по два раза в день, а также внимательнее регулируют работу вентиляционных шахт.'}
```
### 4. Получить первую статью
```
get_first() -> Optional[Item]
```
Получить первую статью в формате
```
{'title': 'Пожар в ростовском поселке Золотой Колос потушили', 'link': 'https://www.rbc.ru/rbcfreenews/6687e2019a794768af544595', 'description': ' Сотрудники МЧС потушили пожар в поселке Золотой Колос в Аксайском районе Ростовской области, сообщила пресс-служба ведомства.'}
```
### 5. Получить последнюю статью
```
get_last() -> Optional[Item]
```
Получить последнюю статью в формате
```
{'title': 'Идеолог Brexit с восьмой попытки избрался в британский парламент', 'link': 'https://www.rbc.ru/rbcfreenews/6687ee089a7947ca7d1f81dc', 'description': 'Лидер правой популистской партии Reform UK Найджел Фарадж получил место в палате общин британского парламента по итогам прошедших выборов, передает Reuters.'}
```
### 6. Получить длину списка статей
```
items_length() -> int
```
Получить длину списка статей в формате int, например: 20
### 7. Получить полное содержимое статьи
```
get_item_content() -> Optional[str]
```
На данный момент возвращает содержимое тега body как строку по ссылке на статью
в текущей позиции навигации. Использует Selenium для эмуляции пользователя.
Соответственно, ничего не возвращает, если у текущей статьи нет ссылки
