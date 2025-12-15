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
This container is pre-configurated to use VSCode as IDE

At the end of your balena push you have to find a code to authenticate with github in the container vscode installation. You have to find a text like this:

```
[Logs]    [2025-12-15T12:03:02.053Z] [app] [2025-12-15 12:03:02] info Using GitHub for authentication, run `code tunnel user login --provider <provider>` option to change this.
[Logs]    [2025-12-15T12:03:02.271Z] [app] To grant access to the server, please log into https://github.com/login/device and use code XXXX-XXXX
```

Then, go to the https://github.com/login/device and enter the provided code.

### Warning
The Jetson require special versions of torch and torchvision, so use the one installed at system level.
Using a torch version installed by pip will not work

### Running RTSP Server
To run the RTSP you can run this container
```bash
podman run --rm -it -e MTX_RTSPTRANSPORTS=tcp -e MTX_WEBRTCADDITIONALHOSTS=192.168.0.131 -p 8554:8554 -p 1935:1935 -p 8888:8888 -p 8889:8889 -p 8890:8890/udp -p 8189:8189/udp docker.io/bluenviron/mediamtx:1-ffmpeg
```