# be-scada

# MQTT Reponse

# HTTPS Response

# Websocket Response

## /ws/unit/:unitId/status

```json
{
"power": "float",
"current": "float",
"voltage": "float",
"toggle": "1" | "0",
"frequency": "float",
"power_factor": "float",
"total_energy": "float",
"gps_log": "float",
"gps_lat": "float",
}
```
or
```json
{
  "alive": "1" | "0",
  "time": "YYYY-MM-DD HH:MM:SS"// YYYY-MM-DD HH:MM:SS
}
```