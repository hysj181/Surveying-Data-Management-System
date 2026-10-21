[app]

title = SurveyingDataManager

project_dir = .

input_file = src\main.py

exec_directory = dist

project_file =

icon = assets/app.ico

[python]

packages = Nuitka==4.1.1

[qt]

modules = Core,Gui,Widgets

plugins = platforms,styles,imageformats,iconengines,platformthemes

qml_files =

excluded_qml_plugins =

[nuitka]

mode = standalone

extra_args = --quiet --noinclude-qt-translations --windows-console-mode=disable --assume-yes-for-downloads --experimental=force-dependencies-pefile
