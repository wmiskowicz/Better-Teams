cmake_minimum_required(VERSION 3.16)
project(ChatApp)

set(CMAKE_CXX_STANDARD 17)

find_package(Qt6 REQUIRED COMPONENTS Widgets Network)

qt_standard_project_setup()

add_executable(chat_client
    main.cpp
    LoginWindow.cpp
    SessionSelectWindow.cpp
    ChatWindow.cpp
)

target_link_libraries(chat_client
    Qt6::Widgets
    Qt6::Network
)
