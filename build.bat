rd /s /q build
mkdir build
cd build


cmake .. -DCMAKE_PREFIX_PATH="C:\Qt\6.11.0\mingw_64" -G "MinGW Makefiles"
cmake --build  .

cd ../
mkdir dist
move ./build/client/chat_client.exe ./dist/chat_client.exe
move ./build/server/chat_server.exe ./dist/chat_server.exe

@REM Can be removed when C:\Qt\6.11.0\mingw_64\bin\ added to path(?)
C:\Qt\6.11.0\mingw_64\bin\windeployqt.exe .\dist\chat_client.exe
C:\Qt\6.11.0\mingw_64\bin\windeployqt.exe .\dist\chat_server.exe