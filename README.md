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
Connect to `[IP_ADDRESS]:8000` with a browser to start programming