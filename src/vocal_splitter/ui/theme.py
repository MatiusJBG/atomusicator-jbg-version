"""Tokens y estilo Qt del prototipo Separador Vocal."""

APPLICATION_STYLE = """
QWidget { color: #E5EDF3; font-family: 'Segoe UI'; font-size: 12px; }
QMainWindow, QWidget#central, QDialog { background: #0B0F14; }
QLabel { background: transparent; }
QLabel#pageTitle { font-size: 25px; font-weight: 700; }
QLabel#pageSubtitle, QLabel#muted, QLabel#workbenchHint, QLabel#result { color: #8A9AA8; }
QLabel#breadcrumb { color: #8A9AA8; font-size: 11px; }
QLabel#workbenchTitle { font-size: 16px; font-weight: 650; }
QLabel#sectionTitle { font-size: 15px; font-weight: 650; }
QLabel#stemCount, QLabel#metadata { background: #18222C; color: #8A9AA8; padding: 4px 8px; border: 1px solid #29343F; border-radius: 3px; font-size: 10px; }
QLabel#trackOrdinal, QLabel#controlEyebrow { color: #81909F; font-size: 10px; }
QLabel#trackTitle { font-size: 12px; font-weight: 650; }
QLabel#gainValue, QLabel#transportTime { font-family: Consolas; color: #9BABB9; font-size: 10px; }
QLabel#transportTime { color: #E5EDF3; font-size: 14px; }
QLabel#accent { color: #2DD4BF; font-size: 11px; }
QPushButton, QToolButton { background: #18232D; border: 1px solid #2D3B48; border-radius: 5px; padding: 8px 12px; color: #DCE6ED; }
QPushButton:hover, QToolButton:hover { background: #233340; border-color: #536575; }
QPushButton:focus, QToolButton:focus, QSlider:focus, QDial:focus, QSpinBox:focus, QComboBox:focus, QCheckBox:focus, QLineEdit:focus { border: 1px solid #2DD4BF; }
QPushButton:disabled, QToolButton:disabled { color: #60717F; background: #131B23; border-color: #23303B; }
QPushButton#primaryButton { background: #2DD4BF; border-color: #2DD4BF; color: #062B2A; font-weight: 650; }
QPushButton#primaryButton:hover { background: #58E5CF; }
QPushButton#primaryButton:disabled { background: #183B39; border-color: #234943; color: #6B9A93; }
QFrame#sidebar { background: #0F161E; border-right: 1px solid #29343F; }
QToolButton#navButton { border: 1px solid transparent; background: transparent; color: #8A9AA8; font-size: 10px; padding: 10px 2px; }
QToolButton#navButton:checked { color: #2DD4BF; background: #12332F; border-color: #28524B; }
QToolButton#navButton:hover { background: #18252D; }
QLabel#brand { color: #2DD4BF; background: #123C38; font-size: 25px; border-radius: 12px; padding: 8px; }
QFrame#dropArea { background: #10171F; border: 1px dashed #344652; border-radius: 8px; }
QFrame#dropArea[dragActive='true'] { background: #13312F; border: 2px solid #2DD4BF; }
QLabel#dropPrompt { color: #E5EDF3; font-size: 23px; font-weight: 650; }
QLabel#formatList { color: #8A9AA8; }
QFrame#separationPanel, QFrame#transportPanel, QFrame#pitchPanel, QFrame#masterPanel, QFrame#exportCard { background: #131B23; border: 1px solid #29343F; border-radius: 6px; }
QLabel#separationHeading { font-size: 25px; font-weight: 650; }
QLabel#separationPhase { color: #2DD4BF; font-size: 17px; }
QLabel#separationDetail, QLabel#separationSteps { color: #8A9AA8; }
QFrame#trackRow { background: #141D26; border: 0; border-bottom: 1px solid #29343F; }
QPushButton#trackToggle { padding: 2px; border-radius: 3px; min-width: 21px; min-height: 21px; color: #8A9AA8; }
QPushButton#trackToggle:checked { background: #5A4317; border-color: #F5B52E; color: #F5B52E; }
QPushButton#playButton { border-radius: 17px; background: #2DD4BF; border: 0; color: #06302D; padding: 0; font-size: 15px; }
QPushButton#transportButton { padding: 2px; background: transparent; border: 0; font-size: 16px; }
QSlider { border: 1px solid transparent; }
QSlider::groove:horizontal { height: 3px; background: #293642; border: 0; }
QSlider::sub-page:horizontal { background: #2DD4BF; }
QSlider::handle:horizontal { width: 8px; background: #D7E1E9; margin: -4px 0; border-radius: 2px; }
QSpinBox, QComboBox, QLineEdit { color: #DCE6ED; background: #101820; border: 1px solid #293E4C; border-radius: 4px; padding: 6px; }
QComboBox QAbstractItemView { background: #18232D; color: #E5EDF3; selection-background-color: #23564E; }
QCheckBox { color: #9BAAB8; spacing: 6px; }
QCheckBox::indicator { width: 13px; height: 13px; border: 1px solid #49606E; border-radius: 3px; background: #101820; }
QCheckBox::indicator:checked { background: #2DD4BF; border-color: #2DD4BF; image: none; }
QProgressBar { background: #29343F; border: 0; border-radius: 2px; min-height: 4px; max-height: 6px; color: transparent; }
QProgressBar::chunk { background: #2DD4BF; border-radius: 2px; }
QScrollArea#trackScroll, QWidget#trackContent { background: #10171F; border: 1px solid #29343F; border-radius: 4px; }
QScrollBar:vertical { width: 7px; background: #10171F; margin: 0; }
QScrollBar::handle:vertical { background: #394A59; min-height: 24px; border-radius: 3px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
QMenuBar, QMenu, QStatusBar { background: #0F161E; color: #8A9AA8; font-size: 10px; }
QMenuBar::item:selected, QMenu::item:selected { background: #233A3C; }
QPushButton#formatCard { text-align: left; min-height: 44px; padding: 10px; }
QPushButton#formatCard:checked { background: #123B35; border-color: #2DD4BF; color: #2DD4BF; }
QListWidget { background: #10171F; border: 1px solid #29343F; padding: 8px; }
QListWidget::item { padding: 12px; border-bottom: 1px solid #29343F; }
QListWidget::item:selected { background: #123B35; color: #2DD4BF; }
"""
