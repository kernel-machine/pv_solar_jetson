# Template for Nvidia Jetson Orin with Balena

This template is based on: https://github.com/balena-io-examples/jetson-examples/tree/master

### How to customize
- Add your packages in `postscript.sh`

### How to push
```bash
balena push [fleet_name]
```
Or when local mode is enabled
```bash
balena push [ip_address]
```

### HOW TO DEVELOP
- Connect to `[IP_ADDRESS]:8000` with a browser to start programming and enter the password inserted in the `docker-compose.yaml` file
- Put all your data in `\app`, otherwise they will be deleted on reboot

### Warning
The Jetson require special versions of torch and torchvision, so use the one installed at system level.
Using a torch version installed by pip will not work

### Running RTSP Server
To run the RTSP you can run this container
```bash
podman run --rm -it -e MTX_RTSPTRANSPORTS=tcp -e MTX_WEBRTCADDITIONALHOSTS=192.168.0.131 -p 8554:8554 -p 1935:1935 -p 8888:8888 -p 8889:8889 -p 8890:8890/udp -p 8189:8189/udp docker.io/bluenviron/mediamtx:1-ffmpeg
```