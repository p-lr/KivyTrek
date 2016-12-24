********** DEBOGAGE ********** 
-lancer "adb logcat" depuis n'importe quel repertoire
-le debogage usb doit être activé sur le telephone (settings > devs opt > debug usb)
-lancer l'app depuis le telephone

En cas de pb, repérer une éventuelle erreur python. Dans mon cas c'était :
	ImportError: No module named pygments.lexer I/python  (21247): Python for android ended.
Il a fallu ajouter pygments dans les requirements de buildozer.spec

nb : pour utiliser adb, il fault l'installer "sudo apt-get install android-tools-adb"

********** Utiliser un fork de plyer **********
Plutôt que de définir "requirements.source.plyer = path/to/plyer" dans buildozer.spec,
définir la variable d'environnement P4A_plyer_DIR
Par ex : "export P4A_plyer_DIR=/home/pla/Dev/plyer"

********** Installer un module du garden *******

-installer si ce n'est pas déjà fait kivy garden : "sudo pip install kivy-garden"
-puis se placer à la racine de l'application, par ex "cd /home/pla/KivyTrek"
-et installer le module, par ex : "garden install recylceview --app"

********** COMPILER ********** 
-lancer "buildozer -v android debug" dans le répertoire de l'app

********** DEPLOYER + LANCER ********** 
-lancer "buildozer android deploy run logcat"
-si buildozer dit que l'accès au device n'est pas autorisé, tenter de faire "adb kill-server" puis "adb start-server"
 L'ordinateur doit préalablement avoir fait été ajouté à la liste des machines autorisées par le téléphone, ce qui se
 fait lorsqu'on connecte pour la première fois le tel au pc, avec le débogage usb activé. 


