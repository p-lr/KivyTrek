rm bin/*.apk

echo Compilation
buildozer -v android debug

echo Installation sur le device
buildozer android deploy run logcat
