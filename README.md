# chatGPTRaspi4


Instellen Bluetooth

start :  bluetoothctl
vervolgens scan on,  trust, pair en connect de bluetooth device

Dan exit

zoeken naar devices :

pactl list sinks short

de juiste selecteren :  pactl set-default-sink <sink-name>

en vervolgens starten :  pulseaudio --start

Om terug op de defeult te zetten :  pactl set-default-sink alsa_output.platform-bcm2835_audio.stereo-fallback.2


Om te kijken tot welke wifi de RPI is geconnecteerd :  iwgetid
