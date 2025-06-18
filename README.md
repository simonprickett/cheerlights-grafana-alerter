# TODO TITLE

## Introduction

TODO

## Hardware Required

TODO

### Grafana Alert Setup

TODO

jsonata expression:

```
$map(feeds^(>entry_id), function($v) {
  return {
    "howLongAgo": $millis() - $toMillis($v.created_at),
    "color": $v.field1,
    "entryId": $formatNumber($v.entry_id, '#')
  }
})
```

with filter:

```
howLongAgo <= 90000
```

## Unicorn Setup

TODO

### Install Dependencies

The code uses Peter Hinch's [MicroPython MQTT client](https://github.com/peterhinch/micropython-mqtt/).

```bash
mpremote mip install github:peterhinch/micropython-mqtt
```

### Configure Secrets

TODO

### Copying the Code to the Unicorn

TODO

### Running the Code

TODO

## Test it Out!

TODO

