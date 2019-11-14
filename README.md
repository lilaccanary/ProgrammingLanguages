# ProgrammingLanguages
Веб приложение реализующее json API методы для доступа к файловой системе.
Для работы сервиса требуется библиотека Flask и Python 3.

Методы:
1. Построение иерархии директорий в представлении json.
0.0.0.0:8080/getJsonOfDir/alina
2. Можно создавать дирекотории.
0.0.0.0:8080/createDir/alina/foldername
3. Можно удалять пустые дирекотории.
0.0.0.0:8080/delete/foldername
4. Можно скачивать файлы с сервиса.
0.0.0.0:8080/download/alina/text.txt
5. Можно загружать файлы на сервер.
0.0.0.0:8080/upload/alina
