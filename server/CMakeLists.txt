cmake_minimum_required(VERSION 3.16)
project(ChatApp)

set(CMAKE_CXX_STANDARD 17)
find_package(Qt6 REQUIRED COMPONENTS Network)
add_executable(chat_server server.cpp)

target_link_libraries(chat_server 
    PRIVATE 
    Qt6::Network
    pthread
)