<h1 align="center">Рекомендации ТВ-программ на основе пользовательских предпочтений</h1>

<p align="center">
  <img src="https://github.com/katecapri/images-for-readme/blob/main/fastapi.png"/>
  <img src="https://github.com/katecapri/images-for-readme/blob/main/mongodb.png"/>
  <img src="https://github.com/katecapri/images-for-readme/blob/main/opensearch.png"/>
</p>


##  Описание ##

REST API сервис по предложению контента пользователям на основе истории просмотров ТВ-программ. Вместе с запуском проекта заполняется база каналов, программ и пользователей из файлов programs.xml и users.xml из папки src/database. 
![](https://github.com/katecapri/images-for-readme/blob/main/ТВ-0-нач%20заполнение.png) 


##  Используемые технологии ##

- Python
- FastApi
- MongoDB
- OpenSearch
- Docker
- Celery
- BeautifulSoup4


##  Инструкция по запуску ##

1. Перед запуском проекта требуется изменить переменную системы vm.max_map_count для запуска OpenSearch:

> sudo sysctl -w vm.max_map_count=262144 

2. Запуск всего проекта производится командой:

> make run

##  Результат ##

1. Методом POST http://127.0.0.1:8000/program_watching/ в базу сохраняется информация о просмотре пользователем ТВ-программы
   
![](https://github.com/katecapri/images-for-readme/blob/main/ТВ-1-сохранение%20просмотра.png)

2. На основе информации о пользовательских просмотрах 3 периодические Celery-задачи рассчитывают популярность ТВ-программ (сохраняется в OpenSearch), пользовательские предпочтения, и на основании этих двух расчетов формируется рекомендованный для каждого пользователя контент. Для каждого пользователя после прихода информации о новом просмотре, задачи на расчет пользовательских предпочтений и рекомендаций запускаются автоматически, не дожидаясь времени следующего срабатывания. Для просмотра коллекции OpenSearch можно авторизоваться в браузере по адресу http://0.0.0.0:5601/app/login с доступами: логин -  admin , пароль - My_custom_pass123 .
   
![](https://github.com/katecapri/images-for-readme/blob/main/ТВ-2-попул%20в%20опенсеарч.png)
![](https://github.com/katecapri/images-for-readme/blob/main/ТВ-2%20предпочтения.png)
![](https://github.com/katecapri/images-for-readme/blob/main/ТВ-2%20рекомендации.png)


3. Предпочтения и рекомендации для пользователя можно так же получить по url http://127.0.0.1:8000/user_preferences/{user_id} и http://127.0.0.1:8000/user_recommendations/{user_id}
   
![](https://github.com/katecapri/images-for-readme/blob/main/ТВ-3-получ%20предпочт.png)
![](https://github.com/katecapri/images-for-readme/blob/main/ТВ-3-получ%20реком.png)
