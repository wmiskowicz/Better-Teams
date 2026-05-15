
GLOBAL_STYLE = """
QWidget {
    background-color: #F8F9FA;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

#VideoDisplay {
    background-color: #D0E0FF;
    border: 2px solid #A0A0A0;
    border-radius: 15px;
}

#ChatContainer {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 10px;
}

/* PushButton Styles including Hover and Pressed states */
QPushButton {
    background-color: #E0E0E0;
    border: 1px solid #999999;
    border-radius: 6px;
    padding: 6px 12px;
    color: #333333;
}

QPushButton:hover {
    background-color: #D0D0D0;
    border: 1px solid #666666;
}

QPushButton:pressed {
    background-color: #B0B0B0;
    padding-top: 8px; /* Simple trick to simulate a physical 'press' */
}

/* Input Styles */
QLineEdit {
    background-color: #FFFFFF;
    border: 1px solid #CCCCCC;
    border-radius: 4px;
    padding: 5px;
}

QLineEdit:focus {
    border: 2px solid #4070C0;
}

/* Scrollbar and Text Area */
QTextEdit {
    background-color: white;
    border: none;
}
"""