from predictor import predict_camera_health


result = predict_camera_health(
    uptime=75,
response_time=900,
packet_loss=15,
cpu_usage=95
)


print()
print("====================================")
print("CCTV AI CAMERA HEALTH PREDICTION")
print("====================================")
print(f"Health          : {result['health']}")
print(f"Confidence      : {result['confidence']}%")
print(f"Uptime          : {result['uptime']}%")
print(f"Response Time   : {result['response_time']} ms")
print(f"Packet Loss     : {result['packet_loss']}%")
print(f"CPU Usage       : {result['cpu_usage']}%")
print("====================================")